# Ajouter une nouvelle source — NovIT

Deux cas selon le type de source : **flux RSS standard** (le cas le plus courant) ou
**API/format propre** (nécessite un scraper dédié).

---

## Cas 1 — Flux RSS standard

La majorité des sources NovIT sont des flux RSS déclarés (pas de code par source). Choisir le
fichier selon la catégorie éditoriale, puis ajouter une entrée à sa liste `*_SOURCES` :

| Fichier | Catégorie | Fonction builder |
|---|---|---|
| `src/scrapers/rss.py` | Actus tech générales | `build_rss_scrapers()` (liste `RSS_SOURCES`) |
| `src/scrapers/ai_blogs.py` | Blogs IA (labos, recherche) | `build_ai_scrapers()` |
| `src/scrapers/eng_blogs.py` | Blogs d'ingénierie (tech companies) | `build_eng_scrapers()` |
| `src/scrapers/regulation.py` | Réglementation / conformité | `build_regulation_scrapers()` |
| `src/scrapers/training.py` | Formation / certifications | `build_training_scrapers()` |

```python
RssSource(
    name="mon_blog",                          # identifiant unique, snake_case
    url="https://monblog.example.com/feed",    # URL du flux RSS/Atom
    domains=["dev", "ia"],                     # domaines NovIT couverts (voir domains.yaml)
    profiles=["ETUDIANT", "INGENIEUR"],        # profils concernés
    base_score=0.5,                            # pertinence de base 0.0–1.0 (0.5 = neutre)
)
```

C'est tout : `RssScraper` (classe partagée) gère le fetch, le parsing (`feedparser`) et la
conversion en `Article`. Aucun nouveau fichier, aucune modification de `ScraperManager`.

---

## Cas 2 — Source avec API/format propre

Pour une source qui n'expose pas de flux RSS exploitable (API JSON, HTML à parser, etc.) :

### Étapes

1. **Copier le template** : `cp src/scrapers/_template.py src/scrapers/ma_source.py`
2. **Implémenter le contrat `BaseScraper`** :
   ```python
   class MaSourceScraper(BaseScraper):
       name = "ma_source"                        # identifiant unique
       domains = ["dev"]                          # domaines par défaut (le tagger peut en ajouter)
       profiles = ["ETUDIANT", "INGENIEUR"]

       async def fetch(self) -> list[Article]: ...
       async def health_check(self) -> bool: ...
   ```
   - `fetch()` ne doit **jamais lever d'exception non gérée pour un cas attendu** (ex : réponse
     vide) — `ScraperManager._run_scraper()` capture déjà les exceptions et timeouts, mais une
     source qui échoue systématiquement dégradera son `ScraperReport` en continu.
   - `health_check()` doit être rapide (< 5s) et ne pas dépendre de `fetch()`.
3. **Enregistrer le scraper** dans `ScraperManager._build_all_scrapers()`
   (`src/scrapers/manager.py`) :
   ```python
   scrapers: list[BaseScraper] = [
       HackerNewsScraper(),
       GitHubTrendingScraper(),
       CVEScraper(),
       ANSSIScraper(),
       MaSourceScraper(),   # ← ajouter ici
   ]
   ```
4. **Écrire les tests** dans `tests/test_ma_source.py`, sur le modèle de
   `tests/test_hacker_news.py` (mock HTTP avec `respx`, pas d'appel réseau réel dans les tests).

### Étapes de développement et test

```bash
# Tester le scraper isolément (appel réseau réel, pour valider le parsing) :
python -c "import asyncio; from src.scrapers.ma_source import MaSourceScraper; print(asyncio.run(MaSourceScraper().fetch()))"

# Puis tests automatisés (mockés, dans la suite CI) :
pytest tests/test_ma_source.py -v

# Vérifier que l'intégration au manager fonctionne :
pytest tests/test_integration.py -v
```

### Comment soumettre une PR

1. Créer une branche `feature/scraper-ma-source` depuis `dev` (voir
   [CONTRIBUTING.md](../CONTRIBUTING.md) pour le workflow complet).
2. Commit : `feat: ajouter le scraper ma_source (#N)`.
3. PR vers `dev`, en liant l'issue (`Closes #N`).
4. La CI (lint + tests) doit passer.

### Critères d'acceptation d'une nouvelle source

- [ ] `fetch()` et `health_check()` implémentés, typés, sans appel bloquant synchrone.
- [ ] Timeout HTTP explicite (`httpx.AsyncClient(timeout=...)`), pas de valeur par défaut infinie.
- [ ] Au moins un domaine NovIT valide déclaré (voir [ADDING_A_DOMAIN.md](ADDING_A_DOMAIN.md)
      pour la liste).
- [ ] Tests unitaires avec HTTP mocké (`respx`), couvrant : cas nominal, réponse vide,
      erreur HTTP.
- [ ] Pas de clé API en dur dans le code — passer par `config/settings.py`/`.env` si la source
      en nécessite une.
- [ ] Enregistré dans `ScraperManager._build_all_scrapers()` (cas 2 uniquement).
- [ ] `black`, `isort`, `ruff` passent (`pre-commit run --all-files`).
