"""Client HTTP des sources : délai par domaine, relance sur 429, agent (#118)."""

import time

import httpx
import pytest

from novit.scrapers.http import PoliteTransport, http_client, retry_after
from novit.scrapers.rate_limiter import RateLimiter


class Recorder(httpx.AsyncBaseTransport):
    """Transport factice : renvoie les statuts prévus et note chaque requête."""

    def __init__(self, statuses, headers=None):
        self.statuses = list(statuses)
        self.headers = headers or {}
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request):
        self.requests.append(request)
        return httpx.Response(self.statuses.pop(0), headers=self.headers)


class Sleeps:
    def __init__(self):
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def client(inner, limiter=None, sleep=None, retries=2):
    transport = PoliteTransport(
        inner, limiter or RateLimiter(default_delay=0.0), retries, sleep or Sleeps()
    )
    return httpx.AsyncClient(transport=transport)


async def test_a_429_is_retried_after_retry_after():
    inner = Recorder([429, 200], headers={"Retry-After": "3"})
    sleeps = Sleeps()
    async with client(inner, sleep=sleeps) as c:
        response = await c.get("https://api.example.com/items")
    assert response.status_code == 200
    assert len(inner.requests) == 2
    assert sleeps.calls == [3.0]


async def test_without_retry_after_the_wait_grows():
    inner = Recorder([429, 429, 200])
    sleeps = Sleeps()
    async with client(inner, sleep=sleeps) as c:
        response = await c.get("https://api.example.com/items")
    assert response.status_code == 200
    assert sleeps.calls == [2, 4]


async def test_gives_up_after_the_last_retry():
    inner = Recorder([429, 429, 429])
    async with client(inner, retries=2) as c:
        response = await c.get("https://api.example.com/items")
    assert response.status_code == 429
    assert len(inner.requests) == 3


async def test_a_long_retry_after_is_capped():
    inner = Recorder([429, 200], headers={"Retry-After": "3600"})
    sleeps = Sleeps()
    async with client(inner, sleep=sleeps) as c:
        await c.get("https://api.example.com/items")
    assert sleeps.calls == [10.0]


async def test_other_errors_are_returned_at_once():
    inner = Recorder([503])
    async with client(inner) as c:
        response = await c.get("https://api.example.com/items")
    assert response.status_code == 503
    assert len(inner.requests) == 1


async def test_concurrent_requests_to_one_domain_are_spaced():
    import asyncio

    limiter = RateLimiter(default_delay=0.05)
    start = time.monotonic()
    await asyncio.gather(*(limiter.wait("example.com") for _ in range(3)))
    assert time.monotonic() - start >= 0.09  # 0, 0.05 puis 0.10 s


async def test_domains_are_limited_separately():
    limiter = RateLimiter(default_delay=5.0)
    start = time.monotonic()
    await limiter.wait("a.example.com")
    await limiter.wait("b.example.com")
    assert time.monotonic() - start < 1


async def test_the_novit_user_agent_is_sent(monkeypatch):
    monkeypatch.setenv("NOVIT_USER_AGENT", "NovIT-test/1.0")
    from novit.settings import reload_settings

    reload_settings()
    try:
        async with http_client(timeout=5) as c:
            assert c.headers["User-Agent"] == "NovIT-test/1.0"
            assert c.follow_redirects is True
    finally:
        monkeypatch.undo()
        reload_settings()  # ne pas laisser l'agent de test aux autres tests


@pytest.mark.parametrize(
    "value, expected", [("3", 3.0), ("0", 0.0), ("Wed, 21 Oct 2015", None), ("", None)]
)
def test_retry_after(value, expected):
    response = httpx.Response(429, headers={"Retry-After": value} if value else {})
    assert retry_after(response) == expected
