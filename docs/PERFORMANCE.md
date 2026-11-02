# Performances de collecte

Objectif (#90) : un rafraîchissement complet de toutes les sources en moins de
60 secondes.

## Mesurer

```bash
python scripts/profile_scrapers.py --top 10
```

Le script lance `ScraperManager.fetch_all()` sur les sources réelles, comme le
serveur, puis affiche le temps total et les sources les plus lentes. Les
scrapers tournent en parallèle : le temps total est celui de la source la plus
lente, plafonné par le timeout par scraper (30 s).

## Résultats

Mesures du 2 novembre 2026 sur un VPS à 1 vCPU, 22 sources, 1 738 articles
uniques (trois collectes) :

| | Avant | Après |
|---|---|---|
| Collecte complète | 6,3 s à 9,1 s | **1,9 s à 2,7 s** |
| Hacker News seul | 8,6 s | 1,3 s |

## Goulots d'étranglement corrigés

1. **Flux RSS lus de façon bloquante.** `feedparser.parse(url)` télécharge le
   flux de façon synchrone : appelé dans une coroutine, il bloquait toute la
   boucle d'événements. Les ~15 sources RSS étaient donc lues l'une après
   l'autre et retardaient aussi les scrapers HTTP lancés en parallèle.
   `novit.scrapers.feeds.fetch_feed` télécharge désormais le flux avec httpx,
   puis l'analyse dans un thread (`asyncio.to_thread`). Le parsing d'arXiv
   passe aussi par un thread.
2. **Items Hacker News récupérés un par un.** L'API Firebase ne renvoie qu'un
   item par requête, et 60 requêtes passaient en série. Elles sont maintenant
   envoyées 10 par 10 (`ITEM_CONCURRENCY`), dans l'ordre du classement.

## Effet de bord : sources mortes visibles

Avec `feedparser.parse(url)`, une erreur HTTP (404, 500…) donnait un flux vide
compté comme un succès à 0 article. `fetch_feed` lève l'erreur : la source
apparaît en échec dans le rapport de collecte et dans `novit_health`. C'est le
cas aujourd'hui d'un des blogs IA (404), suivi avec les redirections d'arXiv et
de roadmap.sh dans #118.
