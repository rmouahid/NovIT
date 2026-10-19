# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
projet adhérant au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [Unreleased]

### Added
- Structure initiale du projet (dossiers, packages Python)
- `requirements.txt` et `requirements-dev.txt`
- `.env.example` avec toutes les variables documentées
- Pre-commit hooks : black, ruff, isort, detect-secrets
- `pyproject.toml` pour la configuration des outils
- `CHANGELOG.md` et `VERSION` (0.1.0)
- `scripts/demo.py` : session de démonstration sur les sources en direct, sans client MCP graphique
- Landing page du projet dans le README : logo, démo animée, captures de réponses réelles, badges et appels à l'action
- Paquet Python `novit` (`pyproject.toml`, build hatchling, version lue dans `VERSION`) : commande `novit`, configuration YAML par défaut embarquée et utilisée quand `./config/` est absent ; job CI qui construit, vérifie (`twine check`) et installe la wheel hors du dépôt ; workflow de publication TestPyPI puis PyPI sur tag `vX.Y.Z` par trusted publishing ([docs/PUBLISHING.md](docs/PUBLISHING.md)) (#93)

### Fixed
- `novit_search` cherche des mots entiers (index SQLite FTS5) au lieu de sous-chaînes : « rust » ne renvoie plus « trust » ; résultats classés par pertinence (#104)
- CI rétablie : `mcp` borné à la série 1.x (la 2.x retire `Server.list_tools()`)

### Changed
- Serveur migré vers l'API du SDK `mcp` 2.x (handlers `on_list_tools` / `on_call_tool` passés au constructeur de `Server`) ; dépendance relevée à `mcp>=2.3.0,<3`. Les erreurs d'outil sont signalées avec `isError` (#112)
- **Rupture** : le package `src` devient `novit` et `config.settings` devient `novit.settings`. Lancement : `python -m novit.mcp` (mettre à jour la configuration du client MCP). Préalable à la publication sur PyPI, où `src` et `config` entreraient en conflit avec d'autres paquets (#93)

---

## [0.1.0] — 2026-06-26

### Added
- Initialisation du dépôt GitHub NovIT (privé)
- README initial et LICENSE MIT
- `.gitignore` Python complet
- Branches `main` et `dev`
- 98 issues et 10 milestones créés sur GitHub

[Unreleased]: https://github.com/rmouahid/NovIT/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rmouahid/NovIT/releases/tag/v0.1.0
