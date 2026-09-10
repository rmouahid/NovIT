# Système de plugins de scrapers — NovIT

Ajouter une source **sans modifier le dépôt NovIT** : un plugin est un fichier Python déposé
dans un dossier local, chargé dynamiquement au démarrage du serveur.

À utiliser quand une source ne convient pas au [guide standard d'ajout de source](ADDING_A_SOURCE.md)
(RSS déclaratif dans `config/sources.yaml`, ou PR de scraper dans le dépôt) — par exemple une
source privée/interne, une expérimentation, ou un scraper que vous ne souhaitez pas contribuer
en amont.

---

## Contrat d'interface

Un plugin est une classe Python qui hérite de `BaseScraper` (`src/scrapers/base.py`) :

```python
from src.scrapers.base import Article, BaseScraper

class MonScraper(BaseScraper):
    name = "mon_scraper"                     # identifiant unique
    domains = ["dev"]                        # domaines NovIT (voir config/domains.yaml)
    profiles = ["ETUDIANT", "INGENIEUR"]      # profils concernés

    async def fetch(self) -> list[Article]:
        ...  # retourne la liste des articles récupérés

    async def health_check(self) -> bool:
        ...  # True si la source est joignable
```

**Contraintes :**
- La classe doit être **instanciable sans argument** — `MonScraper()`. Une configuration
  spécifique (URL, clé API) doit être lue par le plugin lui-même (variable d'environnement,
  fichier dédié), pas passée au constructeur.
- Un fichier peut définir plusieurs classes `BaseScraper` — toutes sont chargées.
- `fetch()` et `health_check()` doivent respecter les mêmes règles que n'importe quel scraper
  NovIT : timeout HTTP explicite, pas d'exception non gérée pour un cas attendu (réponse vide,
  erreur réseau) — voir [ADDING_A_SOURCE.md](ADDING_A_SOURCE.md#critères-dacceptation-dune-nouvelle-source).

## Activer un plugin

```bash
mkdir -p plugins
cp examples/plugins/example_scraper.py plugins/
```

Au prochain démarrage du serveur (ou immédiatement via un rechargement — voir plus bas), le
scraper est ajouté à `ScraperManager` au même titre que les scrapers intégrés.

Le dossier scanné est configurable via `NOVIT_PLUGINS_DIR` (défaut : `plugins/` à la racine du
dépôt). `plugins/` est dans `.gitignore` — les plugins locaux ne sont pas versionnés avec le
dépôt NovIT.

## Chargement dynamique

`discover_plugin_scrapers()` (`src/scrapers/plugins.py`) scanne `NOVIT_PLUGINS_DIR` à chaque
appel (pas de cache) :

- Chaque fichier `*.py` non préfixé par `_` est importé dynamiquement (`importlib`).
- Toute classe `BaseScraper` définie dans ce fichier est instanciée et ajoutée.
- **Isolation des pannes :** un plugin qui échoue à l'import (erreur de syntaxe, dépendance
  manquante) ou à l'instanciation est ignoré avec un log d'erreur — il ne bloque ni le
  démarrage du serveur, ni le chargement des autres plugins, ni le fonctionnement des scrapers
  intégrés. Du code externe ne doit jamais pouvoir casser le cœur de NovIT.

### Recharger sans redémarrer

Comme pour `config/sources.yaml` (#84), `ScraperManager.reload_sources()` re-scanne le dossier
de plugins en plus des sources déclaratives — déposer/retirer un fichier dans `plugins/` puis
appeler `reload_sources()` prend effet sans redémarrer le serveur.

## Exemple fourni

[`examples/plugins/example_scraper.py`](../examples/plugins/example_scraper.py) : scraper
Lobste.rs (agrégateur communautaire tech, API JSON publique sans clé), pleinement fonctionnel —
pas un squelette vide. Testé dans `tests/test_plugins.py::TestExamplePlugin`.

## Sécurité

Un plugin s'exécute avec les mêmes permissions que le serveur NovIT (accès réseau, système de
fichiers). Ne déposer que du code de confiance dans `NOVIT_PLUGINS_DIR` — le chargement
dynamique n'applique aucun bac à sable.
