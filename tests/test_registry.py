import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_registry_release_matches_package_and_ownership_marker():
    manifest = json.loads((ROOT / "server.json").read_text())
    version = (ROOT / "VERSION").read_text().strip()
    assert manifest["version"] == version
    assert manifest["name"] == "io.github.rmouahid/novit"
    assert len(manifest["description"]) <= 100
    assert f'<!-- mcp-name: {manifest["name"]} -->' in (ROOT / "README.md").read_text()
    assert manifest["packages"] == [
        {
            "registryType": "pypi",
            "identifier": "novit",
            "version": version,
            "transport": {"type": "stdio"},
        }
    ]
