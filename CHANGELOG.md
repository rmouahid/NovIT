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
- Transport HTTP pour le déploiement distant : `novit --transport http` (ou `NOVIT_TRANSPORT=http`) sert le serveur MCP en Streamable HTTP sur `/mcp`, protégé par le jeton bearer `NOVIT_API_TOKEN`, avec une sonde publique `/health` (`?sources=1` pour l'état des sources). stdio reste le défaut ([ADR-005](docs/ADR/0005-transport-http-authentification.md)) (#100)
- Mode hors-ligne dégradé : quand aucune source ne répond, `novit_get_news` et `novit_get_by_domain` servent les articles encore en base (fenêtre de rétention) avec un bandeau qui indique la date et l'âge de la dernière collecte réussie ; la collecte est relancée en arrière-plan (30 s, 2 min, 5 min) et la réponse dégradée n'est gardée en cache qu'une minute ([guide des erreurs](docs/ERROR_HANDLING_GUIDE.md)) (#91)
- Multi-utilisateurs en HTTP : `NOVIT_API_TOKENS` donne un jeton à chaque utilisateur ; profil, domaines favoris et historique de session sont rangés par utilisateur et ne fuient pas de l'un à l'autre (ADR-006, #87)
- Support après release : `.github/SUPPORT.md` (canaux, délais de première réponse, triage hebdomadaire avec le label `a-trier` posé par les modèles d'issue), `SECURITY.md` (signalement privé de vulnérabilités, délais), roadmap v1.0 / v1.1 à jour, `novit --version` (#97)
- Outil `novit_feedback` : enregistre un retour (bug, suggestion, avis positif ou négatif) avec l'outil et la requête concernés, le profil, les domaines favoris et la version, dans la table `feedback` de la base locale ; un bug renvoie un lien vers une issue GitHub pré-remplie. Rapport hebdomadaire : `scripts/feedback_report.py` (#89)

### Performance
- Collecte complète des 22 sources en ~2 s au lieu de 6 à 9 s : les flux RSS sont téléchargés en asynchrone (httpx) et analysés hors de la boucle d'événements au lieu de `feedparser.parse(url)`, bloquant ; les items Hacker News sont récupérés 10 par 10. Une source RSS en erreur HTTP est désormais comptée en échec au lieu de « 0 article ». Mesure : `scripts/profile_scrapers.py` ([docs/PERFORMANCE.md](docs/PERFORMANCE.md)) (#90)

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
