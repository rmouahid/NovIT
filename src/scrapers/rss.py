from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
import yaml
from loguru import logger

from src.scrapers.base import Article, BaseScraper

SOURCES_CONFIG_PATH = Path("config/sources.yaml")

_REQUIRED_FIELDS = ("name", "url", "domains", "profiles")


@dataclass
class RssSource:
    name: str
    url: str
    domains: list[str]
    profiles: list[str]
    base_score: float = 0.5
    category: str = ""


class SourcesConfigError(ValueError):
    """Le fichier config/sources.yaml est absent, malformé ou invalide."""


def load_rss_sources(
    path: Path | None = None, category: str | None = None
) -> list[RssSource]:
    """Charge et valide les sources RSS déclaratives depuis config/sources.yaml.

    Lit le fichier à chaque appel (pas de cache) : combiné à
    ScraperManager.reload_sources(), une source ajoutée/modifiée est prise en
    compte sans redémarrer le serveur. Filtre par `category` si fourni.
    Lève SourcesConfigError si le fichier est absent ou qu'une entrée n'a pas
    les champs requis — on préfère un échec net au démarrage à des sources
    silencieusement ignorées.

    `path` par défaut résolu à l'appel (pas en valeur par défaut figée à
    l'import) pour que la config puisse être redirigée dynamiquement (tests,
    rechargement) via le module-level SOURCES_CONFIG_PATH.
    """
    path = path or SOURCES_CONFIG_PATH
    if not path.exists():
        raise SourcesConfigError(f"Fichier de sources introuvable : {path}")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    entries = data.get("sources", [])
    names_seen: set[str] = set()
    sources: list[RssSource] = []

    for i, entry in enumerate(entries):
        missing = [field for field in _REQUIRED_FIELDS if not entry.get(field)]
        if missing:
            raise SourcesConfigError(
                f"{path}: entrée #{i} invalide, champs manquants : {missing}"
            )
        if entry["name"] in names_seen:
            raise SourcesConfigError(
                f"{path}: nom de source dupliqué : {entry['name']}"
            )
        names_seen.add(entry["name"])

        if category and entry.get("category") != category:
            continue

        sources.append(
            RssSource(
                name=entry["name"],
                url=entry["url"],
                domains=list(entry["domains"]),
                profiles=list(entry["profiles"]),
                base_score=float(entry.get("base_score", 0.5)),
                category=entry.get("category", ""),
            )
        )

    return sources


def _parse_date(entry: dict) -> datetime:
    """Parse la date depuis un entry feedparser, retourne now() si impossible."""
    for attr in ("published", "updated"):
        value = getattr(entry, attr, None)
        if value:
            try:
                return parsedate_to_datetime(value).astimezone(UTC)
            except Exception:
                pass
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=UTC)
    return datetime.now(tz=UTC)


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

                articles.append(
                    Article(
                        title=title,
                        url=url,
                        summary=summary,
                        published_at=_parse_date(entry),
                        source=self.name,
                        domains=self._source.domains,
                        profiles=self._source.profiles,
                        score=self._source.base_score,
                        extra={"feed_url": self._source.url},
                    )
                )
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
    """Retourne les scrapers RSS de la catégorie "actualites" (config/sources.yaml)."""
    return [RssScraper(source) for source in load_rss_sources(category="actualites")]
