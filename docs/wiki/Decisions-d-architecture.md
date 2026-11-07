# Décisions d'architecture (ADR)

Chaque décision structurante est consignée dans un *Architecture Decision
Record* sous [`docs/ADR/`](https://github.com/rmouahid/NovIT/tree/dev/docs/ADR),
à partir du [modèle](https://github.com/rmouahid/NovIT/blob/dev/docs/ADR/template.md).
Un changement structurant (nouvelle dépendance majeure, format de sortie,
architecture) se discute d'abord dans une issue, puis donne lieu à un ADR
([gouvernance](https://github.com/rmouahid/NovIT/blob/dev/GOVERNANCE.md)).

| ADR | Décision | Statut |
|---|---|---|
| [ADR-001](https://github.com/rmouahid/NovIT/blob/dev/docs/ADR/0001-transport-serveur-mcp.md) | Serveur écrit avec le SDK officiel `mcp`, transport stdio, sans FastAPI | Acceptée, complétée par ADR-005 |
| [ADR-002](https://github.com/rmouahid/NovIT/blob/dev/docs/ADR/0002-sqlite-dev-postgresql-prod.md) | SQLite (`aiosqlite`) en local ; PostgreSQL envisagé en production | Acceptée (SQLite) / non implémentée (PostgreSQL) |
| [ADR-003](https://github.com/rmouahid/NovIT/blob/dev/docs/ADR/0003-strategie-cache-ttl.md) | Cache en mémoire avec un TTL par type de contenu | Acceptée |
| [ADR-004](https://github.com/rmouahid/NovIT/blob/dev/docs/ADR/0004-format-sortie-standardise.md) | Réponses en texte Markdown structuré plutôt qu'en JSON | Acceptée |
| [ADR-005](https://github.com/rmouahid/NovIT/blob/dev/docs/ADR/0005-transport-http-authentification.md) | Transport distant en Streamable HTTP, jeton bearer statique | Acceptée |

## Écrire un nouvel ADR

1. Copier `docs/ADR/template.md` en `docs/ADR/000N-titre-court.md`.
2. Remplir contexte, options envisagées, décision et conséquences.
3. L'ajouter à ce tableau (`docs/wiki/Decisions-d-architecture.md`) dans la
   même pull request.
