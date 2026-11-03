"""Mode hors-ligne dégradé (#91) : réponse servie depuis le cache local quand
aucune source ne répond, âge des données affiché, relance en arrière-plan."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from novit.mcp import offline
from novit.mcp.errors import NovitError, NovitErrorCode
from novit.mcp.handlers import handle_get_by_domain, handle_get_news
from novit.mcp.offline import (
    TTL_OFFLINE,
    BackgroundRetry,
    all_sources_down,
    format_age,
    offline_banner,
)
from novit.mcp.schemas import GetByDomainInput, GetNewsInput
from novit.scrapers.base import Article
from novit.scrapers.manager import FetchResult, ScraperReport
from novit.scrapers.storage import ArticleStore


def article(i: int, age: timedelta, domains=None) -> Article:
    return Article(
        title=f"Article {i}",
        url=f"https://example.com/{i}",
        summary="Résumé",
        published_at=datetime.now(tz=UTC) - age,
        source="hacker_news",
        domains=domains or ["ia"],
        profiles=["ETUDIANT", "INGENIEUR"],
        score=0.6,
    )


def report(name: str, ok: bool) -> ScraperReport:
    return ScraperReport(scraper=name, success=ok, article_count=0, duration_ms=1.0)


DOWN = FetchResult(articles=[], reports=[report("hn", False), report("rss", False)])


@pytest.fixture(autouse=True)
def clear_cache():
    from novit.mcp.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
async def stale_store(tmp_path):
    """Base contenant uniquement des articles vieux de 3 jours."""
    s = ArticleStore(db_path=str(tmp_path / "offline.db"), retention_days=7)
    await s.init()
    await s.save([article(i, timedelta(days=3)) for i in range(5)])
    return s


@pytest.fixture
def no_retry():
    """Remplace la relance en arrière-plan par un faux qui enregistre l'appel."""
    fake = MagicMock(running=True)
    with patch("novit.mcp.handlers.retry", fake):
        yield fake


class TestHelpers:
    def test_all_sources_down(self):
        assert all_sources_down(DOWN)
        assert not all_sources_down(
            FetchResult(articles=[], reports=[report("hn", False), report("rss", True)])
        )
        # Aucun scraper lancé : rien ne permet de conclure à une panne
        assert not all_sources_down(FetchResult(articles=[]))

    @pytest.mark.parametrize(
        "delta,expected",
        [
            (timedelta(seconds=30), "0 min"),
            (timedelta(minutes=12), "12 min"),
            (timedelta(hours=3, minutes=40), "3 h"),
            (timedelta(days=2, hours=5), "2 j"),
        ],
    )
    def test_format_age(self, delta, expected):
        assert format_age(delta) == expected

    def test_banner_shows_last_update_and_retry(self):
        now = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
        text = offline_banner(now - timedelta(hours=5), retrying=True, now=now)
        assert "Mode hors-ligne" in text
        assert "02/11 à 07:00 UTC" in text
        assert "il y a 5 h" in text
        assert "arrière-plan" in text

    def test_banner_without_date(self):
        text = offline_banner(None, retrying=False)
        assert "Mode hors-ligne" in text
        assert "Dernière collecte" not in text
        assert "arrière-plan" not in text


class TestBackgroundRetry:
    async def test_stops_at_first_success(self):
        refresh = AsyncMock(side_effect=[False, True, True])
        r = BackgroundRetry(delays=(0, 0, 0))
        r.schedule(refresh)
        await r.wait()
        assert refresh.await_count == 2
        assert not r.running

    async def test_gives_up_after_all_delays_and_survives_errors(self):
        refresh = AsyncMock(side_effect=[RuntimeError("réseau"), False])
        r = BackgroundRetry(delays=(0, 0))
        r.schedule(refresh)
        await r.wait()
        assert refresh.await_count == 2

    async def test_single_loop_at_a_time(self):
        refresh = AsyncMock(return_value=True)
        r = BackgroundRetry(delays=(0.05,))
        r.schedule(refresh)
        r.schedule(refresh)
        await r.wait()
        assert refresh.await_count == 1


