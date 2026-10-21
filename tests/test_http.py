"""Transport HTTP : endpoint MCP, jeton bearer et route /health, sur un vrai
serveur uvicorn local."""

import socket
import threading
import time

import httpx
import httpx2
import pytest
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from novit.mcp import health, server
from novit.mcp.http import create_http_app

TOKEN = "jeton-de-test"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _serve(app):
    port = _free_port()
    uv = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_config=None)
    )
    thread = threading.Thread(target=uv.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not uv.started:
        if time.monotonic() > deadline:
            raise RuntimeError("le serveur HTTP de test n'a pas démarré")
        time.sleep(0.05)
    return uv, thread, f"http://127.0.0.1:{port}"


@pytest.fixture
def base_url():
    uv, thread, url = _serve(create_http_app(server.app, "127.0.0.1", TOKEN))
    yield url
    uv.should_exit = True
    thread.join(timeout=10)


def _mcp_client(base_url, token=TOKEN):
    http_client = httpx2.AsyncClient(headers={"Authorization": f"Bearer {token}"})
    return Client(streamable_http_client(f"{base_url}/mcp", http_client=http_client))


async def test_mcp_tools_are_reachable_with_the_token(base_url, monkeypatch):
    async def fake_dig_url(url):
        return f"analyse de {url}"

    monkeypatch.setattr(server, "dig_url", fake_dig_url)

    async with _mcp_client(base_url) as client:
        tools = await client.list_tools()
        result = await client.call_tool("novit_dig", {"url": "https://example.org"})

    assert [tool.name for tool in tools.tools] == [tool.name for tool in server.TOOLS]
    assert result.content[0].text == "analyse de https://example.org"


@pytest.mark.parametrize(
    "headers", [{}, {"Authorization": "Bearer mauvais"}, {"Authorization": TOKEN}]
)
def test_mcp_endpoint_rejects_a_missing_or_wrong_token(base_url, headers):
    response = httpx.post(f"{base_url}/mcp", headers=headers, json={})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_health_is_public_and_makes_no_network_call(base_url, monkeypatch):
    async def must_not_run():
        raise AssertionError("la sonde de vie ne doit pas vérifier les sources")

    monkeypatch.setattr("novit.mcp.http.get_health", must_not_run)

    response = httpx.get(f"{base_url}/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == health.read_version()
    assert body["uptime_seconds"] >= 0


def test_health_with_sources_reuses_the_health_report(base_url, monkeypatch):
    report = health.HealthReport(
        status="degraded",
        uptime_seconds=12.0,
        version="1.2.3",
        sources=[health.SourceStatus("hacker_news", False, 0.0, "indisponible")],
    )

    async def fake_get_health():
        return report

    monkeypatch.setattr("novit.mcp.http.get_health", fake_get_health)

    response = httpx.get(f"{base_url}/health", params={"sources": "1"})

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["sources"][0]["name"] == "hacker_news"


def test_listening_on_the_network_without_a_token_is_refused():
    with pytest.raises(ValueError, match="NOVIT_API_TOKEN"):
        create_http_app(server.app, "0.0.0.0", "")


def test_local_listening_without_a_token_is_allowed():
    assert create_http_app(server.app, "127.0.0.1", "")


def test_transport_option_selects_http(monkeypatch):
    calls = {}

    def fake_run_http(app, host, port, token):
        calls.update(app=app, host=host, port=port, token=token)

    monkeypatch.setattr("novit.mcp.http.run_http", fake_run_http)

    server.run(["--transport", "http"])

    assert calls["app"] is server.app
    assert calls["port"] == server._settings.port
