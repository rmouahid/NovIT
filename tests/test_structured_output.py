"""Contenu structuré des outils d'articles, validé par le client MCP du SDK
contre le schéma de sortie déclaré (une réponse non conforme lève une erreur)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from mcp import Client

from novit.mcp import server
from novit.mcp.cache import cache
from novit.scrapers.base import Article

ARTICLE_TOOLS = {"novit_get_news", "novit_search", "novit_get_by_domain"}
WRITE_TOOLS = {"novit_set_profile", "novit_set_domains", "novit_feedback"}


def make_article(title="Rust 2.0", url="https://example.com/rust"):
    return Article(
        title=title,
        url=url,
        summary="Une nouvelle version majeure.",
        published_at=datetime(2026, 11, 5, 9, 30, tzinfo=UTC),
        source="hacker_news",
        domains=["dev"],
        profiles=["ETUDIANT", "INGENIEUR"],
        score=0.8,
    )


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


async def test_article_tools_declare_an_output_schema():
    async with Client(server.app) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    for name in ARTICLE_TOOLS:
        schema = tools[name].output_schema
        assert schema["required"] == ["articles", "offline"]
        assert schema["properties"]["articles"]["items"]["required"] == [
            "title", "url", "source", "published_at", "domains",
        ]  # fmt: skip


async def test_tools_declare_whether_they_change_state():
    async with Client(server.app) as client:
        tools = (await client.list_tools()).tools

    for tool in tools:
        assert tool.annotations is not None, tool.name
        assert tool.annotations.read_only_hint == (tool.name not in WRITE_TOOLS)


async def test_search_returns_articles_as_structured_content():
    with patch("novit.mcp.handlers.store") as store:
        store.search = AsyncMock(return_value=[make_article()])
        async with Client(server.app) as client:
            result = await client.call_tool("novit_search", {"query": "rust"})

    assert not result.is_error
    assert "Rust 2.0" in result.content[0].text  # le Markdown reste pour le modèle
    assert result.structured_content == {
        "articles": [
            {
                "title": "Rust 2.0",
                "url": "https://example.com/rust",
                "source": "hacker_news",
                "published_at": "2026-11-05T09:30:00+00:00",
                "domains": ["dev"],
                "summary": "Une nouvelle version majeure.",
                "score": 0.8,
            }
        ],
        "offline": False,
    }


async def test_an_empty_search_still_returns_structured_content():
    with patch("novit.mcp.handlers.store") as store:
        store.search = AsyncMock(return_value=[])
        async with Client(server.app) as client:
            result = await client.call_tool("novit_search", {"query": "zzz"})

    assert result.structured_content == {"articles": [], "offline": False}


async def test_offline_answers_are_flagged():
    articles = [
        make_article(f"Article {i}", f"https://example.com/{i}") for i in range(3)
    ]
    with (
        patch("novit.mcp.handlers.store") as store,
        patch("novit.mcp.handlers._collect", AsyncMock(return_value=False)),
        patch("novit.mcp.handlers.retry"),
    ):
        store.get_recent = AsyncMock(side_effect=[[], articles])
        store.retention_days = 7
        store.last_inserted_at = AsyncMock(return_value=datetime.now(tz=UTC))
        async with Client(server.app) as client:
            result = await client.call_tool("novit_get_by_domain", {"domaine": "dev"})

    assert not result.is_error
    assert result.structured_content["offline"] is True
    assert len(result.structured_content["articles"]) == 3
