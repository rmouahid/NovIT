from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
from loguru import logger

from src.scrapers.base import Article, BaseScraper


@dataclass
class RssSource:
    name: str
    url: str
    domains: list[str]
    profiles: list[str]
    base_score: float = 0.5


RSS_SOURCES: list[RssSource] = [
    RssSource(
        name="dev_to",
        url="https://dev.to/feed",
        domains=["dev", "formation"],
        profiles=["ETUDIANT", "INGENIEUR"],
        base_score=0.5,
    ),
    RssSource(
        name="techcrunch",
        url="https://techcrunch.com/feed/",
        domains=["dev", "ia", "ingenierie"],
        profiles=["ETUDIANT", "INGENIEUR"],
        base_score=0.6,
    ),
    RssSource(
        name="the_verge",
        url="https://www.theverge.com/rss/index.xml",
        domains=["dev", "ia"],
        profiles=["ETUDIANT"],
        base_score=0.45,
    ),
    RssSource(
        name="mit_tech_review",
        url="https://www.technologyreview.com/feed/",
        domains=["ia", "reglementation"],
        profiles=["ETUDIANT", "INGENIEUR"],
        base_score=0.7,
    ),
]


def _parse_date(entry: dict) -> datetime:
    """Parse la date depuis un entry feedparser, retourne now() si impossible."""
    for attr in ("published", "updated"):
        value = getattr(entry, attr, None)
        if value:
            try:
                return parsedate_to_datetime(value).astimezone(timezone.utc)
            except Exception:
                pass
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(tz=timezone.utc)


class RssScraper(BaseScraper):
    """Scraper RSS/Atom générique et réutilisable.

    Instancié avec une RssSource, fonctionne pour n'importe quel flux
    RSS 2.0 ou Atom. La déduplication par URL est gérée par le ScraperManager.
    """

    def __init__(self, source: RssSource):
        self._source = source

    @property
    def name(self) -> str:
        return self._source.name

    @property
    def domains(self) -> list[str]:
        return self._source.domains

    @property
    def profiles(self) -> list[str]:
        return self._source.profiles

    async def fetch(self) -> list[Article]:
        logger.debug(f"[{self.name}] Lecture du flux RSS : {self._source.url}")
        feed = feedparser.parse(self._source.url)

        if feed.bozo and not feed.entries:
            logger.warning(f"[{self.name}] Flux RSS invalide : {feed.bozo_exception}")
            return []

        articles: list[Article] = []
        seen_urls: set[str] = set()

        for entry in feed.entries:
            try:
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", ""))
                # Nettoyer le HTML basique des résumés RSS
                summary = summary[:600].strip() if summary else ""

                articles.append(Article(
                    title=title,
                    url=url,
                    summary=summary,
                    published_at=_parse_date(entry),
                    source=self.name,
                    domains=self._source.domains,
                    profiles=self._source.profiles,
                    score=self._source.base_score,
                    extra={"feed_url": self._source.url},
                ))
            except Exception as e:
                logger.warning(f"[{self.name}] Erreur entrée RSS : {e}")

        logger.info(f"[{self.name}] {len(articles)} articles récupérés")
        return articles

    async def health_check(self) -> bool:
        try:
            feed = feedparser.parse(self._source.url)
            return not feed.bozo or len(feed.entries) > 0
        except Exception:
            return False


def build_rss_scrapers() -> list[RssScraper]:
    """Retourne la liste de tous les scrapers RSS configurés."""
    return [RssScraper(source) for source in RSS_SOURCES]
