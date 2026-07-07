from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp.errors import NovitError, NovitErrorCode
from src.mcp.handlers import (
    handle_get_by_domain,
    handle_get_news,
    handle_get_profile,
    handle_search,
)
from src.mcp.schemas import (
    GetByDomainInput,
    GetNewsInput,
    GetProfileInput,
    SearchInput,
)
from src.scrapers.base import Article
from src.scrapers.manager import FetchResult


def make_article(title="Test", url="https://example.com/1", domains=None, score=0.6):
    return Article(
        title=title,
        url=url,
        summary="Summary text",
        published_at=datetime.now(tz=UTC),
        source="hacker_news",
        domains=domains or ["ia"],
        profiles=["ETUDIANT", "INGENIEUR"],
        score=score,
    )


@pytest.fixture(autouse=True)
def clear_cache():
    from src.mcp.cache import cache

    cache.clear()
    yield
    cache.clear()


class TestHandleGetNews:
    async def test_returns_news_from_store(self):
        articles = [
            make_article(f"Article {i}", url=f"https://x.com/{i}") for i in range(10)
        ]
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.get_recent = AsyncMock(return_value=articles)
            result = await handle_get_news(
                GetNewsInput(profil="ETUDIANT", domaines=["ia"])
            )

        assert "Veille NovIT" in result
        assert "ETUDIANT" in result

    async def test_triggers_scraper_when_empty(self):
        with (
            patch("src.mcp.handlers.store") as mock_store,
            patch("src.mcp.handlers._manager") as mock_manager,
            patch("src.mcp.handlers.tagger") as mock_tagger,
        ):
            mock_store.get_recent = AsyncMock(return_value=[])
            mock_store.save = AsyncMock()
            mock_manager.fetch_all = AsyncMock(return_value=FetchResult(articles=[]))
            mock_tagger.tag_all = MagicMock(return_value=[])

            result = await handle_get_news(GetNewsInput(profil="ETUDIANT"))

        assert "Aucun article" in result

    async def test_cache_hit_returns_same_result(self):
        articles = [make_article(f"A{i}", url=f"https://x.com/{i}") for i in range(10)]
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.get_recent = AsyncMock(return_value=articles)
            params = GetNewsInput(profil="ETUDIANT", domaines=["ia"])
            result1 = await handle_get_news(params)
            result2 = await handle_get_news(params)

        assert result1 == result2
        assert mock_store.get_recent.call_count == 1  # second call hit cache

    async def test_scraper_error_with_empty_store_raises(self):
        with (
            patch("src.mcp.handlers.store") as mock_store,
            patch("src.mcp.handlers._manager") as mock_manager,
            patch("src.mcp.handlers.tagger") as mock_tagger,
        ):
            mock_store.get_recent = AsyncMock(return_value=[])
            mock_store.save = AsyncMock()
            mock_manager.fetch_all = AsyncMock(
                side_effect=RuntimeError("network error")
            )
            mock_tagger.tag_all = MagicMock(return_value=[])

            with pytest.raises(NovitError) as exc:
                await handle_get_news(GetNewsInput(profil="ETUDIANT"))

        assert exc.value.code == NovitErrorCode.SOURCE_UNAVAILABLE


class TestHandleSearch:
    async def test_returns_results(self):
        articles = [make_article("Python tutorial")]
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.search = AsyncMock(return_value=articles)
            result = await handle_search(SearchInput(query="python"))

        assert "1 résultat" in result
        assert "python" in result.lower()

    async def test_no_results(self):
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.search = AsyncMock(return_value=[])
            result = await handle_search(SearchInput(query="zzz_nothing"))

        assert "Aucun résultat" in result

    async def test_domain_filter(self):
        articles = [
            make_article("IA article", url="https://x.com/1", domains=["ia"]),
            make_article("Dev article", url="https://x.com/2", domains=["dev"]),
        ]
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.search = AsyncMock(return_value=articles)
            result = await handle_search(SearchInput(query="article", domaine="ia"))

        assert "IA article" in result
        assert "Dev article" not in result

    async def test_pagination(self):
        articles = [make_article(f"A{i}", url=f"https://x.com/{i}") for i in range(5)]
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.search = AsyncMock(return_value=articles)
            result = await handle_search(
                SearchInput(query="article", page=1, per_page=3)
            )

        assert "5 résultat" in result


class TestHandleGetProfile:
    async def test_etudiant(self):
        result = await handle_get_profile(GetProfileInput(profil="ETUDIANT"))
        assert "ETUDIANT" in result

    async def test_ingenieur(self):
        result = await handle_get_profile(GetProfileInput(profil="INGENIEUR"))
        assert "INGENIEUR" in result

    async def test_raises_novit_error_on_invalid(self):
        with patch(
            "src.mcp.handlers.get_profile", side_effect=ValueError("Profil inconnu")
        ):
            with pytest.raises(NovitError) as exc:
                await handle_get_profile(GetProfileInput(profil="ETUDIANT"))
        assert exc.value.code == NovitErrorCode.INVALID_PROFILE


class TestHandleGetByDomain:
    async def test_returns_articles(self):
        articles = [
            make_article(f"A{i}", url=f"https://x.com/{i}", domains=["ia"])
            for i in range(5)
        ]
        with (
            patch("src.mcp.handlers.store") as mock_store,
            patch("src.mcp.handlers.cache") as mock_cache,
        ):
            mock_store.get_recent = AsyncMock(return_value=articles)
            mock_cache.get = MagicMock(return_value=None)
            mock_cache.set = MagicMock()
            result = await handle_get_by_domain(GetByDomainInput(domaine="ia"))

        assert "ia" in result

    async def test_triggers_scraper_when_empty(self):
        articles = [make_article("Fresh", domains=["ia"])]
        with (
            patch("src.mcp.handlers.store") as mock_store,
            patch("src.mcp.handlers._manager") as mock_manager,
            patch("src.mcp.handlers.tagger") as mock_tagger,
            patch("src.mcp.handlers.cache") as mock_cache,
        ):
            mock_store.get_recent = AsyncMock(side_effect=[[], articles])
            mock_store.save = AsyncMock()
            mock_manager.fetch_by_domains = AsyncMock(
                return_value=FetchResult(articles=articles)
            )
            mock_tagger.tag_all = MagicMock(return_value=articles)
            mock_cache.get = MagicMock(return_value=None)
            mock_cache.set = MagicMock()

            result = await handle_get_by_domain(GetByDomainInput(domaine="ia"))

        mock_manager.fetch_by_domains.assert_called_once()
        assert "ia" in result
