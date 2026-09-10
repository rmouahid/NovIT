import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from loguru import logger


@dataclass
class SourceStatus:
    name: str
    available: bool
    last_check: str
    downtime_minutes: float = 0.0
    consecutive_failures: int = 0


@dataclass
class MonitoringReport:
    checked_at: str
    sources: list[SourceStatus]

    @property
    def sources_up(self) -> int:
        return sum(1 for s in self.sources if s.available)

    @property
    def sources_down(self) -> int:
        return sum(1 for s in self.sources if not s.available)

    def to_dict(self) -> dict:
        return {
            "checked_at": self.checked_at,
            "sources_up": self.sources_up,
            "sources_down": self.sources_down,
            "sources": [asdict(s) for s in self.sources],
        }


class SourceMonitor:
    """Surveille la disponibilité des sources NovIT.

    Maintient un historique et émet une alerte si une source est down
    depuis plus de alert_threshold_hours.
    """

    def __init__(
        self,
        manager=None,
        alert_threshold_hours: int = 2,
        report_path: Path = Path("./monitoring.json"),
    ):
        self._manager = manager
        self.alert_threshold = timedelta(hours=alert_threshold_hours)
        self.report_path = report_path
        self._down_since: dict[str, datetime] = {}
        self._consecutive_failures: dict[str, int] = {}

    async def check_all(self) -> MonitoringReport:
        if self._manager is None:
            from src.scrapers.manager import ScraperManager

            self._manager = ScraperManager()

        results: dict[str, bool] = await self._manager.health_check_all()
        now = datetime.now(tz=UTC)
        statuses: list[SourceStatus] = []

        for source, available in results.items():
            if available:
                if source in self._down_since:
                    downtime = (now - self._down_since.pop(source)).total_seconds() / 60
                    logger.info(
                        f"[monitoring] {source} de nouveau disponible (downtime : {downtime:.0f}min)"
                    )
                self._consecutive_failures.pop(source, None)
                statuses.append(
                    SourceStatus(
                        name=source, available=True, last_check=now.isoformat()
                    )
                )
            else:
                self._consecutive_failures[source] = (
                    self._consecutive_failures.get(source, 0) + 1
                )
                if source not in self._down_since:
                    self._down_since[source] = now
                    logger.warning(f"[monitoring] {source} indisponible")

                downtime = (now - self._down_since[source]).total_seconds() / 60
                if now - self._down_since[source] >= self.alert_threshold:
                    logger.error(
                        f"[monitoring] ALERTE : {source} down depuis {downtime:.0f}min"
                    )

                statuses.append(
                    SourceStatus(
                        name=source,
                        available=False,
                        last_check=now.isoformat(),
                        downtime_minutes=round(downtime, 1),
                        consecutive_failures=self._consecutive_failures[source],
                    )
                )

        report = MonitoringReport(checked_at=now.isoformat(), sources=statuses)
        self._save_report(report)
        return report

    def _save_report(self, report: MonitoringReport) -> None:
        try:
            self.report_path.write_text(
                json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning(f"[monitoring] Impossible d'écrire le rapport : {e}")

    def down_sources(self) -> list[str]:
        return list(self._down_since.keys())
