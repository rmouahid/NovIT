# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
projet adhérant au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [Unreleased]

### Added
- Contenu structuré : `novit_get_news`, `novit_search` et `novit_get_by_domain` déclarent un schéma de sortie et renvoient les articles en `structuredContent`, avec un indicateur `offline` ([formats de réponse](docs/RESPONSE_FORMATS.md))
- Annotations MCP sur chaque outil (`readOnlyHint`, `openWorldHint`)
- Tests de bout en bout avec le client MCP du SDK sur le transport stdio, serveur lancé en sous-processus comme par un client de bureau
- Exemples de configuration pour Claude Desktop : `examples/claude_desktop_config.json` (paquet installé) et `examples/claude_desktop_config.source.json` (depuis un clone)

### Fixed
- arXiv et roadmap.sh répondaient 301 (passage en HTTPS, dépôt GitHub renommé) : URL à jour et redirections suivies ; leur `health_check` exige désormais une réponse sous 400 au lieu de 500, comme la collecte (#118)
- Le tagger détecte les mots-clés en mots entiers : « norme » ne tague plus « énorme » ; les mots-clés trop génériques de `reglementation` (standard, policy, legal, governance, directive) sont retirés (#118)

### Removed
- Sources `anthropic_blog` (plus de flux RSS, 404), `papers_with_code` (site fermé, redirigé vers Hugging Face) et `eurlex_ai` (page anti-robot au lieu du flux) : la collecte passe de 22 sources dont 5 sans article à 19 sources qui répondent toutes (#118)

---

## [1.0.0] — 2026-11-05

Première version publique : un serveur MCP de veille technologique qui collecte
22 sources (actualités, CVE, réglementation, blogs d'ingénierie), les filtre par
profil et par domaine et les expose à un assistant à travers 13 outils.

### Added

#### Fondations et serveur MCP (M0, M1)
- Structure du projet, `requirements.txt` / `requirements-dev.txt`, `.env.example` documenté, pre-commit (black, ruff, isort, detect-secrets), versionnage SemVer (`VERSION`)
- Squelette du serveur MCP (handlers, schémas, erreurs typées), configuration Pydantic Settings, logs loguru (JSON en production, rotation)
- Cache TTL, outil `novit_health` (état du cache et de chaque source, version)
- Image Docker multi-étapes et `docker-compose` de développement

#### Collecte (M2)
- Architecture `BaseScraper` / `Article` et scrapers Hacker News (API officielle), GitHub Trending, CVE/NVD, CERT-FR (ANSSI), RSS générique (dev.to, TechCrunch, The Verge, MIT Technology Review), blogs IA, ingénierie, réglementation et formation
- `ScraperManager` : collecte asynchrone de toutes les sources avec rapport, déduplication (URL puis similarité de Jaccard des titres), limiteur de débit par domaine avec backoff exponentiel, file de priorité à 3 niveaux
- Tagger automatique de domaines piloté par YAML, stockage SQLite (aiosqlite) avec rétention de 7 jours
- Configuration des sources 100 % déclarative et système de plugins de scrapers ([docs/PLUGINS.md](docs/PLUGINS.md))

#### Veille et expérience utilisateur (M3, M4, M5)
- Profils ETUDIANT et INGENIEUR, moteur de filtrage et de scoring par profil
- Outils `novit_get_news`, `novit_search`, `novit_get_by_domain`, `novit_dig` (contenu complet d'un article), `novit_related`, `novit_daily` (résumé du jour par domaine), `novit_trends` (sujets en montée rapide), `novit_unusual` (nouveautés insolites)
- Commandes `novit_start`, `novit_set_profile`, `novit_set_domains` (raccourcis, persistance), alertes personnalisées (info, important, critique), contexte de conversation (articles vus, navigation) et résumé de session
- Prompt système, prompts par profil, 6 formats de réponse standard, injection dynamique de contexte, guide de gestion des erreurs, gestion basique du français et de l'anglais, mode verbose/debug
- `scripts/demo.py` : session de démonstration sur les sources en direct, sans client MCP graphique

#### Robustesse et exploitation (M6)
- Circuit breaker par source, monitoring de disponibilité des sources, métriques applicatives
- Suivi des erreurs avec Sentry (actif seulement si `SENTRY_DSN` est défini), rotation des secrets ([docs/SECRET_ROTATION.md](docs/SECRET_ROTATION.md))
- Tests unitaires, d'intégration (collecte → tagging → stockage → outils), de performance et de régression des prompts ; CI GitHub Actions (lint, tests, paquet)
- Déploiement cloud sur Fly.io ([docs/CLOUD_DEPLOYMENT.md](docs/CLOUD_DEPLOYMENT.md))
- Transport HTTP pour le déploiement distant : `novit --transport http` (ou `NOVIT_TRANSPORT=http`) sert le serveur MCP en Streamable HTTP sur `/mcp`, protégé par le jeton bearer `NOVIT_API_TOKEN`, avec une sonde publique `/health` (`?sources=1` pour l'état des sources). stdio reste le défaut ([ADR-005](docs/ADR/0005-transport-http-authentification.md)) (#100)
- Mode hors-ligne dégradé : quand aucune source ne répond, `novit_get_news` et `novit_get_by_domain` servent les articles encore en base avec un bandeau qui indique la date et l'âge de la dernière collecte réussie ; la collecte est relancée en arrière-plan (30 s, 2 min, 5 min) et la réponse dégradée n'est gardée en cache qu'une minute ([guide des erreurs](docs/ERROR_HANDLING_GUIDE.md)) (#91)

#### Documentation (M7)
- README en page d'accueil (logo, démo animée, captures de réponses réelles), documentation technique, guides d'installation et d'utilisation, ajout d'une source ou d'un domaine, ADR, exemples de requêtes, guide de prompting, cadre d'évaluation de la qualité
- Wiki GitHub généré depuis `docs/wiki/` par le workflow « Wiki » (#78)

#### Collaboration (M8)
- Gouvernance, guide de contribution, modèles d'issue et de PR
- Multi-utilisateurs en HTTP : `NOVIT_API_TOKENS` donne un jeton à chaque utilisateur ; profil, domaines favoris et historique de session sont rangés par utilisateur et ne fuient pas de l'un à l'autre (ADR-006, #87)
- Outil `novit_feedback` : enregistre un retour (bug, suggestion, avis) avec l'outil et la requête concernés, le profil et la version, dans la table `feedback` de la base locale ; un bug renvoie un lien vers une issue GitHub pré-remplie. Rapport hebdomadaire : `scripts/feedback_report.py` (#89)
- Gestion des dépendances : Dependabot (actions mensuelles, Python hebdomadaire) et workflow « Dépendances » qui teste chaque lundi les dernières versions et les versions minimales déclarées ([docs/DEPENDENCIES.md](docs/DEPENDENCIES.md)) (#88)
- Support après release : `.github/SUPPORT.md` (canaux, délais de première réponse, triage hebdomadaire), `SECURITY.md` (signalement privé de vulnérabilités), `novit --version` (#97)

#### Publication (M9)
- Paquet Python `novit` (build hatchling, version lue dans `VERSION`) : commande `novit`, configuration YAML par défaut embarquée et utilisée quand `./config/` est absent ; job CI qui construit, vérifie (`twine check`) et installe la wheel hors du dépôt ; workflow de publication TestPyPI puis PyPI sur tag `vX.Y.Z` par trusted publishing ([docs/PUBLISHING.md](docs/PUBLISHING.md)) (#93)

### Changed
- **Rupture** : le package `src` devient `novit` et `config.settings` devient `novit.settings`. Lancement : `python -m novit.mcp` ou `novit` (mettre à jour la configuration du client MCP) (#93)
- Serveur migré vers l'API du SDK `mcp` 2.x (handlers `on_list_tools` / `on_call_tool` passés au constructeur de `Server`) ; dépendance relevée à `mcp>=2.3.0,<3`. Les erreurs d'outil sont signalées avec `isError` (#112)
- `novit_health` liste l'état de chaque source
- Statut du paquet : « Production/Stable »

### Performance
- Collecte complète des 22 sources en ~2 s au lieu de 6 à 9 s : les flux RSS sont téléchargés en asynchrone (httpx) et analysés hors de la boucle d'événements ; les items Hacker News sont récupérés 10 par 10. Une source RSS en erreur HTTP est désormais comptée en échec au lieu de « 0 article ». Mesure : `scripts/profile_scrapers.py` ([docs/PERFORMANCE.md](docs/PERFORMANCE.md)) (#90)

### Fixed
- `novit_search` cherche des mots entiers (index SQLite FTS5) au lieu de sous-chaînes : « rust » ne renvoie plus « trust » ; résultats classés par pertinence (#104)
- Les filtres de domaine et de profil s'appliquent avant la limite : les articles du domaine demandé ne sont plus évincés par ceux des autres domaines (#107)
- Dates des articles normalisées en UTC avec fuseau
- GitHub Trending : étoiles du jour affichées en français, plus d'étiquette IA attribuée à tort
- Les méthodes synchrones des préférences ne sont plus attendues avec `await`
- Les flux RSS sont demandés avec `NOVIT_USER_AGENT`

### Security
- Audit de la version : `pip-audit` ne relève aucune vulnérabilité connue dans les dépendances d'exécution ; les alertes `bandit` restantes sont documentées dans le code (empreinte MD5 de déduplication, requêtes SQL construites uniquement à partir de constantes)

---

## [0.1.0] — 2026-06-26

### Added
- Initialisation du dépôt GitHub NovIT (privé)
- README initial et LICENSE MIT
- `.gitignore` Python complet
- Branches `main` et `dev`
- 98 issues et 10 milestones créés sur GitHub

[Unreleased]: https://github.com/rmouahid/NovIT/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/rmouahid/NovIT/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/rmouahid/NovIT/releases/tag/v0.1.0
