import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.mcp.monitoring import MonitoringReport, SourceMonitor, SourceStatus


@pytest.fixture
def mock_manager():
    manager = MagicMock()
    manager.health_check_all = AsyncMock(
        return_value={
            "hacker_news": True,
            "github_trending": False,
            "anssi_cert": True,
        }
    )
    return manager


@pytest.fixture
def monitor(mock_manager, tmp_path):
    return SourceMonitor(
        manager=mock_manager,
        alert_threshold_hours=2,
        report_path=tmp_path / "monitoring.json",
    )


async def test_check_all_counts_up_down(monitor):
    report = await monitor.check_all()
    assert report.sources_up == 2
    assert report.sources_down == 1


async def test_check_all_identifies_down_source(monitor):
    report = await monitor.check_all()
    down = [s.name for s in report.sources if not s.available]
    assert "github_trending" in down


async def test_check_all_saves_report_file(monitor, tmp_path):
    await monitor.check_all()
    report_file = tmp_path / "monitoring.json"
    assert report_file.exists()
    data = json.loads(report_file.read_text())
    assert "checked_at" in data
    assert data["sources_down"] == 1


async def test_down_sources_tracked(monitor):
    await monitor.check_all()
    assert "github_trending" in monitor.down_sources()


async def test_recovery_clears_down_source(monitor, mock_manager):
    await monitor.check_all()
    assert "github_trending" in monitor.down_sources()

    mock_manager.health_check_all = AsyncMock(
        return_value={
            "hacker_news": True,
            "github_trending": True,
            "anssi_cert": True,
        }
    )
    await monitor.check_all()
    assert "github_trending" not in monitor.down_sources()


async def test_consecutive_failures_tracked(monitor):
    await monitor.check_all()
    await monitor.check_all()
    report = await monitor.check_all()
    down = next(s for s in report.sources if s.name == "github_trending")
    assert down.consecutive_failures == 3


async def test_downtime_minutes_increases(monitor, tmp_path):
    monitor._down_since["github_trending"] = datetime.now(tz=UTC) - timedelta(
        minutes=15
    )
    report = await monitor.check_all()
    down = next(s for s in report.sources if s.name == "github_trending")
    assert down.downtime_minutes >= 15


class TestMonitoringReport:
    def test_sources_up_count(self):
        report = MonitoringReport(
            checked_at="2026-01-01T00:00:00",
            sources=[
                SourceStatus("a", True, "now"),
                SourceStatus("b", False, "now"),
                SourceStatus("c", True, "now"),
            ],
        )
        assert report.sources_up == 2
        assert report.sources_down == 1

    def test_to_dict(self):
        report = MonitoringReport(
            checked_at="2026-01-01T00:00:00",
            sources=[SourceStatus("a", True, "now")],
        )
        d = report.to_dict()
        assert d["sources_up"] == 1
        assert d["sources_down"] == 0
        assert len(d["sources"]) == 1
