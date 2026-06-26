from datetime import datetime, timezone

import httpx
from loguru import logger

from src.scrapers.base import Article, BaseScraper

HN_API = "https://hacker-news.firebaseio.com/v0"
HN_ITEM_URL = "https://news.ycombinator.com/item?id={id}"

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "ia": ["ai", "llm", "machine learning", "gpt", "claude", "openai", "neural", "deep learning", "ml"],
    "securite": ["security", "vulnerability", "cve", "exploit", "malware", "breach", "hack"],
    "dev": ["javascript", "python", "rust", "golang", "typescript", "framework", "library", "api"],
    "ingenierie": ["distributed", "kubernetes", "postgres", "architecture", "scalability", "microservices"],
    "reglementation": ["gdpr", "regulation", "compliance", "law", "policy", "eu ai act"],
    "formation": ["tutorial", "course", "learn", "beginner", "guide", "how to"],
}


def _tag_domains(text: str) -> list[str]:
    text_lower = text.lower()
    return [domain for domain, keywords in DOMAIN_KEYWORDS.items() if any(kw in text_lower for kw in keywords)]


class HackerNewsScraper(BaseScraper):
    """Scrape Hacker News via l'API Firebase officielle (pas de scraping HTML)."""

    name = "hacker_news"
    domains = ["dev", "ia", "securite", "ingenierie"]
    profiles = ["ETUDIANT", "INGENIEUR"]

    def __init__(self, min_score: int = 50, max_articles: int = 30):
        self.min_score = min_score
        self.max_articles = max_articles

    async def fetch(self) -> list[Article]:
        logger.debug(f"[{self.name}] Récupération des top stories")
        async with httpx.AsyncClient(timeout=10) as client:
            # Récupérer les IDs des top stories
            r = await client.get(f"{HN_API}/topstories.json")
            r.raise_for_status()
            story_ids: list[int] = r.json()[: self.max_articles * 2]

            articles: list[Article] = []
            for story_id in story_ids:
                if len(articles) >= self.max_articles:
                    break
                try:
                    item = await self._fetch_item(client, story_id)
                    if item and item.get("score", 0) >= self.min_score:
                        article = self._to_article(item)
                        if article:
                            articles.append(article)
                except Exception as e:
                    logger.warning(f"[{self.name}] Erreur item {story_id}: {e}")

        logger.info(f"[{self.name}] {len(articles)} articles récupérés")
        return articles

    async def _fetch_item(self, client: httpx.AsyncClient, item_id: int) -> dict | None:
        r = await client.get(f"{HN_API}/item/{item_id}.json")
        r.raise_for_status()
        return r.json()

    def _to_article(self, item: dict) -> Article | None:
        if item.get("type") != "story" or not item.get("title"):
            return None

        title = item["title"]
        url = item.get("url") or HN_ITEM_URL.format(id=item["id"])
        summary = f"Score HN : {item.get('score', 0)} points · {item.get('descendants', 0)} commentaires"
        published_at = datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc)
        tagged_domains = _tag_domains(title)

        return Article(
            title=title,
            url=url,
            summary=summary,
            published_at=published_at,
            source=self.name,
            domains=tagged_domains or ["dev"],
            profiles=self.profiles,
            score=min(item.get("score", 0) / 1000, 1.0),
            extra={"hn_score": item.get("score", 0), "hn_id": item["id"]},
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{HN_API}/topstories.json")
                return r.status_code == 200
        except Exception:
            return False
