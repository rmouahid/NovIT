# ADR-001 : Transport du serveur MCP — SDK officiel `mcp` en stdio (pas FastAPI)

**Statut :** Acceptée
**Date :** 2026-07-07 (rédigée rétroactivement — voir « Contexte » ci-dessous)

## Contexte

La vision technique initiale du projet ([ARCHITECTURE.md](../ARCHITECTURE.md) v0.1, juin 2026)
prévoyait un serveur **FastAPI**, avant que l'implémentation ne démarre réellement. `fastapi` et
`uvicorn` ont été ajoutés à `requirements.txt` sur cette base. En pratique, l'implémentation du
serveur MCP (`src/mcp/server.py`) a divergé de ce plan initial pendant le développement des
outils MCP (mi-2026) : NovIT est un serveur MCP en usage local avec Claude Desktop, qui parle le
protocole MCP directement sur **stdio** (stdin/stdout) — un framework HTTP complet n'apporte
rien à ce cas d'usage tant qu'aucun transport réseau n'est requis.

## Décision

Le serveur utilise le **SDK Python officiel `mcp`** (`mcp.server.Server`, transport
`mcp.server.stdio.stdio_server`) directement, sans FastAPI. `app = Server("novit")` déclare les
outils (`TOOLS`) et route les appels (`call_tool()`) sans passer par une couche HTTP.

## Alternatives considérées

- **FastAPI + endpoint HTTP MCP** — écartée pour l'usage local actuel : ajoute une dépendance et
  une surface (port, CORS, auth HTTP) sans bénéfice quand Claude Desktop lance le serveur comme
  sous-processus stdio. Redevient pertinente pour un déploiement distant (voir Conséquences).
- **Implémenter le protocole JSON-RPC à la main** — écartée : le SDK officiel gère le handshake,
  la validation des schémas d'outils et les types MCP (`Tool`, `TextContent`), sans valeur
  ajoutée à le réécrire.

## Conséquences

- `fastapi`/`uvicorn` restent dans `requirements.txt`, non utilisés à ce jour — dette
  documentaire potentielle (dépendances qui donnent une fausse impression d'architecture) tant
  qu'un transport HTTP+SSE n'est pas implémenté pour le déploiement cloud (#86, prévu, pas fait).
- Les logs doivent impérativement sortir sur **stderr**, jamais sur stdout (réservé au JSON-RPC)
  — contrainte structurante pour tout le module `src/mcp/logging_config.py` et tout code qui
  serait tenté d'utiliser `print()`.
- Un transport HTTP+SSE distinct devra être ajouté (probablement en réutilisant FastAPI, d'où
  sa présence conservée dans les dépendances) sans réécrire la logique métier des handlers,
  qui est déjà découplée du transport.