class TestGetNewsOffline:
    async def test_serves_stale_articles_with_banner(self, stale_store, no_retry):
        with (
            patch("novit.mcp.handlers.store", stale_store),
            patch("novit.mcp.handlers._manager") as manager,
        ):
            manager.fetch_by_domains = AsyncMock(return_value=DOWN)
            result = await handle_get_news(
                GetNewsInput(profil="ETUDIANT", domaines=["ia"], periode="24h")
            )

        assert result.startswith("> ⚠️ **Mode hors-ligne**")
        assert "il y a 0 min" in result  # articles insérés à l'instant
        assert "Article 0" in result  # publié il y a 3 jours, hors période 24h
        no_retry.schedule.assert_called_once()

    async def test_scraper_exception_also_serves_cache(self, stale_store, no_retry):
        with (
            patch("novit.mcp.handlers.store", stale_store),
            patch("novit.mcp.handlers._manager") as manager,
        ):
            manager.fetch_all = AsyncMock(side_effect=RuntimeError("DNS"))
            result = await handle_get_news(GetNewsInput(profil="ETUDIANT"))

        assert "Mode hors-ligne" in result
        assert "Article" in result

    async def test_degraded_answer_is_cached_briefly(self, stale_store, no_retry):
        with (
            patch("novit.mcp.handlers.store", stale_store),
            patch("novit.mcp.handlers._manager") as manager,
            patch("novit.mcp.handlers.cache") as cache,
        ):
            cache.get.return_value = None
            manager.fetch_all = AsyncMock(return_value=DOWN)
            await handle_get_news(GetNewsInput(profil="ETUDIANT"))

        assert cache.set.call_args.kwargs["ttl"] == TTL_OFFLINE

    async def test_empty_cache_still_raises(self, tmp_path, no_retry):
        empty = ArticleStore(db_path=str(tmp_path / "empty.db"))
        with (
            patch("novit.mcp.handlers.store", empty),
            patch("novit.mcp.handlers._manager") as manager,
        ):
            manager.fetch_all = AsyncMock(return_value=DOWN)
            with pytest.raises(NovitError) as exc:
                await handle_get_news(GetNewsInput(profil="ETUDIANT"))

        assert exc.value.code == NovitErrorCode.SOURCE_UNAVAILABLE
        no_retry.schedule.assert_not_called()

    async def test_partial_outage_is_not_offline(self, tmp_path, no_retry):
        s = ArticleStore(db_path=str(tmp_path / "partial.db"))
        fresh = [article(i, timedelta(hours=1)) for i in range(3)]
        partial = FetchResult(
            articles=fresh, reports=[report("hn", True), report("rss", False)]
        )
        with (
            patch("novit.mcp.handlers.store", s),
            patch("novit.mcp.handlers._manager") as manager,
        ):
            manager.fetch_all = AsyncMock(return_value=partial)
            result = await handle_get_news(GetNewsInput(profil="ETUDIANT"))

        assert "Mode hors-ligne" not in result
        assert "Article 0" in result
        no_retry.schedule.assert_not_called()


class TestGetByDomainOffline:
    async def test_serves_stale_articles_with_banner(self, stale_store, no_retry):
        with (
            patch("novit.mcp.handlers.store", stale_store),
            patch("novit.mcp.handlers._manager") as manager,
        ):
            manager.fetch_by_domains = AsyncMock(return_value=DOWN)
            result = await handle_get_by_domain(GetByDomainInput(domaine="ia"))

        assert "Mode hors-ligne" in result
        assert "Domaine : ia" in result


class TestRetryRefreshesStore:
    async def test_background_retry_saves_articles_when_sources_return(self, tmp_path):
        s = ArticleStore(db_path=str(tmp_path / "retry.db"))
        await s.init()
        await s.save([article(0, timedelta(days=2))])
        back = FetchResult(
            articles=[article(1, timedelta(minutes=5))], reports=[report("hn", True)]
        )
        r = BackgroundRetry(delays=(0,))
        with (
            patch("novit.mcp.handlers.store", s),
            patch("novit.mcp.handlers.retry", r),
            patch("novit.mcp.handlers._manager") as manager,
        ):
            manager.fetch_all = AsyncMock(side_effect=[DOWN, back])
            first = await handle_get_news(GetNewsInput(profil="ETUDIANT"))
            await r.wait()

        assert "Mode hors-ligne" in first
        recent = await s.get_recent(hours=1)
        assert [a.url for a in recent] == ["https://example.com/1"]


def test_module_defaults():
    assert offline.RETRY_DELAYS == (30, 120, 300)
    assert offline.TTL_OFFLINE < 3600
