# Documentation technique — NovIT

> Reflète l'implémentation réelle du code (à distinguer de [ARCHITECTURE.md](ARCHITECTURE.md),
> qui est la vision technique initiale rédigée avant l'implémentation — certains choix y ont
> changé en cours de route, notés ci-dessous).

---

## 1. Vue d'ensemble

NovIT est un **serveur MCP (Model Context Protocol)** : Claude s'y connecte comme client MCP,
liste les outils disponibles, puis les appelle avec des arguments structurés. Le serveur agrège
des articles depuis des sources externes (Hacker News, GitHub Trending, flux RSS, CVE/ANSSI...),
les filtre/score selon le profil utilisateur, et retourne du texte markdown prêt à être présenté
par Claude.

```
┌─────────────┐   MCP (stdio, JSON-RPC 2.0)   ┌───────────────────────┐    HTTP    ┌──────────────┐
│             │───────────────────────────────▶│                       │───────────▶│ Sources web  │
│   Claude    │                                 │   Serveur NovIT       │            │ (HN, GitHub, │
│  (client)   │◀───────────────────────────────│   (SDK `mcp`, stdio)   │◀───────────│  CVE, RSS…)  │
│             │      Réponse texte markdown      │                       │  Articles  │              │
└─────────────┘                                 └───────────┬───────────┘            └──────────────┘
                                                              │
                                              ┌───────────────┴────────────────┐
                                              │  TTLCache (mémoire) + SQLite    │
                                              │  (aiosqlite, novit.db)          │
                                              └─────────────────────────────────┘
```

**Écart avec ARCHITECTURE.md v0.1 :** le serveur n'utilise pas FastAPI. `src/mcp/server.py`
instancie directement `mcp.server.Server` (SDK Python officiel MCP) sur transport **stdio**.
`fastapi`/`uvicorn` restent dans `requirements.txt` en prévision d'un transport HTTP+SSE pour
un déploiement distant (voir [MCP_NOTES.md](MCP_NOTES.md)), non implémenté à ce jour.

---

## 2. Modules

### `src/mcp/` — Serveur et logique applicative

