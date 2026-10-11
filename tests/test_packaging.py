"""Paquet PyPI : configuration embarquée, version et dépendances déclarées."""

import re
import tomllib
from importlib.metadata import PackageNotFoundError
from pathlib import Path

from novit import settings
from novit.mcp import health

ROOT = Path(__file__).resolve().parent.parent


def _write(path: Path, text: str = "x: 1\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_config_file_prefers_the_local_config_directory(monkeypatch, tmp_path):
    local = _write(tmp_path / "config" / "sources.yaml")
    _write(tmp_path / "packaged" / "sources.yaml")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "_PACKAGED_CONFIG_DIR", tmp_path / "packaged")

    assert settings.config_file("sources.yaml").resolve() == local


def test_config_file_falls_back_to_the_packaged_copy(monkeypatch, tmp_path):
    packaged = _write(tmp_path / "packaged" / "domains.yaml")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "_PACKAGED_CONFIG_DIR", tmp_path / "packaged")

    assert settings.config_file("domains.yaml") == packaged


def test_config_file_names_the_local_path_when_nothing_exists(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "_PACKAGED_CONFIG_DIR", tmp_path / "packaged")

    assert settings.config_file("profiles.yaml") == Path("config/profiles.yaml")


def test_version_falls_back_to_the_installed_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # pas de fichier VERSION ici
    monkeypatch.setattr(health, "package_version", lambda name: "1.2.3")

    assert health._read_version() == "1.2.3"


def test_version_is_unknown_without_file_nor_package(monkeypatch, tmp_path):
    def missing(name):
        raise PackageNotFoundError(name)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(health, "package_version", missing)

    assert health._read_version() == "unknown"


def _requirement_names(lines: list[str]) -> dict[str, str]:
    requirements = {}
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if line:
            name = re.split(r"[\[<>=!~ ]", line, maxsplit=1)[0].lower()
            requirements[name] = line.replace(" ", "")
    return requirements


def test_pyproject_dependencies_match_requirements_txt():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    requirements = (ROOT / "requirements.txt").read_text().splitlines()

    assert _requirement_names(project["dependencies"]) == _requirement_names(
        requirements
    )


def test_wheel_embeds_every_yaml_of_the_config_directory():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    wheel = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]
    embedded = wheel["force-include"]

    for path in sorted((ROOT / "config").glob("*.yaml")):
        assert embedded[f"config/{path.name}"] == f"novit/data/{path.name}"
