import random
import re
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from src.scrapers.base import Article, BaseScraper

GITHUB_TRENDING_URL = "https://github.com/trending"

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

_COUNT_RE = re.compile(r"(\d[\d,.]*)\s*([kK])?")


def parse_count(text: str) -> int:
    """Premier nombre d'un texte GitHub : « 3,274 stars today » → 3274, « 1.2k » → 1200."""
    match = _COUNT_RE.search(text or "")
    if not match:
        return 0
    number, thousands = match.groups()
    if thousands:
        return round(float(number.replace(",", "")) * 1000)
    return int(number.replace(",", "").replace(".", ""))


def format_count(n: int) -> str:
    """Séparateur de milliers à la française, insécable : 42358 → « 42 358 »."""
    return f"{n:,}".replace(",", "\u00a0")


LANGUAGE_DOMAIN_MAP: dict[str, list[str]] = {
    "python": ["ia", "dev"],
    "jupyter notebook": ["ia", "formation"],
    "rust": ["dev", "ingenierie"],
    "go": ["dev", "ingenierie"],
    "typescript": ["dev"],
    "javascript": ["dev"],
    "c": ["securite", "ingenierie"],
    "c++": ["securite", "ingenierie"],
    "shell": ["dev", "ingenierie"],
}


class GitHubTrendingScraper(BaseScraper):
    """Scrape github.com/trending (pas d'API officielle — parsing HTML)."""

    name = "github_trending"
    domains = ["dev", "ia", "ingenierie"]
    profiles = ["ETUDIANT", "INGENIEUR"]

    def __init__(self, language: str = "", period: str = "daily"):
        self.language = language
        self.period = period  # daily | weekly | monthly

    async def fetch(self) -> list[Article]:
        url = GITHUB_TRENDING_URL
        params: dict[str, str] = {"since": self.period}
        if self.language:
            params["l"] = self.language

        headers = {"User-Agent": random.choice(USER_AGENTS)}

        logger.debug(
            f"[{self.name}] Scraping {url} (lang={self.language or 'all'}, period={self.period})"
        )

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()

        articles = self._parse(r.text)
        logger.info(f"[{self.name}] {len(articles)} dépôts récupérés")
        return articles

    def _parse(self, html: str) -> list[Article]:
        soup = BeautifulSoup(html, "lxml")
        articles: list[Article] = []
        now = datetime.now(tz=UTC)

        for repo_box in soup.select("article.Box-row"):
            try:
                name_tag = repo_box.select_one("h2 a")
                if not name_tag:
                    continue

                full_name = (
                    name_tag.get_text(strip=True).replace("\n", "").replace(" ", "")
                )
                url = f"https://github.com{name_tag['href']}"

                desc_tag = repo_box.select_one("p")
                description = desc_tag.get_text(strip=True) if desc_tag else ""

                lang_tag = repo_box.select_one("[itemprop='programmingLanguage']")
                language = lang_tag.get_text(strip=True) if lang_tag else ""

                stars_tag = repo_box.select_one("a[href*='stargazers']")
                stars = parse_count(stars_tag.get_text(strip=True)) if stars_tag else 0

                # Texte anglais de GitHub (« 3,274 stars today ») : on n'en
                # garde que le nombre
                today_stars_tag = repo_box.select_one(
                    "span.d-inline-block.float-sm-right"
                )
                today_stars = (
                    parse_count(today_stars_tag.get_text(strip=True))
                    if today_stars_tag
                    else 0
                )

                domains = LANGUAGE_DOMAIN_MAP.get(language.lower(), ["dev"])
                if any(
                    kw in description.lower()
                    for kw in ["ai", "llm", "machine learning", "neural"]
                ):
                    if "ia" not in domains:
                        domains.append("ia")

                summary = f"⭐ {format_count(stars)} étoiles"
                if today_stars:
                    summary += f" · +{format_count(today_stars)} aujourd'hui"
                if language:
                    summary += f" · {language}"
                if description:
                    summary += f"\n{description}"

                articles.append(
                    Article(
                        title=full_name,
                        url=url,
                        summary=summary,
                        published_at=now,
                        source=self.name,
                        domains=domains,
                        profiles=self.profiles,
                        score=min(stars / 10000, 1.0),
                        extra={
                            "stars": stars,
                            "stars_today": today_stars,
                            "language": language,
                        },
                    )
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Erreur parsing repo : {e}")

        return articles

    async def health_check(self) -> bool:
        try:
            headers = {"User-Agent": USER_AGENTS[0]}
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.head(GITHUB_TRENDING_URL, headers=headers)
                return r.status_code < 500
        except Exception:
            return False
