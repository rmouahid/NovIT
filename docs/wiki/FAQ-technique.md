# FAQ technique

## Installation et démarrage

**Le client MCP ne voit aucun outil NovIT.**
Le client doit lancer l'interpréteur de l'environnement virtuel avec un chemin
absolu (`/chemin/vers/NovIT/.venv/bin/python -m novit.mcp`), ou la commande
`novit` si le paquet est installé. Vérifiez que le serveur démarre seul :
`python -m novit.mcp < /dev/null` doit se terminer sans erreur.

**Quelle version est installée ?**
`novit --version`. Joignez-la à tout signalement de bug.

**Je vois du texte parasite dans la réponse du client, ou la connexion se coupe.**
En transport stdio, la sortie standard est réservée aux messages JSON-RPC :
tout `print()` casse le protocole. Les journaux passent par loguru sur la
sortie d'erreur ; leur niveau se règle avec `NOVIT_LOG_LEVEL`.

## Données et sources

**Où sont stockés les articles ?**
Dans la base SQLite `NOVIT_DB_PATH` (défaut `./novit.db`). Les articles plus
vieux que `NOVIT_RETENTION_DAYS` (7 jours par défaut) sont purgés. La même base
contient les retours envoyés avec `novit_feedback`.

**Une source apparaît en échec dans `novit_health`.**
`novit_health` avec `detail=sources` donne l'erreur de chaque source. Une erreur
HTTP (404, 301 non suivie) signifie le plus souvent que le flux a changé d'URL :
corrigez-la dans `config/sources.yaml`, rechargée sans redémarrer. Pour
mesurer toutes les sources : `python scripts/profile_scrapers.py`.

**Toutes les sources sont injoignables : NovIT répond-il encore ?**
Oui, en mode hors-ligne : les articles encore en base sont servis avec un
bandeau qui indique l'âge de la dernière collecte, et la collecte est relancée
en arrière-plan (voir le
[guide des erreurs](https://github.com/rmouahid/NovIT/blob/dev/docs/ERROR_HANDLING_GUIDE.md)).

**Combien de temps prend une collecte complète ?**
Environ 2 secondes pour 22 sources, les scrapers tournant en parallèle (mesures
dans [docs/PERFORMANCE.md](https://github.com/rmouahid/NovIT/blob/dev/docs/PERFORMANCE.md)).

**Pourquoi la même question renvoie-t-elle la même réponse pendant un moment ?**
Les réponses sont mises en cache en mémoire : 1 h pour les actualités, 30 min
pour la recherche, 1 min pour une réponse hors-ligne
([ADR-003](https://github.com/rmouahid/NovIT/blob/dev/docs/ADR/0003-strategie-cache-ttl.md)).

## Déploiement

**Comment exposer NovIT sur un serveur ?**
`novit --transport http` (ou `NOVIT_TRANSPORT=http`) sert le protocole MCP sur
`/mcp`, protégé par le jeton `NOVIT_API_TOKEN`, obligatoire dès que
`NOVIT_HOST` n'est pas local. `/health` reste public pour les sondes. Détails :
[déploiement cloud](https://github.com/rmouahid/NovIT/blob/dev/docs/CLOUD_DEPLOYMENT.md),
[rotation des secrets](https://github.com/rmouahid/NovIT/blob/dev/docs/SECRET_ROTATION.md).

## Développement

**Comment lancer les tests comme la CI ?**
`pip install -r requirements-dev.txt`, puis `black --check novit tests`,
`isort --check-only --profile black novit tests`, `ruff check novit tests` et
`pytest tests/ --benchmark-skip`.

**Comment ajouter une source sans toucher au code ?**
Un flux RSS s'ajoute dans `config/sources.yaml` ; une source spécifique
s'écrit en plugin
([docs/PLUGINS.md](https://github.com/rmouahid/NovIT/blob/dev/docs/PLUGINS.md)).

**Comment sont gérées les dépendances ?**
Bornes basses uniquement, Dependabot chaque semaine, et un workflow qui teste
les dernières versions comme les versions minimales
([docs/DEPENDENCIES.md](https://github.com/rmouahid/NovIT/blob/dev/docs/DEPENDENCIES.md)).
