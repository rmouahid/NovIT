import importlib.util
import inspect
from pathlib import Path

from loguru import logger

from src.scrapers.base import BaseScraper


def discover_plugin_scrapers(plugins_dir: Path | str = "plugins") -> list[BaseScraper]:
    """Charge dynamiquement les scrapers externes déposés dans `plugins_dir`.

    Contrat : chaque fichier `*.py` du dossier (hors fichiers commençant par
    `_`) peut définir une ou plusieurs classes héritant de BaseScraper. Elles
    sont instanciées sans argument — un plugin qui nécessite une
    configuration doit la lire lui-même (variables d'environnement, fichier
    dédié), pas via le constructeur.

    Isolation : un plugin qui échoue à l'import ou à l'instanciation est
    ignoré avec un log d'erreur, sans faire échouer le démarrage du serveur
    ni les autres plugins — du code externe ne doit jamais pouvoir casser le
    cœur de NovIT. Voir docs/PLUGINS.md pour le guide complet.
    """
    plugins_dir = Path(plugins_dir)
    if not plugins_dir.is_dir():
        logger.debug(f"[plugins] Dossier absent, aucun plugin chargé : {plugins_dir}")
        return []

    scrapers: list[BaseScraper] = []

    for py_file in sorted(plugins_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        module_name = f"novit_plugin_{py_file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Impossible de charger le module depuis {py_file}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            logger.error(f"[plugins] Échec de chargement de {py_file.name} : {e}")
            continue

        found_in_file = 0
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseScraper)
                and obj is not BaseScraper
                and obj.__module__ == module_name
            ):
                try:
                    scrapers.append(obj())
                    found_in_file += 1
                except Exception as e:
                    logger.error(
                        f"[plugins] Échec d'instanciation de {obj.__name__} "
                        f"({py_file.name}) : {e}"
                    )

        if found_in_file:
            logger.info(
                f"[plugins] {found_in_file} scraper(s) chargé(s) depuis {py_file.name}"
            )
        else:
            logger.warning(
                f"[plugins] Aucune classe BaseScraper trouvée dans {py_file.name}"
            )

    return scrapers
