"""Serveur MCP : déclaration des outils et dispatch, via un client en mémoire."""

from mcp import Client

from novit.mcp import server
from novit.mcp.errors import NovitError, NovitErrorCode


async def test_list_tools_exposes_every_declared_tool():
    async with Client(server.app) as client:
        result = await client.list_tools()

    assert [tool.name for tool in result.tools] == [tool.name for tool in server.TOOLS]
    assert all(tool.input_schema["type"] == "object" for tool in result.tools)


async def test_call_tool_dispatches_to_the_handler(monkeypatch):
    async def fake_dig_url(url):
        return f"analyse de {url}"

    monkeypatch.setattr(server, "dig_url", fake_dig_url)

    async with Client(server.app) as client:
        result = await client.call_tool("novit_dig", {"url": "https://example.org"})

    assert not result.is_error
    assert result.content[0].text == "analyse de https://example.org"


async def test_unknown_tool_is_reported_as_an_error():
    async with Client(server.app) as client:
        result = await client.call_tool("novit_inconnu", {})

    assert result.is_error
    assert "Outil inconnu : novit_inconnu" in result.content[0].text


async def test_novit_error_is_returned_as_a_tool_error(monkeypatch):
    error = NovitError(NovitErrorCode.SCRAPER_ERROR, "URL refusée")

    async def failing_dig_url(url):
        raise error

    monkeypatch.setattr(server, "dig_url", failing_dig_url)

    async with Client(server.app) as client:
        result = await client.call_tool("novit_dig", {"url": "ftp://x"})

    assert result.is_error
    assert result.content[0].text == error.to_mcp_error()


async def test_unexpected_exception_does_not_crash_the_server(monkeypatch):
    async def broken_dig_url(url):
        raise RuntimeError("boom")

    monkeypatch.setattr(server, "dig_url", broken_dig_url)
    monkeypatch.setattr(server, "capture_tool_error", lambda *a, **k: None)

    async with Client(server.app) as client:
        result = await client.call_tool("novit_dig", {"url": "https://example.org"})
        still_alive = await client.list_tools()

    assert result.is_error
    assert result.content[0].text == "Erreur interne NovIT : boom"
    assert still_alive.tools
