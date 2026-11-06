"""Bout en bout comme un client MCP de bureau : le serveur est lancé en
sous-processus (`python -m novit.mcp`) et interrogé en stdio par le client du
SDK, qui valide aussi le contenu structuré contre les schémas de sortie.

Aucun appel réseau : la recherche lit une base SQLite préparée par le test,
dans un dossier de travail qui contient une copie de `config/`, comme un
clone du dépôt (la configuration n'est embarquée que dans la wheel).
"""

import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from mcp import Client, StdioServerParameters

from novit.mcp import server
from novit.scrapers.base import Article
from novit.scrapers.storage import ArticleStore

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
async def workdir(tmp_path):
    shutil.copytree(REPO / "config", tmp_path / "config")
    store = ArticleStore(db_path=str(tmp_path / "novit.db"))
    await store.save(
        [
            Article(
                title="WebAssembly component model reaches 1.0",
                url="https://example.com/wasm",
                summary="The component model is now stable.",
                published_at=datetime.now(tz=UTC),
                source="hacker_news",
                domains=["dev"],
                profiles=["ETUDIANT", "INGENIEUR"],
                score=0.7,
            )
        ]
    )
    return tmp_path


def _params(workdir) -> StdioServerParameters:
    env = {
        **os.environ,
        "NOVIT_DB_PATH": str(workdir / "novit.db"),
        "NOVIT_LOG_LEVEL": "WARNING",
        # Le sous-processus importe le paquet du dépôt, installé ou non.
        "PYTHONPATH": os.pathsep.join(
            filter(None, [str(REPO), os.environ.get("PYTHONPATH")])
        ),
    }
    env.pop("SENTRY_DSN", None)
    return StdioServerParameters(
        command=sys.executable, args=["-m", "novit.mcp"], env=env, cwd=str(workdir)
    )


async def test_a_stdio_client_lists_every_tool(workdir):
    async with Client(_params(workdir)) as client:
        tools = (await client.list_tools()).tools

    assert sorted(tool.name for tool in tools) == sorted(t.name for t in server.TOOLS)


async def test_a_stdio_client_searches_the_local_database(workdir):
    async with Client(_params(workdir)) as client:
        result = await client.call_tool("novit_search", {"query": "webassembly"})

    assert not result.is_error
    assert "WebAssembly component model" in result.content[0].text
    [article] = result.structured_content["articles"]
    assert article["url"] == "https://example.com/wasm"


async def test_a_stdio_client_gets_tool_errors_not_crashes(workdir):
    async with Client(_params(workdir)) as client:
        result = await client.call_tool("novit_get_profile", {"profil": "INCONNU"})
        health = await client.call_tool("novit_health", {})

    assert result.is_error
    assert not health.is_error  # le serveur répond encore après l'erreur
