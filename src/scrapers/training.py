"""Scrapers formation/certifications : freeCodeCamp, Roadmap.sh, Stack Overflow Survey."""

from datetime import datetime

import httpx
from loguru import logger

from src.scrapers.base import Article, BaseScraper
from src.scrapers.rss import RssScraper, RssSource

TRAINING_RSS_SOURCES = [
    RssSource(
        name="freecodecamp",
        url="https://www.freecodecamp.org/news/rss/",
        domains=["formation", "dev"],
        profiles=["ETUDIANT"],
        base_score=0.7,
    ),
]

ROADMAP_RELEASES_URL = (
    "https://api.github.com/repos/kamranahmedse/developer-roadmap/releases"
)


class RoadmapScraper(BaseScraper):
    """Récupère les nouvelles releases de roadmap.sh via l'API GitHub Releases."""

    name = "roadmap_sh"
    domains = ["formation", "dev"]
    profiles = ["ETUDIANT", "INGENIEUR"]

    async def fetch(self) -> list[Article]:
        logger.debug(f"[{self.name}] Récupération des releases GitHub")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(ROADMAP_RELEASES_URL, params={"per_page": 10})
            r.raise_for_status()
            releases = r.json()

        articles: list[Article] = []
        for release in releases:
            if release.get("draft") or release.get("prerelease"):
                continue
            try:
                published_at = datetime.fromisoformat(
                    release["published_at"].replace("Z", "+00:00")
                )
                articles.append(
                    Article(
                        title=f"Roadmap.sh — {release['name'] or release['tag_name']}",
                        url=release["html_url"],
                        summary=release.get("body", "")[:400],
                        published_at=published_at,
                        source=self.name,
                        domains=self.domains,
                        profiles=self.profiles,
                        score=0.65,
                    )
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Erreur release : {e}")

        logger.info(f"[{self.name}] {len(articles)} releases récupérées")
        return articles

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.head(ROADMAP_RELEASES_URL)
                return r.status_code < 500
        except Exception:
            return False


def build_training_scrapers() -> list[BaseScraper]:
    scrapers: list[BaseScraper] = [RssScraper(src) for src in TRAINING_RSS_SOURCES]
    scrapers.append(RoadmapScraper())
    return scrapers