| Fichier | Rôle |
|---|---|
| `server.py` | Point d'entrée. Instancie `Server("novit")`, déclare `TOOLS` (13 outils, schémas JSON), route `call_tool()` vers les handlers. |
| `handlers.py` | Implémente `novit_get_news`, `novit_search`, `novit_get_by_domain`, `novit_get_profile` : cache → lecture `ArticleStore` → scraping si insuffisant → `filter_and_rank` → formatage markdown. |
| `schemas.py` | Modèles Pydantic d'entrée (`GetNewsInput`, `SearchInput`, `GetByDomainInput`, `GetProfileInput`) et de sortie (`ArticleResult`). |
| `errors.py` | `NovitErrorCode` (`StrEnum`, 8 codes `NOVIT_*`) et `NovitError` (exception → `to_mcp_error()` → texte affiché à Claude). |
| `cache.py` | `TTLCache` en mémoire (thread-safe, `Lock`), TTL par type de contenu (`TTL_NEWS`, `TTL_SEARCH`, `TTL_PROFILE`, `TTL_HEALTH`). |
| `circuit_breaker.py` | `CircuitBreaker` / `CircuitBreakerRegistry` par source (CLOSED → OPEN → HALF_OPEN). **Non encore branché** au `ScraperManager` (voir §4). |
| `monitoring.py` | `SourceStatus` / `MonitoringReport`, persistance JSON du downtime cumulé par source. **Non encore branché** à un outil MCP ni au `ScraperManager`. |
| `metrics.py` | `MetricsCollector` (appels/erreurs d'outil, latence par source, requêtes par domaine/profil), export dict ou Prometheus. **Non encore appelé** depuis `server.py`/`handlers.py`. |
| `health.py` | `get_health()` / `get_sources_health()` / `get_cache_health()`, backend de `novit_health`. `sources` est actuellement toujours vide (stub jamais raccordé au `ScraperManager` — cache seul est réellement rapporté). |
| `debug.py` | `DebugInfo` / `append_debug()` : bloc markdown de diagnostic ajouté en pied de réponse en mode verbose. |
| `daily.py`, `trends.py`, `dig.py`, `related.py`, `unusual.py` | Handlers des outils du même nom (résumé quotidien, tendances, extraction d'article, articles similaires, découvertes insolites). |
| `context.py`, `session.py`, `session_summary.py` | Contexte de conversation NovIT (session en mémoire, historique vu/non-vu, résumé de session). |
| `onboarding.py`, `profile_selector.py`, `domain_selector.py` | `novit_start`, `novit_set_profile`, `novit_set_domains` : sélection/persistance du profil et des domaines actifs. |
| `alerts.py` | `AlertManager` (`StrEnum` `AlertLevel` info/important/critique) pour les alertes personnalisées. |
| `i18n.py` | Détection de langue basique + `t()` pour les chaînes FR/EN. |
| `logging_config.py` | Configuration `loguru` (niveau, fichier, format JSON en production). |

### `src/scrapers/` — Sources de données

Chaque source implémente le contrat `BaseScraper` (`src/scrapers/base.py`) :

```python
class BaseScraper(ABC):
    name: str
    domains: list[str]
    profiles: list[str] = ["ETUDIANT", "INGENIEUR"]

    async def fetch(self) -> list[Article]: ...
    async def health_check(self) -> bool: ...
```

`Article` (dataclass, `src/scrapers/base.py`) : `title`, `url`, `summary`, `published_at`,
`source`, `domains`, `profiles`, `score`, `extra`. Égalité/hash basés sur `url`.

| Fichier | Rôle |
|---|---|
| `manager.py` | `ScraperManager` : construit la liste des scrapers (22 sources actuellement), les lance en parallèle (`asyncio.gather` + timeout individuel), agrège, déduplique par URL, produit un `FetchResult` (articles + `ScraperReport` par source). |
| `hacker_news.py`, `github_trending.py`, `cve.py` (CVE NVD + ANSSI) | Scrapers dédiés par API. |
| `rss.py`, `ai_blogs.py`, `eng_blogs.py`, `regulation.py`, `training.py` | `RssScraper` générique instancié depuis `config/sources.yaml` (`load_rss_sources()`, filtré par `category`) ; `ai_blogs.py`/`training.py` ajoutent en plus un scraper code (`ArxivScraper`/`RoadmapScraper`) pour les sources non-RSS. |
| `deduplication.py` | `Deduplicator` : dédoublonnage par URL exacte, hash de titre normalisé, et similarité de Jaccard fuzzy (seuil configurable, 0.7 par défaut). Complexité fuzzy en O(n²) sur la fenêtre — voir `tests/test_performance.py`. |
| `storage.py` | `ArticleStore` : persistance SQLite async (`aiosqlite`), rétention configurable, recherche plein texte `LIKE`. |
| `tagger.py` | `DomainTagger` : enrichit `article.domains` par mots-clés (`config/domains.yaml`), sans jamais écraser les tags déjà posés par le scraper. |
| `queue.py`, `rate_limiter.py` | File d'attente de scraping à 3 niveaux de priorité, limiteur de débit par source. |
| `_template.py` | Squelette à copier pour ajouter une nouvelle source. |

### `src/profiles/` — Filtrage et scoring

| Fichier | Rôle |
|---|---|
| `profile.py` | `Profile` / `ProfileConfig`, chargés depuis `config/profiles.yaml`. `source_weight()` (1.5 si source prioritaire, 1.0 sinon), `domain_weight()` (1.5 favori / 1.0 secondaire / 0.6 autre). |
| `filter.py` | `score_article()` = `article.score × source_weight × max(domain_weight)`. `filter_and_rank()` : filtre par domaine → filtre par profil cible → filtre par `score_min` du profil → tri décroissant → limite. |
| `preferences.py` | Persistance des préférences utilisateur (profil actif, domaines actifs) entre sessions. |

### `config/` — Configuration déclarative

| Fichier | Contenu |
|---|---|
| `settings.py` | `Settings` (Pydantic Settings), préfixe d'env `NOVIT_`, chargé depuis `.env`. |
| `profiles.yaml` | Définition des 2 profils (sources prioritaires, domaines favoris/secondaires, `score_min`, `nb_articles_defaut`). |
| `domains.yaml` | Mots-clés de tagging par domaine NovIT. |
| `sources.yaml` | Sources RSS déclaratives (`name`, `url`, `domains`, `profiles`, `base_score`, `category`) — voir [ADDING_A_SOURCE.md](ADDING_A_SOURCE.md). Chargé/validé par `load_rss_sources()` (`src/scrapers/rss.py`), aucun cache : `ScraperManager.reload_sources()` permet de recharger sans redémarrer le serveur. |

### `src/prompts/`

Vide à ce jour (`__init__.py` + `.gitkeep`). Les « prompts » NovIT sont en réalité des documents
markdown lus par Claude comme instructions (pas de génération dynamique de prompt côté serveur) :
voir [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md), [PROFILE_PROMPTS.md](PROFILE_PROMPTS.md),
[RESPONSE_FORMATS.md](RESPONSE_FORMATS.md), [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md).

### `tests/`

Structure plate (pas de sous-dossiers `unit/`/`integration/` contrairement à ARCHITECTURE.md v0.1) :
un fichier par module + `test_integration.py` (flux multi-modules) + `test_performance.py`
(benchmarks) + `test_prompt_regression.py` (formats de réponse par profil). `conftest.py` fournit
les fixtures partagées (`make_article`, etc.).

---

## 3. Outils MCP

Déclarés dans `TOOLS` (`src/mcp/server.py`), routés dans `call_tool()`. Toutes les réponses sont
du texte markdown (`TextContent`), avec `isError: true` en cas de `NovitError` non rattrapée.

| Outil | Entrées (obligatoire en gras) | Sortie |
|---|---|---|
| `novit_get_news` | **`profil`** (ETUDIANT\|INGENIEUR), `domaines[]`, `nb_articles` (déf. 10), `periode` (1h\|6h\|24h\|7j, déf. 24h) | Liste markdown numérotée, triée par score, groupée sous un titre `# Veille NovIT — {période} · {domaines}`. |
| `novit_search` | **`query`**, `domaine`, `source`, `profil`, `page` (déf. 1), `per_page` (déf. 10) | `# Recherche : « {query} »`, résultats paginés en base SQLite (`LIKE` sur titre/résumé). |
| `novit_get_by_domain` | **`domaine`**, `profil` (déf. INGENIEUR), `nb_articles` (déf. 10) | Articles filtrés par domaine, `# Domaine : {domaine}`. |
| `novit_get_profile` | **`profil`** | Résumé du profil (`Profile.to_summary()`) : sources prioritaires, domaines favoris, score minimum. |
| `novit_set_domains` | **`domaines`** (string `"ia, securite"` ou array, ou `"tout"`) | Confirmation + persistance dans les préférences. |
| `novit_set_profile` | **`profil`** | Confirmation + persistance dans les préférences. |
| `novit_start` | `profil` (optionnel) | Menu de sélection de profil si absent, message de bienvenue sinon. |
| `novit_unusual` | `count` (déf. 3, 1-5) | Articles insolites (score de surprise), profil ETUDIANT. |
| `novit_trends` | `days` (déf. 7), `top_k` (déf. 10) | `# Tendances NovIT — {days} derniers jours` : sujets fréquents + sujets en montée rapide (ratio 24h/période > 1.5). |
| `novit_daily` | **`profil`**, `domaines[]` | `# Veille quotidienne NovIT`, groupé par domaine (emoji dédié), 3 articles max/domaine. |
| `novit_related` | `url`, `title`, `domaines[]`, `top_k` (déf. 5) | Articles similaires (Jaccard 60% domaines + 40% mots du titre), fenêtre 7 jours. |
| `novit_dig` | **`url`** | Extraction du contenu principal de la page (heuristique `article`/`main`/`section`, fallback `body`), tronqué à 4000 caractères. |
| `novit_health` | `detail` (global\|sources\|cache, déf. global) | Statut serveur : uptime, version, stats cache. `sources` toujours vide actuellement (voir §2, `health.py`). |

Schémas JSON complets : voir `TOOLS` dans `src/mcp/server.py`, ou [MCP_NOTES.md](MCP_NOTES.md)
pour le format générique requête/réponse MCP.

---

## 4. Guide de débogage

### Logs

`loguru`, configuré par `configure_logging()` (`src/mcp/logging_config.py`) au démarrage du
serveur. Niveau piloté par `NOVIT_LOG_LEVEL` (`.env` ou variable d'environnement, `DEBUG` en
dev). **Important en transport stdio** : les logs doivent aller sur **stderr**, jamais sur
stdout (réservé aux messages JSON-RPC) — ne pas utiliser `print()`.

### Mode verbose par outil

`DebugInfo` (`src/mcp/debug.py`) + `append_debug()` ajoutent un bloc `**🔍 Debug NovIT**` en
pied de réponse (temps d'exécution, sources consultées, nombre d'articles avant/après filtrage,
cache hit/miss, erreurs). À activer en passant `debug=True` dans les arguments d'un outil
(quand le handler le supporte).

### `novit_health`

Donne l'uptime, la version (`VERSION`), et les stats du `TTLCache` (`entries`, `hit_rate`,
`hits`/`misses`). Ne reflète **pas encore** l'état réel des sources de scraping : le circuit
breaker (`circuit_breaker.py`) et le monitoring (`monitoring.py`) existent et sont testés
indépendamment, mais ne sont pas encore appelés depuis `health.py`/`ScraperManager` — c'est une
dette connue, pas un bug caché.

### Monitoring d'erreurs (Sentry)

Optionnel, désactivé par défaut. Renseigner `SENTRY_DSN` dans `.env` (voir `.env.example`)
pour l'activer — sans DSN, `init_sentry()` (`src/mcp/sentry_config.py`) ne fait rien, aucun
appel réseau. Toute exception non gérée dans `call_tool()` (`src/mcp/server.py`) est envoyée
avec un contexte enrichi : nom de l'outil MCP, profil et domaine (tags `mcp_tool`,
`novit_profil`, `novit_domaine`), arguments complets en contexte. `NOVIT_ENV` détermine
l'environnement Sentry (`development`/`staging`/`production`). `SENTRY_TRACES_SAMPLE_RATE`
(0.0 par défaut) contrôle le tracing de performance, indépendant de la capture d'erreurs.

