"""Tests de régression des formats de réponse NovIT (docs/RESPONSE_FORMATS.md).

Objectif : geler la structure markdown que chaque handler produit pour des
requêtes standard, par profil, afin de détecter toute régression accidentelle
lors d'un futur changement de prompt/handler (en-têtes manquants, emoji
disparus, structure cassée...). Ces tests vérifient la forme, pas le contenu
exact (dates, scores) qui varie naturellement.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import Response

from src.mcp.dig import dig_url
from src.mcp.errors import NovitError, NovitErrorCode
from src.mcp.handlers import (
    handle_get_by_domain,
    handle_get_news,
    handle_get_profile,
    handle_search,
)
from src.mcp.related import find_related
from src.mcp.schemas import GetByDomainInput, GetNewsInput, GetProfileInput, SearchInput
from src.scrapers.base import Article
from src.scrapers.manager import FetchResult


def make_article(title="Test", url="https://example.com/1", domains=None, score=0.6):
    return Article(
        title=title,
        url=url,
        summary="Résumé de test suffisamment long pour être affiché correctement.",
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


class TestGetNewsFormatByProfile:
    """Format 2 (liste de news) : requête standard pour chaque profil NovIT."""

    @pytest.mark.parametrize("profil", ["ETUDIANT", "INGENIEUR"])
    async def test_standard_request_format(self, profil):
        articles = [
            make_article(f"Article {i}", url=f"https://x.com/{i}") for i in range(5)
        ]
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.get_recent = AsyncMock(return_value=articles)
            result = await handle_get_news(
                GetNewsInput(profil=profil, domaines=["ia"], nb_articles=5)
            )

        assert result.startswith("# ")
        assert f"Profil {profil}" in result
        assert "article(s)" in result
        assert "### 1." in result
        assert "🔗 https://x.com/" in result
        assert "📅" in result and "🏷" in result and "📰" in result

    async def test_empty_result_format(self):
        with (
            patch("src.mcp.handlers.store") as mock_store,
            patch("src.mcp.handlers._manager") as mock_manager,
            patch("src.mcp.handlers.tagger") as mock_tagger,
        ):
            mock_store.get_recent = AsyncMock(return_value=[])
            mock_store.save = AsyncMock()
            mock_manager.fetch_all = AsyncMock(return_value=FetchResult(articles=[]))
            mock_tagger.tag_all.return_value = []
            result = await handle_get_news(GetNewsInput(profil="ETUDIANT"))

        assert result.startswith("# ")
        assert "Aucun article trouvé" in result
        assert "ETUDIANT" in result


class TestSearchFormat:
    async def test_standard_request_format(self):
        articles = [
            make_article(f"Résultat {i}", url=f"https://x.com/{i}") for i in range(3)
        ]
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.search = AsyncMock(return_value=articles)
            result = await handle_search(SearchInput(query="python"))

        assert result.startswith("# Recherche")
        assert "« python »" in result
        assert "résultat(s)" in result
        assert "### 1." in result

    async def test_empty_result_format(self):
        with patch("src.mcp.handlers.store") as mock_store:
            mock_store.search = AsyncMock(return_value=[])
            result = await handle_search(SearchInput(query="zzz"))

        assert result.startswith("# Recherche")
        assert "Aucun résultat" in result


class TestGetByDomainFormat:
    async def test_standard_request_format(self):
        articles = [
            make_article(f"A{i}", url=f"https://x.com/{i}", domains=["ia"])
            for i in range(3)
        ]
        with (
            patch("src.mcp.handlers.store") as mock_store,
            patch("src.mcp.handlers.cache") as mock_cache,
        ):
            mock_store.get_recent = AsyncMock(return_value=articles)
            mock_cache.get.return_value = None
            result = await handle_get_by_domain(GetByDomainInput(domaine="ia"))

        assert result.startswith("# Domaine : ia")
        assert "### 1." in result


class TestGetProfileFormat:
    @pytest.mark.parametrize("profil", ["ETUDIANT", "INGENIEUR"])
    async def test_standard_request_format(self, profil):
        result = await handle_get_profile(GetProfileInput(profil=profil))

        assert result.startswith(f"# Profil NovIT : {profil}")
        assert "Sources prioritaires" in result
        assert "Domaines favoris" in result
        assert "Score minimum" in result

    async def test_invalid_profile_raises_documented_error_code(self):
        with pytest.raises(NovitError) as exc:
            with patch(
                "src.mcp.handlers.get_profile",
                side_effect=ValueError("Profil inconnu"),
            ):
                await handle_get_profile(GetProfileInput(profil="ETUDIANT"))
        assert exc.value.code == NovitErrorCode.INVALID_PROFILE


class TestRelatedFormat:
    async def test_standard_request_format(self):
        candidates = [
            make_article(
                "Article proche du sujet", url="https://x.com/1", domains=["ia"]
            ),
        ]
        with patch("src.mcp.related.store") as mock_store:
            mock_store.get_recent = AsyncMock(return_value=candidates)
            result = await find_related(
                url="https://x.com/ref",
                title="Article proche du sujet exact",
                domains=["ia"],
            )

        assert result.startswith("# Articles similaires")
        assert "### 1." in result
        assert "🔗" in result and "📅" in result and "📰" in result
        assert "similarité" in result

    async def test_no_match_format(self):
        with patch("src.mcp.related.store") as mock_store:
            mock_store.get_recent = AsyncMock(return_value=[])
            result = await find_related(
                url="https://x.com/ref", title="Sujet inédit", domains=["ia"]
            )

        assert "Aucun article similaire" in result


class TestDigFormat:
    async def test_standard_request_format(self):
        html = (
            "<html><body><article>"
            + ("Contenu de test bien détaillé. " * 20)
            + "</article></body></html>"
        )
        with respx.mock:
            respx.get("https://example.com/article").mock(
                return_value=Response(
                    200, headers={"content-type": "text/html"}, text=html
                )
            )
            result = await dig_url("https://example.com/article")

        assert result.startswith("# Contenu extrait")
        assert "**Source :**" in result

    async def test_timeout_format(self):
        import httpx

        with respx.mock:
            respx.get("https://example.com/slow").mock(
                side_effect=httpx.TimeoutException("timeout")
            )
            result = await dig_url("https://example.com/slow")

        assert "timeout" in result.lower()
