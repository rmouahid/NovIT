"""Tests d'intégration : plusieurs modules NovIT exercés ensemble, sans mock des
composants internes (seul le réseau des scrapers est simulé).
"""

from datetime import UTC, datetime

import pytest

from src.mcp.handlers import _format_articles
from src.profiles.filter import filter_and_rank
from src.profiles.profile import get_profile
from src.scrapers.base import Article, BaseScraper
from src.scrapers.manager import ScraperManager
from src.scrapers.storage import ArticleStore
from src.scrapers.tagger import DomainTagger


def make_article(title, url, source="hacker_news", domains=None, score=0.8) -> Article:
    return Article(
        title=title,
        url=url,
        summary=f"Résumé de {title}",
        published_at=datetime.now(tz=UTC),
        source=source,
        domains=domains or [],
        profiles=["ETUDIANT", "INGENIEUR"],
        score=score,
    )


class FakeScraper(BaseScraper):
    def __init__(self, name, domains, articles=None, fail=False, hang=False):
        self.name = name
        self.domains = domains
        self._articles = articles or []
        self._fail = fail
        self._hang = hang

    async def fetch(self) -> list[Article]:
        if self._fail:
            raise RuntimeError("source indisponible")
        if self._hang:
            import asyncio

            await asyncio.sleep(10)
        return self._articles

    async def health_check(self) -> bool:
        return not self._fail


class TestScraperManagerIntegration:
    async def test_fetch_all_aggregates_and_deduplicates(self):
        manager = ScraperManager()
        manager._scrapers = [
            FakeScraper(
                "source_a",
                ["ia"],
                [make_article("Article A", "https://x.com/1", source="source_a")],
            ),
            FakeScraper(
                "source_b",
                ["dev"],
                [
                    make_article("Article A dup", "https://x.com/1", source="source_b"),
                    make_article("Article B", "https://x.com/2", source="source_b"),
                ],
            ),
        ]
        result = await manager.fetch_all()

        assert len(result.articles) == 2
        assert {a.url for a in result.articles} == {
            "https://x.com/1",
            "https://x.com/2",
        }
        assert set(result.sources_ok) == {"source_a", "source_b"}
        assert result.sources_failed == []

    async def test_fetch_all_reports_failures_without_losing_successes(self):
        manager = ScraperManager()
        manager._scrapers = [
            FakeScraper("good", ["ia"], [make_article("OK", "https://x.com/ok")]),
            FakeScraper("bad", ["ia"], fail=True),
        ]
        result = await manager.fetch_all()

        assert len(result.articles) == 1
        assert result.sources_ok == ["good"]
        assert result.sources_failed == ["bad"]

    async def test_fetch_all_reports_timeout(self):
        manager = ScraperManager(timeout_per_scraper=1)
        manager._scrapers = [FakeScraper("slow", ["ia"], hang=True)]
        result = await manager.fetch_all()

        assert result.articles == []
        assert result.sources_failed == ["slow"]
        assert result.reports[0].error == "timeout"

    async def test_fetch_by_domains_filters_scrapers_and_articles(self):
        manager = ScraperManager()
        manager._scrapers = [
            FakeScraper(
                "ia_source",
                ["ia"],
                [make_article("IA news", "https://x.com/1", domains=["ia"])],
            ),
            FakeScraper(
                "dev_source",
                ["dev"],
                [make_article("Dev news", "https://x.com/2", domains=["dev"])],
            ),
        ]
        result = await manager.fetch_by_domains(["ia"])

        assert len(result.articles) == 1
        assert result.articles[0].url == "https://x.com/1"

    async def test_health_check_all(self):
        manager = ScraperManager()
        manager._scrapers = [
            FakeScraper("up", ["ia"]),
            FakeScraper("down", ["dev"], fail=True),
        ]
        health = await manager.health_check_all()
        assert health == {"up": True, "down": False}


class TestPipelineIntegration:
    """Simule le flux complet scraping → tagging → stockage → filtrage → rendu."""

    @pytest.fixture
    async def store(self, tmp_path):
        s = ArticleStore(db_path=str(tmp_path / "pipeline.db"))
        await s.init()
        return s

    async def test_full_pipeline_scrape_to_rendered_text(self, store):
        manager = ScraperManager()
        manager._scrapers = [
            FakeScraper(
                "hacker_news",
                ["ia"],
                [
                    make_article(
                        "Nouveau modèle de langage annoncé",
                        "https://x.com/llm",
                        source="hacker_news",
                        score=0.9,
                    )
                ],
            ),
        ]
        tagger = DomainTagger()

        fetched = await manager.fetch_all()
        tagged = tagger.tag_all(fetched.articles)
        saved = await store.save(tagged)
        assert saved == 1

        recent = await store.get_recent(profiles=["ETUDIANT"], hours=24, limit=10)
        assert len(recent) == 1

        profile = get_profile("ETUDIANT")
        ranked = filter_and_rank(recent, profile, limit=10)
        assert len(ranked) == 1

        text = _format_articles(ranked, "ETUDIANT", "Veille NovIT")
        assert "Nouveau modèle de langage annoncé" in text
        assert "https://x.com/llm" in text

    async def test_pipeline_deduplicates_across_sources_before_storage(self, store):
        manager = ScraperManager()
        manager._scrapers = [
            FakeScraper(
                "source_a",
                ["ia"],
                [make_article("Même actu", "https://x.com/same", source="source_a")],
            ),
            FakeScraper(
                "source_b",
                ["ia"],
                [
                    make_article(
                        "Même actu, autre titre",
                        "https://x.com/same",
                        source="source_b",
                    )
                ],
            ),
        ]
        fetched = await manager.fetch_all()
        saved = await store.save(fetched.articles)

        assert saved == 1
        recent = await store.get_recent()
        assert len(recent) == 1

    async def test_pipeline_low_score_filtered_out_for_profile(self, store):
        profile = get_profile("INGENIEUR")
        await store.save(
            [
                make_article(
                    "Article pertinent",
                    "https://x.com/1",
                    source="hacker_news",
                    domains=["dev"],
                    score=0.9,
                ),
                make_article(
                    "Article peu pertinent",
                    "https://x.com/2",
                    source="unknown_source",
                    domains=["divertissement"],
                    score=0.05,
                ),
            ]
        )
        recent = await store.get_recent(profiles=["INGENIEUR"])
        ranked = filter_and_rank(recent, profile)

        titles = [a.title for a in ranked]
        assert "Article pertinent" in titles
        assert "Article peu pertinent" not in titles
