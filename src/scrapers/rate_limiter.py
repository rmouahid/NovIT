import asyncio
import time
from collections import defaultdict

from loguru import logger


class RateLimiter:
    """Rate limiter par domaine avec backoff exponentiel.

    Respecte un délai minimum entre deux requêtes vers le même domaine.
    En cas d'erreur 429, applique un backoff exponentiel.
    """

    def __init__(self, default_delay: float = 1.0):
        self.default_delay = default_delay
        self._last_request: dict[str, float] = defaultdict(float)
        self._backoff_count: dict[str, int] = defaultdict(int)
        self._delays: dict[str, float] = {}

    def set_delay(self, domain: str, delay: float) -> None:
        """Configure un délai spécifique pour un domaine."""
        self._delays[domain] = delay

    async def wait(self, domain: str) -> None:
        """Attend le délai requis avant d'autoriser une requête vers le domaine."""
        delay = self._delays.get(domain, self.default_delay)
        elapsed = time.monotonic() - self._last_request[domain]
        remaining = delay - elapsed
        if remaining > 0:
            logger.debug(f"[rate_limiter] Attente {remaining:.2f}s pour {domain}")
            await asyncio.sleep(remaining)
        self._last_request[domain] = time.monotonic()

    def on_rate_limited(self, domain: str) -> float:
        """Appelé quand une erreur 429 est reçue. Retourne le délai de backoff."""
        self._backoff_count[domain] += 1
        backoff = min(2 ** self._backoff_count[domain], 300)
        logger.warning(f"[rate_limiter] 429 sur {domain} — backoff {backoff}s (tentative #{self._backoff_count[domain]})")
        return backoff

    def on_success(self, domain: str) -> None:
        """Réinitialise le compteur de backoff après un succès."""
        self._backoff_count[domain] = 0


# Instance globale partagée
rate_limiter = RateLimiter(default_delay=1.0)

# Délais spécifiques par source (respectant les politiques robots.txt)
rate_limiter.set_delay("hacker-news.firebaseio.com", 0.2)   # API officielle, tolérant
rate_limiter.set_delay("github.com", 2.0)                   # Scraping HTML, prudent
rate_limiter.set_delay("services.nvd.nist.gov", 6.0)        # NVD sans clé API = 1 req/6s
rate_limiter.set_delay("export.arxiv.org", 3.0)             # arXiv recommande 3s min
rate_limiter.set_delay("api.github.com", 0.5)               # GitHub API avec token = 5000 req/h
