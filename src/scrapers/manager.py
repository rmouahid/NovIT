import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone

from loguru import logger

from src.scrapers.ai_blogs import build_ai_scrapers
from src.scrapers.base import Article, BaseScraper
from src.scrapers.cve import ANSSIScraper, CVEScraper
from src.scrapers.eng_blogs import build_eng_scrapers
from src.scrapers.hacker_news import HackerNewsScraper
from src.scrapers.github_trending import GitHubTrendingScraper
from src.scrapers.regulation import build_regulation_scrapers
from src.scrapers.rss import build_rss_scrapers
from src.scrapers.training import build_training_scrapers


@dataclass
class ScraperReport:
    scraper: str
    success: bool
    article_count: int
    duration_ms: float
    error: str = ""


@dataclass
class FetchResult:
    articles: list[Article]
    reports: list[ScraperReport] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @property
    def sources_ok(self) -> list[str]:
        return [r.scraper for r in self.reports if r.success]

    @property
    def sources_failed(self) -> list[str]:
        return [r.scraper for r in self.reports if not r.success]


class ScraperManager:
    """Orchestre tous les scrapers NovIT en parallèle.

    Responsabilités :
    - Lancer les scrapers en parallèle (asyncio.gather)
    - Gérer les timeouts par scraper
    - Agréger et dédupliquer les articles
    - Générer un rapport d'exécution
    """

    def __init__(self, timeout_per_scraper: int = 30):
        self.timeout = timeout_per_scraper
        self._scrapers: list[BaseScraper] = self._build_all_scrapers()

    def _build_all_scrapers(self) -> list[BaseScraper]:
        scrapers: list[BaseScraper] = [
            HackerNewsScraper(),
            GitHubTrendingScraper(),
            CVEScraper(),
            ANSSIScraper(),
        ]
        scrapers.extend(build_rss_scrapers())
        scrapers.extend(build_ai_scrapers())
        scrapers.extend(build_eng_scrapers())
        scrapers.extend(build_regulation_scrapers())
        scrapers.extend(build_training_scrapers())
        return scrapers

    async def fetch_all(self) -> FetchResult:
        """Lance tous les scrapers en parallèle et agrège les résultats."""
        logger.info(f"ScraperManager : lancement de {len(self._scrapers)} scrapers")
        tasks = [self._run_scraper(scraper) for scraper in self._scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        all_articles: list[Article] = []
        reports: list[ScraperReport] = []

        for articles, report in results:
            all_articles.extend(articles)
            reports.append(report)

        deduplicated = self._deduplicate(all_articles)
        logger.info(
            f"ScraperManager : {len(deduplicated)} articles uniques "
            f"({len(all_articles) - len(deduplicated)} doublons supprimés)"
        )

        return FetchResult(articles=deduplicated, reports=reports)

    async def fetch_by_domains(self, domains: list[str]) -> FetchResult:
        """Récupère les articles en filtrant les scrapers par domaine."""
        relevant = [s for s in self._scrapers if any(d in s.domains for d in domains)]
        if not relevant:
            logger.warning(f"Aucun scraper pour les domaines : {domains}")
            return FetchResult(articles=[])

        logger.info(f"ScraperManager : {len(relevant)} scrapers pour {domains}")
        tasks = [self._run_scraper(scraper) for scraper in relevant]
        results = await asyncio.gather(*tasks)

        all_articles: list[Article] = []
        reports: list[ScraperReport] = []
        for articles, report in results:
            filtered = [a for a in articles if any(d in a.domains for d in domains)]
            all_articles.extend(filtered)
            reports.append(report)

        return FetchResult(articles=self._deduplicate(all_articles), reports=reports)

    async def _run_scraper(self, scraper: BaseScraper) -> tuple[list[Article], ScraperReport]:
        start = asyncio.get_event_loop().time()
        try:
            articles = await asyncio.wait_for(scraper.fetch(), timeout=self.timeout)
            duration = (asyncio.get_event_loop().time() - start) * 1000
            return articles, ScraperReport(
                scraper=scraper.name,
                success=True,
                article_count=len(articles),
                duration_ms=round(duration, 1),
            )
        except TimeoutError:
            logger.warning(f"[{scraper.name}] Timeout ({self.timeout}s)")
            return [], ScraperReport(scraper=scraper.name, success=False, article_count=0, duration_ms=self.timeout * 1000, error="timeout")
        except Exception as e:
            logger.error(f"[{scraper.name}] Erreur : {e}")
            duration = (asyncio.get_event_loop().time() - start) * 1000
            return [], ScraperReport(scraper=scraper.name, success=False, article_count=0, duration_ms=round(duration, 1), error=str(e))

    def _deduplicate(self, articles: list[Article]) -> list[Article]:
        seen: set[str] = set()
        unique: list[Article] = []
        for article in articles:
            if article.url not in seen:
                seen.add(article.url)
                unique.append(article)
        return unique

    async def health_check_all(self) -> dict[str, bool]:
        """Vérifie la disponibilité de toutes les sources en parallèle."""
        tasks = {scraper.name: scraper.health_check() for scraper in self._scrapers}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        return {
            name: (result is True)
            for name, result in zip(tasks.keys(), results)
        }
