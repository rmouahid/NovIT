# Déploiement cloud — préparation

**Statut : préparation seulement, pas encore déployable.** Ce document et les fichiers qu'il
référence mettent en place le pipeline de déploiement pour quand le prérequis ci-dessous sera
résolu — ne pas s'attendre à un déploiement fonctionnel en l'exécutant aujourd'hui.

## Prérequis non satisfait : transport HTTP/SSE

NovIT ne parle que **stdio** avec Claude Desktop ([ADR-001](ADR/0001-transport-serveur-mcp.md)) :
le serveur est lancé comme sous-processus local, il n'écoute aucun port réseau. Un déploiement
cloud n'a de sens que si un client distant peut s'y connecter — ce qui nécessite le transport
HTTP+SSE mentionné comme piste dans MCP_NOTES.md, **non implémenté à ce jour**. Tant que ce
travail n'est pas fait :

- `fly.toml` (`internal_port`, health check `/health`) référence une interface qui n'existe pas
  encore côté serveur.
- `scripts/deploy.sh` s'arrêtera en échec dès le health check Fly.io.

Ce document prépare le reste du pipeline (plateforme, configuration, variables d'environnement,
script) pour ne garder que l'implémentation du transport HTTP+SSE comme travail restant avant un
déploiement réel.

## Choix de la plateforme : Fly.io

| Option | Décision |
|---|---|
| **Fly.io** | ✅ Retenu — Dockerfile existant réutilisable tel quel, volumes persistants pour `novit.db` (SQLite, voir [ADR-002](ADR/0002-sqlite-dev-postgresql-prod.md)), `auto_stop_machines` pour ne payer qu'à l'usage, région proche des utilisateurs (`cdg`/Paris par défaut). |
| Railway | Écarté — bon DX également, mais moins de contrôle fin sur les volumes persistants pour SQLite en usage mono-instance ; à reconsidérer si PostgreSQL managé devient le backend (ADR-002). |
| VPS nu | Écarté pour un premier déploiement — demande de gérer soi-même TLS, restarts, monitoring d'infra ; NovIT n'a pas encore le volume d'usage qui justifierait de s'affranchir d'une plateforme managée. |

## Fichiers créés

- **`fly.toml`** — build sur le `Dockerfile` existant, volume persistant `/data` (base SQLite),
  variables d'environnement de production, `auto_stop_machines` (scale to zero).
- **`scripts/deploy.sh`** — pipeline : vérifie `flyctl` installé → lint (black/isort/ruff) →
  tests (`pytest tests/ --benchmark-skip`) → `flyctl deploy`. Échoue avant d'atteindre Fly.io si
  le lint ou les tests échouent (pas de déploiement d'un état cassé).

## Variables d'environnement de production

En plus de celles déjà documentées dans [`.env.example`](../.env.example) et
l'[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md), en production sur Fly.io :

| Variable | Valeur prod | Où la définir |
|---|---|---|
| `NOVIT_ENV` | `production` | `fly.toml` `[env]` (déjà fait — active les logs JSON structurés) |
| `NOVIT_HOST` / `NOVIT_PORT` | `0.0.0.0` / `8080` | `fly.toml` `[env]` (une fois le transport HTTP prêt) |
| `NOVIT_DB_PATH` | `/data/novit.db` | `fly.toml` `[env]` (sur le volume persistant monté) |
| `SENTRY_DSN`, `NVD_API_KEY`, `GITHUB_TOKEN` | — | **Jamais dans `fly.toml`** (versionné) : `fly secrets set SENTRY_DSN=... NVD_API_KEY=...` |

Voir [SECRET_ROTATION.md](SECRET_ROTATION.md) pour la rotation de ces secrets une fois en
production — `reload_settings()`/`ScraperManager.reload_sources()` fonctionnent identiquement en
déploiement cloud.

## Déploiement (une fois le prérequis résolu)

```bash
flyctl auth login
flyctl apps create novit-mcp   # une seule fois
flyctl secrets set SENTRY_DSN=... NVD_API_KEY=... --app novit-mcp
./scripts/deploy.sh
```

## Ce qui reste à faire avant un déploiement réel

1. Implémenter le transport HTTP+SSE (`fastapi`/`uvicorn`, déjà en dépendances — voir
   [ADR-001](ADR/0001-transport-serveur-mcp.md)) à côté du transport stdio existant, sans casser
   l'usage local avec Claude Desktop.
2. Exposer une route `/health` HTTP qui réutilise `get_health()` (`src/mcp/health.py`).
3. Décider de l'authentification du transport distant (le protocole MCP ne définit pas de
   mécanisme d'auth HTTP standard à ce jour — à documenter dans une ADR dédiée le moment venu).
4. Revoir le volet multi-utilisateurs (#87) et SQLite (ADR-002) si le déploiement doit servir
   plusieurs utilisateurs simultanément.
