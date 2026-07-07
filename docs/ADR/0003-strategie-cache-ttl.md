# ADR-003 : Stratégie de cache — TTL en mémoire par type de contenu

**Statut :** Acceptée
**Date :** 2026-07-07 (rédigée rétroactivement)

## Contexte

Les outils MCP comme `novit_get_news` sont potentiellement appelés plusieurs fois de suite pour
la même combinaison profil/domaines/période dans une session Claude, et le scraping réseau (22
sources) est l'opération la plus lente du pipeline. Un cache est nécessaire pour éviter de
re-scraper à chaque appel, sans pour autant servir des données trop périmées pour une « veille ».

## Décision

`TTLCache` (`src/mcp/cache.py`) : cache en mémoire (process unique), clé → valeur avec
expiration individuelle, TTL différencié par type de contenu :

| Constante | Valeur | Usage |
|---|---|---|
| `TTL_NEWS` | 3600s (1h) | Résultats `novit_get_news` |
| `TTL_SEARCH` | 1800s (30min) | Résultats `novit_search` |
| `TTL_PROFILE` | 86400s (24h) | Résumés de profil |
| `TTL_HEALTH` | 60s (1min) | Statut santé |

## Alternatives considérées

- **Cache distribué (Redis)** — écartée pour l'usage local actuel : un process serveur unique
  par utilisateur ne bénéficie pas d'un cache partagé, et ajoute une dépendance d'infra à faire
  tourner. À reconsidérer si #86 (déploiement cloud) ou #87 (multi-utilisateurs) aboutissent à
  plusieurs instances de process partageant un même cache.
- **`cachetools` (déjà en dépendance)** — présent dans `requirements.txt` mais `TTLCache` est
  finalement une implémentation maison (`threading.Lock` + `dataclass CacheEntry`), plus simple
  à adapter aux besoins spécifiques (stats hit/miss exposées via `novit_health`). `cachetools`
  reste une dépendance inutilisée à ce jour — à nettoyer ou à réutiliser explicitement (#88).
- **Pas de cache, ré-scraper à chaque appel** — écartée : latence inacceptable (dizaines de
  secondes, voir `tests/test_performance.py` et le vécu direct lors des tests d'intégration où
  un scraping complet des 22 sources prend ~40s).

## Conséquences

- Le cache est **local au process** : aucune invalidation croisée entre plusieurs instances du
  serveur (non pertinent tant qu'il n'y a qu'un process par utilisateur local).
- Une donnée peut être servie jusqu'à `TTL_NEWS` (1h) après un événement réel — acceptable pour
  de la veille tech, pas pour un cas d'usage temps réel strict.
- Le cache ne survit pas à un redémarrage du serveur (en mémoire, pas persisté) — cohérent avec
  son rôle de simple évitement de re-scraping à court terme, `ArticleStore` (SQLite) restant la
  persistance de fond.
