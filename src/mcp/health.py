import time
from dataclasses import dataclass, field

from src.mcp.cache import cache

# Timestamp de démarrage du serveur
_START_TIME = time.time()


@dataclass
class SourceStatus:
    name: str
    available: bool
    last_check: float
    last_error: str = ""


@dataclass
class HealthReport:
    status: str  # "ok" | "degraded" | "down"
    uptime_seconds: float
    version: str
    sources: list[SourceStatus] = field(default_factory=list)
    cache_stats: dict = field(default_factory=dict)

    def to_text(self) -> str:
        icon = {"ok": "✅", "degraded": "⚠️", "down": "❌"}.get(self.status, "❓")
        lines = [
            f"# Health NovIT {icon}",
            f"**Statut :** {self.status}",
            f"**Uptime :** {int(self.uptime_seconds // 3600)}h {int((self.uptime_seconds % 3600) // 60)}m",
            f"**Version :** {self.version}",
            "",
            "## Cache",
            f"- Entrées : {self.cache_stats.get('entries', 0)}",
            f"- Taux de hit : {self.cache_stats.get('hit_rate', 0):.1%}",
            f"- Hits : {self.cache_stats.get('hits', 0)} / Misses : {self.cache_stats.get('misses', 0)}",
            "",
            "## Sources",
        ]
        for src in self.sources:
            status_icon = "✅" if src.available else "❌"
            lines.append(
                f"- {status_icon} **{src.name}**"
                + (f" — {src.last_error}" if src.last_error else "")
            )
        return "\n".join(lines)


def _read_version() -> str:
    try:
        with open("VERSION") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


async def get_health() -> HealthReport:
    """Rapport de santé global du serveur NovIT."""
    # Les scrapers rempliront cette liste en M2
    sources: list[SourceStatus] = []

    all_up = all(s.available for s in sources) if sources else True
    any_up = any(s.available for s in sources) if sources else True

    if all_up:
        status = "ok"
    elif any_up:
        status = "degraded"
    else:
        status = "down"

    return HealthReport(
        status=status,
        uptime_seconds=time.time() - _START_TIME,
        version=_read_version(),
        sources=sources,
        cache_stats=cache.stats(),
    )


async def get_sources_health() -> list[SourceStatus]:
    """Statut détaillé de chaque source de scraping."""
    # Rempli en M2 par le ScraperManager
    return []


async def get_cache_health() -> dict:
    """Métriques du cache."""
    return cache.stats()
