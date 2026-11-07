import time
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    """Cache en mémoire avec expiration par entrée."""

    def __init__(self, default_ttl: int = 3600):
        self._store: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None or time.monotonic() > entry.expires_at:
                if entry:
                    del self._store[key]
                self.misses += 1
                return None
            self.hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            self._store[key] = CacheEntry(
                value=value,
                expires_at=time.monotonic() + ttl,
            )

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> dict:
        with self._lock:
            total = self.hits + self.misses
            return {
                "entries": len(self._store),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(self.hits / total, 3) if total else 0.0,
            }


# TTL par type de contenu (secondes)
TTL_NEWS = 3600  # 1h — actualités
TTL_PROFILE = 86400  # 24h — profils utilisateur
TTL_SEARCH = 1800  # 30min — résultats de recherche
TTL_HEALTH = 60  # 1min — statut des sources

# Instance globale partagée entre les handlers
cache = TTLCache(default_ttl=TTL_NEWS)
