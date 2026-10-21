# Déploiement cloud — préparation

**Statut : déployable en mono-utilisateur.** Le serveur sait écouter en HTTP (#100) ; une
instance sert une seule personne, protégée par un jeton (voir la section « Limites »).

## Transport HTTP

En local, NovIT parle **stdio** avec le client MCP ([ADR-001](ADR/0001-transport-serveur-mcp.md)).
Pour un client distant, `novit --transport http` (ou `NOVIT_TRANSPORT=http`) sert le même
serveur en **Streamable HTTP** ([ADR-005](ADR/0005-transport-http-authentification.md)) :

| Chemin | Rôle | Accès |
|---|---|---|
| `/mcp` | endpoint MCP (requêtes POST, réponses et notifications en flux SSE) | `Authorization: Bearer $NOVIT_API_TOKEN` |
| `/health` | sonde de vie (statut, version, uptime), sans appel réseau | public |
| `/health?sources=1` | rapport complet de `get_health()`, état de chaque source | public |

Sans `NOVIT_API_TOKEN`, le serveur refuse de démarrer s'il écoute ailleurs qu'en local.
Essai en local :

```bash
NOVIT_API_TOKEN=essai novit --transport http   # http://127.0.0.1:8000/mcp
curl http://127.0.0.1:8000/health
```

Côté client, déclarer l'URL `https://<app>.fly.dev/mcp` et l'en-tête `Authorization`.

## Choix de la plateforme : Fly.io

| Option | Décision |
|---|---|
| **Fly.io** | ✅ Retenu — Dockerfile existant réutilisable tel quel, volumes persistants pour `novit.db` (SQLite, voir [ADR-002](ADR/0002-sqlite-dev-postgresql-prod.md)), `auto_stop_machines` pour ne payer qu'à l'usage, région proche des utilisateurs (`cdg`/Paris par défaut). |
| Railway | Écarté — bon DX également, mais moins de contrôle fin sur les volumes persistants pour SQLite en usage mono-instance ; à reconsidérer si PostgreSQL managé devient le backend (ADR-002). |
| VPS nu | Écarté pour un premier déploiement — demande de gérer soi-même TLS, restarts, monitoring d'infra ; NovIT n'a pas encore le volume d'usage qui justifierait de s'affranchir d'une plateforme managée. |

## Fichiers créés

- **`fly.toml`** — build sur le `Dockerfile` existant, lancement en `--transport http` sur le
  port 8080, health check `/health`, volume persistant `/data` (base SQLite), variables
  d'environnement de production, `auto_stop_machines` (scale to zero).
- **`scripts/deploy.sh`** — pipeline : vérifie `flyctl` installé → lint (black/isort/ruff) →
  tests (`pytest tests/ --benchmark-skip`) → `flyctl deploy`. Échoue avant d'atteindre Fly.io si
  le lint ou les tests échouent (pas de déploiement d'un état cassé).

## Variables d'environnement de production

En plus de celles déjà documentées dans [`.env.example`](../.env.example) et
l'[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md), en production sur Fly.io :

| Variable | Valeur prod | Où la définir |
|---|---|---|
| `NOVIT_ENV` | `production` | `fly.toml` `[env]` (déjà fait — active les logs JSON structurés) |
| `NOVIT_TRANSPORT` | `http` | `fly.toml` `[env]` |
| `NOVIT_HOST` / `NOVIT_PORT` | `0.0.0.0` / `8080` | `fly.toml` `[env]` |
| `NOVIT_API_TOKEN` | jeton long et aléatoire (`openssl rand -hex 32`) | **Secret** : `fly secrets set NOVIT_API_TOKEN=...` |
| `NOVIT_DB_PATH` | `/data/novit.db` | `fly.toml` `[env]` (sur le volume persistant monté) |
| `SENTRY_DSN`, `NVD_API_KEY`, `GITHUB_TOKEN` | — | **Jamais dans `fly.toml`** (versionné) : `fly secrets set SENTRY_DSN=... NVD_API_KEY=...` |

Voir [SECRET_ROTATION.md](SECRET_ROTATION.md) pour la rotation de ces secrets une fois en
production — `reload_settings()`/`ScraperManager.reload_sources()` fonctionnent identiquement en
déploiement cloud.

## Déploiement

```bash
flyctl auth login
flyctl apps create novit-mcp   # une seule fois
flyctl volumes create novit_data --region cdg --size 1 --app novit-mcp   # une seule fois
flyctl secrets set NOVIT_API_TOKEN=$(openssl rand -hex 32) SENTRY_DSN=... NVD_API_KEY=... --app novit-mcp
./scripts/deploy.sh
```

## Limites

- **Un utilisateur par instance** : profil et domaines choisis sont globaux au processus ; deux
  clients sur la même instance les partagent. Le multi-utilisateur (#87) demandera OAuth et un
  état par session, puis une base partagée si plusieurs instances tournent (ADR-002).
- **Changer le jeton** (`fly secrets set NOVIT_API_TOKEN=...`) redémarre l'instance et coupe les
  sessions ouvertes.
- **TLS** : assuré par Fly.io. Sans proxy HTTPS devant uvicorn, le jeton circulerait en clair.
