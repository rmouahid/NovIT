"""Scrapers pour les blogs IA (flux RSS de config/sources.yaml) et arXiv."""

import asyncio
from datetime import UTC, datetime

import feedparser
from loguru import logger

from novit.scrapers.base import Article, BaseScraper
from novit.scrapers.http import http_client
from novit.scrapers.rss import RssScraper, load_rss_sources

ARXIV_API_URL = "https://export.arxiv.org/api/query"


class ArxivScraper(BaseScraper):
    """Récupère les derniers papiers arXiv cs.AI et cs.LG via l'API officielle."""

    name = "arxiv"
    domains = ["ia"]
    profiles = ["INGENIEUR"]

    def __init__(self, categories: list[str] | None = None, max_results: int = 20):
        self.categories = categories or ["cs.AI", "cs.LG"]
        self.max_results = max_results

    async def fetch(self) -> list[Article]:
        query = " OR ".join(f"cat:{cat}" for cat in self.categories)
        params = {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": self.max_results,
        }
        logger.debug(f"[{self.name}] Requête arXiv : {query}")
        async with http_client(timeout=20, follow_redirects=True) as client:
            r = await client.get(ARXIV_API_URL, params=params)
            r.raise_for_status()

        # Analyse hors de la boucle d'événements : un gros flux arXiv la bloquait (#90)
        feed = await asyncio.to_thread(feedparser.parse, r.text)
        articles: list[Article] = []

        for entry in feed.entries:
            try:
                published_at = (
                    datetime(*entry.published_parsed[:6], tzinfo=UTC)
                    if hasattr(entry, "published_parsed") and entry.published_parsed
                    else datetime.now(tz=UTC)
                )
                authors = ", ".join(
                    a.get("name", "") for a in entry.get("authors", [])[:3]
                )
                summary = f"**Auteurs :** {authors}\n\n{entry.get('summary', '')[:400]}"
                articles.append(
                    Article(
                        title=entry.get("title", "").replace("\n", " ").strip(),
                        url=entry.get("link", ""),
                        summary=summary,
                        published_at=published_at,
                        source=self.name,
                        domains=["ia"],
                        profiles=["INGENIEUR"],
                        score=0.7,
                        extra={"categories": self.categories},
                    )
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Erreur entry : {e}")

        logger.info(f"[{self.name}] {len(articles)} papiers récupérés")
        return articles

    async def health_check(self) -> bool:
        try:
            async with http_client(timeout=5, follow_redirects=True) as client:
                r = await client.head(ARXIV_API_URL)
                return r.status_code < 400
        except Exception:
            return False


def build_ai_scrapers() -> list[BaseScraper]:
    scrapers: list[BaseScraper] = [
        RssScraper(src) for src in load_rss_sources(category="ia")
    ]
    scrapers.append(ArxivScraper())
    return scrapers
