from unittest.mock import AsyncMock, MagicMock

import pytest

from src.mcp import health
from src.mcp.monitoring import SourceMonitor


@pytest.fixture
def sources(monkeypatch, tmp_path):
    """Branche le rapport de santé sur un monitoring dont les sources sont simulées."""
    manager = MagicMock()
    manager.health_check_all = AsyncMock(
        return_value={"cve_nvd": True, "eurlex_ai": False, "anssi_cert": True}
    )
    monitor = SourceMonitor(manager=manager, report_path=tmp_path / "monitoring.json")
    monkeypatch.setattr(health, "_monitor", monitor)
    return manager


async def test_the_sources_section_lists_every_source(sources):
    text = (await health.get_health()).to_text()

    sources_section = text.split("## Sources", 1)[1]
    assert "✅ **anssi_cert**" in sources_section
    assert "✅ **cve_nvd**" in sources_section
    assert "❌ **eurlex_ai**" in sources_section


async def test_a_failing_source_degrades_the_status_and_says_since_when(sources):
    report = await health.get_health()

    assert report.status == "degraded"
    eurlex = next(s for s in report.sources if s.name == "eurlex_ai")
    assert not eurlex.available
    assert "1 échec" in eurlex.last_error


async def test_all_sources_down_is_reported_as_down(sources):
    sources.health_check_all.return_value = {"cve_nvd": False, "anssi_cert": False}

    assert (await health.get_health()).status == "down"


async def test_sources_detail_is_sorted_by_name(sources):
    names = [s.name for s in await health.get_sources_health()]

    assert names == ["anssi_cert", "cve_nvd", "eurlex_ai"]


def test_the_default_monitor_watches_the_scrapers_used_by_the_tools(monkeypatch):
    from src.mcp import handlers

    monkeypatch.setattr(health, "_monitor", None)

    assert health._get_monitor()._manager is handlers._manager
