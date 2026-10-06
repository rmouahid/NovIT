import time
from dataclasses import dataclass, field
from datetime import datetime

from src.mcp.cache import cache
from src.mcp.monitoring import SourceMonitor

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


# Monitoring des sources (#69), créé au premier rapport
_monitor: SourceMonitor | None = None


def _get_monitor() -> SourceMonitor:
    """Monitoring branché sur le ScraperManager des outils, pour vérifier les
    sources réellement utilisées (y compris celles de config/sources.yaml)."""
    global _monitor
    if _monitor is None:
        from src.mcp.handlers import _manager

        _monitor = SourceMonitor(manager=_manager)
    return _monitor


async def get_health() -> HealthReport:
    """Rapport de santé global du serveur NovIT."""
    sources = await get_sources_health()

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
    """Statut de chaque source de scraping, vérifiée à l'instant par le
    monitoring ; une source en échec indique depuis quand et combien de fois."""
    report = await _get_monitor().check_all()
    statuses = []
    for src in sorted(report.sources, key=lambda s: s.name):
        error = ""
        if not src.available:
            error = (
                f"indisponible depuis {src.downtime_minutes:.0f} min "
                f"({src.consecutive_failures} échec(s) consécutif(s))"
            )
        statuses.append(
            SourceStatus(
                name=src.name,
                available=src.available,
                last_check=datetime.fromisoformat(src.last_check).timestamp(),
                last_error=error,
            )
        )
    return statuses


async def get_cache_health() -> dict:
    """Métriques du cache."""
    return cache.stats()
