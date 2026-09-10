# Rotation des secrets — NovIT

Procédure pour renouveler une clé API ou un secret NovIT **sans redémarrer le serveur**, et
comment vérifier que le service continue de fonctionner pendant l'opération.

---

## Secrets concernés

| Secret | Utilisé par | Optionnel ? |
|---|---|---|
| `NVD_API_KEY` | `CVEScraper` (`src/scrapers/cve.py`) — augmente le rate limit NVD (50 req/30s au lieu de 5) | Oui — fonctionne sans, juste plus lentement |
| `GITHUB_TOKEN` | Réservé pour un futur usage de l'API GitHub (le scraper `GitHubTrendingScraper` actuel scrape la page HTML, pas l'API) | Oui, non consommé actuellement |
| `SENTRY_DSN` | Monitoring d'erreurs (`src/mcp/sentry_config.py`) | Oui — désactive Sentry si absent |

Ces secrets vivent dans `.env` (jamais committé — voir `.env.example` pour le nom exact des
variables) ou dans le gestionnaire de secrets de l'environnement de déploiement.

---

## Procédure de rotation

1. **Générer la nouvelle clé** chez le fournisseur (NVD, GitHub, Sentry) **sans révoquer
   l'ancienne immédiatement** — les deux doivent être valides pendant la bascule.
2. **Mettre à jour la valeur** : éditer `.env` (dev) ou la variable d'environnement / le secret
   manager du déploiement (prod), puis recharger la configuration :
   ```python
   from config.settings import reload_settings
   reload_settings()   # invalide le cache lru_cache de get_settings() et relit .env/l'env
   ```
   En pratique : ce reload peut être déclenché depuis un shell Python attaché au processus, ou
   intégré à un futur outil d'admin — aucun mécanisme HTTP/MCP dédié n'existe à ce jour (pas de
   surface d'attaque supplémentaire exposée à Claude).
3. **Vérifier la prise en compte** sans redémarrage : le prochain appel de `CVEScraper.fetch()`
   lit `get_settings().nvd_api_key` à chaque exécution (pas de valeur mise en cache sur
   l'instance du scraper) — la nouvelle clé est donc utilisée dès le scrape suivant, typiquement
   dans l'heure (`TTL_NEWS`) ou immédiatement via `novit_get_news` si le cache est vide.
4. **Révoquer l'ancienne clé** chez le fournisseur une fois la nouvelle confirmée fonctionnelle
   (logs sans erreur 401/403 sur `cve_nvd`).

## Continuité de service pendant la rotation

- Aucune interruption : `reload_settings()` ne touche ni au `TTLCache`, ni à `ArticleStore`, ni
  aux connexions en cours — seul le singleton `Settings` est reconstruit.
- Si la nouvelle clé est invalide (typo, pas encore active côté fournisseur), `CVEScraper.fetch()`
  échoue proprement : `ScraperManager._run_scraper()` capture l'exception, la source apparaît
  dans `sources_failed`, mais **les autres sources continuent de fonctionner** — pas de panne
  globale (voir `tests/test_integration.py::TestScraperManagerIntegration`). NVD étant optionnel,
  `fetch()` fonctionne aussi avec `apiKey` absent (rate limit réduit).
- Voir `tests/test_secret_rotation.py` pour le test automatisé de ce scénario.

## Secrets applicatifs (hors clés API fournisseur)

`.env` n'est jamais committé (`.gitignore`) et `detect-secrets` (hook pre-commit, baseline
`.secrets.baseline`) bloque toute clé qui se retrouverait accidentellement dans un commit. En
cas de fuite avérée d'un secret dans l'historique git, la rotation ci-dessus ne suffit pas :
suivre la procédure de purge d'historique de GitHub en plus de la révocation côté fournisseur.
