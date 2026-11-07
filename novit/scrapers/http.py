"""Client HTTP commun à toutes les sources : politesse et relances.

Chaque requête passe par `PoliteTransport` :

- avant l'envoi, le limiteur impose le délai minimal du domaine
  (`rate_limiter`, réglé par source dans `rate_limiter.py`) ;
- sur une réponse 429, il attend `Retry-After` s'il est donné, sinon une
  durée croissante (2 s, 4 s…), puis réessaie, au plus `RETRIES` fois ;
- l'agent envoyé est `NOVIT_USER_AGENT`, pour que les sites sachent qui
  les interroge.

Les scrapers créent leur client avec `http_client()` au lieu de
`httpx.AsyncClient()`.
"""

import asyncio
from collections.abc import Awaitable, Callable

import httpx
from loguru import logger

from novit.scrapers.rate_limiter import RateLimiter, rate_limiter
from novit.settings import get_settings

RETRIES = 2
MAX_WAIT = 10.0  # au-delà, la source dépasserait le timeout de collecte (30 s)


def retry_after(response: httpx.Response) -> float | None:
    """Délai demandé par l'en-tête `Retry-After` (en secondes), s'il est lisible."""
    value = response.headers.get("retry-after", "").strip()
    try:
        return max(float(value), 0.0)
    except ValueError:
        return None


class PoliteTransport(httpx.AsyncBaseTransport):
    """Transport httpx qui espace les requêtes par domaine et relance sur 429."""

    def __init__(
        self,
        inner: httpx.AsyncBaseTransport | None = None,
        limiter: RateLimiter = rate_limiter,
        retries: int = RETRIES,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        self._inner = inner or httpx.AsyncHTTPTransport()
        self._limiter = limiter
        self._retries = retries
        self._sleep = sleep

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host
        for attempt in range(self._retries + 1):
            await self._limiter.wait(host)
            response = await self._inner.handle_async_request(request)
            if response.status_code != 429:
                self._limiter.on_success(host)
                return response
            if attempt == self._retries:
                return response
            delay = retry_after(response)
            if delay is None:
                delay = self._limiter.on_rate_limited(host)
            delay = min(delay, MAX_WAIT)
            logger.warning(f"[http] 429 sur {host}, nouvel essai dans {delay:.0f} s")
            await response.aclose()
            await self._sleep(delay)
        raise AssertionError("inatteignable")  # pragma: no cover

    async def aclose(self) -> None:
        await self._inner.aclose()


def http_client(timeout: float, **kwargs) -> httpx.AsyncClient:
    """Client httpx des sources : redirections suivies, agent NovIT, transport poli."""
    headers = {"User-Agent": get_settings().user_agent, **kwargs.pop("headers", {})}
    kwargs.setdefault("follow_redirects", True)
    return httpx.AsyncClient(
        timeout=timeout, headers=headers, transport=PoliteTransport(), **kwargs
    )