### Erreurs NovIT

Chaque erreur applicative est un `NovitError(code, message)` (`src/mcp/errors.py`), converti en
texte via `to_mcp_error()` → `"Erreur NovIT [{code}] : {message}"`. Codes disponibles :
`NOVIT_SOURCE_UNAVAILABLE`, `NOVIT_SOURCE_TIMEOUT`, `NOVIT_NO_RESULTS`, `NOVIT_INVALID_PROFILE`,
`NOVIT_INVALID_DOMAIN`, `NOVIT_CACHE_ERROR`, `NOVIT_SCRAPER_ERROR`, `NOVIT_INTERNAL_ERROR`. Voir
[ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) pour la façon dont Claude doit reformuler
chaque code à l'utilisateur.

### Reproduire un problème de scraping

1. Isoler le scraper concerné : `python -c "import asyncio; from src.scrapers.hacker_news import HackerNewsScraper; print(asyncio.run(HackerNewsScraper().fetch()))"`.
2. Vérifier son `health_check()` séparément (ne dépend pas du réseau applicatif NovIT).
3. `ScraperManager._run_scraper()` capture toute exception par scraper (timeout inclus) sans
   faire échouer les autres sources — un scraper cassé n'empêche jamais `fetch_all()` de
   retourner les autres résultats. Regarder `ScraperReport.error` dans les logs pour la cause.

### Tests et couverture locale

```bash
pip install -r requirements-dev.txt
pytest tests/                       # suite complète + couverture (voir pyproject.toml)
pytest tests/ --benchmark-skip      # exclut les tests de performance (plus rapide)
black --check src tests && isort --check-only --profile black src tests && ruff check src tests
```

La CI (`.github/workflows/ci.yml`) exécute exactement ces commandes sur chaque push/PR vers
`main`/`dev`.

### Base SQLite locale

`ArticleStore` écrit dans `NOVIT_DB_PATH` (déf. `./novit.db`). Pour repartir d'une base vide :
supprimer ce fichier (il est recréé au prochain appel — schéma dans `src/scrapers/storage.py`).
