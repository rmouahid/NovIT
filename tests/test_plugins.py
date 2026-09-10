import shutil
from pathlib import Path

import httpx
import respx

from src.scrapers.base import BaseScraper
from src.scrapers.manager import ScraperManager
from src.scrapers.plugins import discover_plugin_scrapers

VALID_PLUGIN = """
from src.scrapers.base import Article, BaseScraper


class DummyPluginScraper(BaseScraper):
    name = "dummy_plugin"
    domains = ["dev"]
    profiles = ["ETUDIANT"]

    async def fetch(self):
        return []

    async def health_check(self):
        return True
"""

BROKEN_IMPORT_PLUGIN = "import ceci_n_existe_pas\n"

MULTI_CLASS_PLUGIN = """
from src.scrapers.base import BaseScraper


class FirstScraper(BaseScraper):
    name = "first"

    async def fetch(self):
        return []

    async def health_check(self):
        return True


class SecondScraper(BaseScraper):
    name = "second"

    async def fetch(self):
        return []

    async def health_check(self):
        return True
"""

REQUIRES_ARGS_PLUGIN = """
from src.scrapers.base import BaseScraper


class NeedsArgScraper(BaseScraper):
    name = "needs_arg"

    def __init__(self, required):
        self.required = required

    async def fetch(self):
        return []

    async def health_check(self):
        return True
"""


class TestDiscoverPluginScrapers:
    def test_missing_directory_returns_empty(self, tmp_path):
        assert discover_plugin_scrapers(tmp_path / "does_not_exist") == []

    def test_empty_directory_returns_empty(self, tmp_path):
        assert discover_plugin_scrapers(tmp_path) == []

    def test_loads_valid_plugin(self, tmp_path):
        (tmp_path / "dummy.py").write_text(VALID_PLUGIN, encoding="utf-8")
        scrapers = discover_plugin_scrapers(tmp_path)
        assert len(scrapers) == 1
        assert isinstance(scrapers[0], BaseScraper)
        assert scrapers[0].name == "dummy_plugin"

    def test_skips_files_starting_with_underscore(self, tmp_path):
        (tmp_path / "_disabled.py").write_text(VALID_PLUGIN, encoding="utf-8")
        assert discover_plugin_scrapers(tmp_path) == []

    def test_broken_plugin_does_not_crash_discovery(self, tmp_path):
        (tmp_path / "broken.py").write_text(BROKEN_IMPORT_PLUGIN, encoding="utf-8")
        (tmp_path / "dummy.py").write_text(VALID_PLUGIN, encoding="utf-8")

        scrapers = discover_plugin_scrapers(tmp_path)

        assert len(scrapers) == 1
        assert scrapers[0].name == "dummy_plugin"

    def test_multiple_classes_in_one_file_all_loaded(self, tmp_path):
        (tmp_path / "multi.py").write_text(MULTI_CLASS_PLUGIN, encoding="utf-8")
        names = {s.name for s in discover_plugin_scrapers(tmp_path)}
        assert names == {"first", "second"}

    def test_instantiation_failure_is_isolated(self, tmp_path):
        (tmp_path / "needs_arg.py").write_text(REQUIRES_ARGS_PLUGIN, encoding="utf-8")
        (tmp_path / "dummy.py").write_text(VALID_PLUGIN, encoding="utf-8")

        scrapers = discover_plugin_scrapers(tmp_path)

        assert len(scrapers) == 1
        assert scrapers[0].name == "dummy_plugin"


class TestScraperManagerPluginIntegration:
    def test_reload_sources_picks_up_new_plugin(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.scrapers.manager.get_settings",
            lambda: type("S", (), {"plugins_dir": str(tmp_path)})(),
        )
        manager = ScraperManager()
        before_names = {s.name for s in manager._scrapers}
        assert "dummy_plugin" not in before_names

        (tmp_path / "dummy.py").write_text(VALID_PLUGIN, encoding="utf-8")
        manager.reload_sources()

        assert "dummy_plugin" in {s.name for s in manager._scrapers}


class TestExamplePlugin:
    """Vérifie que l'exemple fourni dans examples/plugins/ est un plugin valide et fonctionnel."""

    def test_example_plugin_is_discovered(self, tmp_path):
        example = Path("examples/plugins/example_scraper.py")
        shutil.copy(example, tmp_path / "example_scraper.py")

        scrapers = discover_plugin_scrapers(tmp_path)

        assert len(scrapers) == 1
        assert scrapers[0].name == "lobsters"

    async def test_example_plugin_fetch_works(self, tmp_path):
        example = Path("examples/plugins/example_scraper.py")
        shutil.copy(example, tmp_path / "example_scraper.py")
        scraper = discover_plugin_scrapers(tmp_path)[0]

        with respx.mock:
            respx.get("https://lobste.rs/hottest.json").mock(
                return_value=httpx.Response(
                    200,
                    json=[
                        {
                            "title": "A great article",
                            "url": "https://example.com/article",
                            "created_at": "2026-01-01T12:00:00.000+00:00",
                            "score": 42,
                            "comment_count": 5,
                            "tags": ["programming"],
                        }
                    ],
                )
            )
            articles = await scraper.fetch()

        assert len(articles) == 1
        assert articles[0].title == "A great article"
        assert articles[0].source == "lobsters"
