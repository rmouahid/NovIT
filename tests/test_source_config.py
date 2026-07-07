from pathlib import Path

import pytest

from src.scrapers.ai_blogs import build_ai_scrapers
from src.scrapers.eng_blogs import build_eng_scrapers
from src.scrapers.manager import ScraperManager
from src.scrapers.regulation import build_regulation_scrapers
from src.scrapers.rss import (
    SourcesConfigError,
    build_rss_scrapers,
    load_rss_sources,
)
from src.scrapers.training import build_training_scrapers


def write_yaml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sources.yaml"
    path.write_text(content, encoding="utf-8")
    return path


class TestLoadRssSources:
    def test_loads_real_config(self):
        sources = load_rss_sources()
        assert len(sources) == 16
        names = {s.name for s in sources}
        assert "dev_to" in names
        assert "anthropic_blog" in names

    def test_filters_by_category(self):
        sources = load_rss_sources(category="ia")
        assert {s.name for s in sources} == {
            "anthropic_blog",
            "openai_blog",
            "deepmind_blog",
            "papers_with_code",
        }

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(SourcesConfigError, match="introuvable"):
            load_rss_sources(path=tmp_path / "does_not_exist.yaml")

    def test_missing_required_field_raises(self, tmp_path):
        path = write_yaml(
            tmp_path,
            """
            sources:
              - name: bad_source
                url: "https://example.com/feed"
                # domains manquant
                profiles: [ETUDIANT]
            """,
        )
        with pytest.raises(SourcesConfigError, match="champs manquants"):
            load_rss_sources(path=path)

    def test_duplicate_name_raises(self, tmp_path):
        path = write_yaml(
            tmp_path,
            """
            sources:
              - name: dup
                url: "https://a.example.com/feed"
                domains: [dev]
                profiles: [ETUDIANT]
              - name: dup
                url: "https://b.example.com/feed"
                domains: [dev]
                profiles: [ETUDIANT]
            """,
        )
        with pytest.raises(SourcesConfigError, match="dupliqué"):
            load_rss_sources(path=path)

    def test_base_score_defaults_to_half(self, tmp_path):
        path = write_yaml(
            tmp_path,
            """
            sources:
              - name: no_score
                url: "https://example.com/feed"
                domains: [dev]
                profiles: [ETUDIANT]
            """,
        )
        sources = load_rss_sources(path=path)
        assert sources[0].base_score == 0.5

    def test_empty_file_returns_empty_list(self, tmp_path):
        path = write_yaml(tmp_path, "sources: []\n")
        assert load_rss_sources(path=path) == []


class TestCategoryBuilders:
    def test_build_rss_scrapers_matches_actualites_category(self):
        names = {s.name for s in build_rss_scrapers()}
        assert names == {"dev_to", "techcrunch", "the_verge", "mit_tech_review"}

    def test_build_eng_scrapers(self):
        names = {s.name for s in build_eng_scrapers()}
        assert names == {"netflix_tech", "google_eng", "meta_eng", "the_new_stack"}

    def test_build_regulation_scrapers(self):
        names = {s.name for s in build_regulation_scrapers()}
        assert names == {"cnil", "eurlex_ai", "w3c_news"}

    def test_build_training_scrapers_includes_roadmap(self):
        names = {s.name for s in build_training_scrapers()}
        assert "freecodecamp" in names
        assert "roadmap_sh" in names  # scraper code, pas déclaratif

    def test_build_ai_scrapers_includes_arxiv(self):
        names = {s.name for s in build_ai_scrapers()}
        assert "anthropic_blog" in names
        assert "arxiv" in names  # scraper code, pas déclaratif


class TestScraperManagerReload:
    def test_reload_sources_picks_up_new_entry(self, tmp_path, monkeypatch):
        config_path = write_yaml(
            tmp_path,
            """
            sources:
              - name: source_v1
                category: actualites
                url: "https://example.com/feed"
                domains: [dev]
                profiles: [ETUDIANT]
            """,
        )
        monkeypatch.setattr("src.scrapers.rss.SOURCES_CONFIG_PATH", config_path)

        manager = ScraperManager()
        assert "source_v1" in {s.name for s in manager._scrapers}

        config_path.write_text(
            """
            sources:
              - name: source_v1
                category: actualites
                url: "https://example.com/feed"
                domains: [dev]
                profiles: [ETUDIANT]
              - name: source_v2
                category: actualites
                url: "https://example.com/feed2"
                domains: [dev]
                profiles: [ETUDIANT]
            """,
            encoding="utf-8",
        )
        total = manager.reload_sources()

        names = {s.name for s in manager._scrapers}
        assert "source_v2" in names
        assert total == len(manager._scrapers)

    def test_reload_keeps_previous_scrapers_on_invalid_config(
        self, tmp_path, monkeypatch
    ):
        config_path = write_yaml(
            tmp_path,
            """
            sources:
              - name: source_ok
                category: actualites
                url: "https://example.com/feed"
                domains: [dev]
                profiles: [ETUDIANT]
            """,
        )
        monkeypatch.setattr("src.scrapers.rss.SOURCES_CONFIG_PATH", config_path)
        manager = ScraperManager()
        before = {s.name for s in manager._scrapers}

        config_path.write_text("sources:\n  - name: broken\n", encoding="utf-8")

        with pytest.raises(SourcesConfigError):
            manager.reload_sources()

        assert {s.name for s in manager._scrapers} == before
