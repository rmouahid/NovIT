# ADR-005 : Transport HTTP distant — Streamable HTTP du SDK `mcp`, jeton bearer statique

**Statut :** Acceptée
**Date :** 2026-10-21

## Contexte

[ADR-001](0001-transport-serveur-mcp.md) a retenu stdio pour l'usage local et laissé ouvert un
transport réseau pour le déploiement cloud (#100). `fly.toml` attend un serveur qui écoute sur
`$PORT` et répond sur `/health` ; `docs/CLOUD_DEPLOYMENT.md` liste aussi l'authentification du
transport distant comme décision à prendre. Contraintes : ne rien changer à l'usage local en
stdio, ne pas réécrire les handlers, et ne pas exposer les outils sur Internet sans contrôle
d'accès.

## Décision

1. **Transport** : `Streamable HTTP` du SDK `mcp` 2.x (`Server.streamable_http_app()`), servi
   par uvicorn sur `/mcp`. Les réponses longues et les notifications passent en flux SSE sur ce
   même endpoint. Sélection par `novit --transport http` ou `NOVIT_TRANSPORT=http` ; stdio reste
   le défaut.
2. **Authentification** : un jeton bearer statique, `NOVIT_API_TOKEN`, exigé sur tout chemin
   sauf `/health`, comparé en temps constant (`hmac.compare_digest`). Le serveur refuse de
   démarrer sans jeton dès qu'il écoute ailleurs qu'en local.
3. **Santé** : `GET /health` est une sonde de vie sans appel réseau (statut, version, uptime),
   en 200 tant que le processus répond. `GET /health?sources=1` renvoie le rapport complet de
   `get_health()`, toujours en 200 : une source tierce en panne ne justifie pas un redémarrage.

## Alternatives considérées

- **Ancien transport HTTP+SSE (`/sse` + `/messages/`)** — écarté : déprécié par la
  spécification MCP depuis la révision 2025-03-26, au profit de Streamable HTTP qui garde le
  flux SSE sur un seul endpoint. Les clients MCP actuels parlent Streamable HTTP.
- **FastAPI** (prévu par l'architecture initiale) — écarté : le SDK fournit déjà une
  application Starlette complète (sessions, sécurité des en-têtes `Host`/`Origin`, limite de
  taille des requêtes) ; une couche FastAPI n'ajouterait qu'une indirection. `fastapi` reste en
  dépendance pour l'instant (voir Conséquences).
- **OAuth 2.1** (mécanisme d'autorisation de la spécification MCP, pris en charge par le SDK
  via `AuthSettings` et `TokenVerifier`) — écarté pour un premier déploiement mono-utilisateur :
  il impose un serveur d'autorisation, sans bénéfice tant qu'une seule personne utilise
  l'instance. C'est l'évolution naturelle si l'instance devient partagée.
- **Pas d'authentification derrière une URL secrète** — écarté : une URL fuit (logs,
  historique) et ne se révoque pas sans redéployer.

## Conséquences

- Une instance = un utilisateur. L'état de session (profil, domaines choisis) est global au
  processus, comme en stdio : deux clients connectés à la même instance le partagent. Le
  multi-utilisateur (#87) reste à faire, avec OAuth et un état par session ; SQLite sur un
  volume mono-instance ([ADR-002](0002-sqlite-dev-postgresql-prod.md)) suffit d'ici là.
- Le jeton se change avec `fly secrets set NOVIT_API_TOKEN=...` ; Fly.io redémarre l'instance,
  ce qui coupe les sessions ouvertes. Pas de rotation à chaud, contrairement aux clés API de
  [SECRET_ROTATION.md](../SECRET_ROTATION.md).
- `fastapi` n'est toujours pas utilisé : sa suppression des dépendances est à trancher avant
  la v1.0 (#92).
- Le TLS est assuré par la plateforme (Fly.io termine HTTPS) ; uvicorn ne sert que du HTTP
  derrière elle. Un déploiement sans proxy TLS ferait transiter le jeton en clair.
