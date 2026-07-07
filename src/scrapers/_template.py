"""Template de scraper — copier ce fichier pour ajouter une nouvelle source
avec une API/format propre (pas un simple flux RSS — pour un flux RSS, voir
docs/ADDING_A_SOURCE.md, il suffit d'ajouter une entrée à RSS_SOURCES).

Étapes : voir docs/ADDING_A_SOURCE.md pour le guide complet.
1. Copier ce fichier : cp _template.py ma_source.py
2. Renommer la classe et remplir name, domains, profiles
3. Implémenter fetch() et health_check()
4. Enregistrer le scraper dans ScraperManager._build_all_scrapers() (src/scrapers/manager.py)
5. Écrire les tests dans tests/test_ma_source.py
"""

import httpx
from loguru import logger

from src.scrapers.base import Article, BaseScraper


class TemplateScraper(BaseScraper):
    name = "template"
    domains = ["dev"]
    profiles = ["ETUDIANT", "INGENIEUR"]

    BASE_URL = "https://example.com"

    async def fetch(self) -> list[Article]:
        logger.debug(f"[{self.name}] fetch() démarré")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.BASE_URL)
            response.raise_for_status()
        # Parser la réponse ici et retourner une liste d'Article
        return []

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.head(self.BASE_URL)
                return r.status_code < 500
        except Exception:
            return False
