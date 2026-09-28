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

### Fixed
- CI rétablie : `mcp` borné à la série 1.x (la 2.x retire `Server.list_tools()`)

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
