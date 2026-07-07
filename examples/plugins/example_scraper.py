"""Exemple de scraper plugin NovIT — Lobste.rs (agrégateur tech communautaire, API JSON).

Pour l'activer : copier ce fichier dans le dossier pointé par NOVIT_PLUGINS_DIR
(`plugins/` par défaut, à la racine du dépôt — voir docs/PLUGINS.md) :

    mkdir -p plugins
    cp examples/plugins/example_scraper.py plugins/

Il sera chargé automatiquement au prochain démarrage du serveur (ou via
ScraperManager.reload_sources() sans redémarrage).

Ceci illustre le cas d'un plugin "API JSON propre" — pour un simple flux RSS,
il n'y a pas besoin d'écrire de plugin : voir docs/ADDING_A_SOURCE.md (Cas 1).
"""

from datetime import datetime

import httpx
from loguru import logger

from src.scrapers.base import Article, BaseScraper

LOBSTERS_API_URL = "https://lobste.rs/hottest.json"


class LobstersScraper(BaseScraper):
    """Récupère les articles les plus populaires de Lobste.rs (API JSON publique, sans clé)."""

    name = "lobsters"
    domains = ["dev", "ingenierie"]
    profiles = ["ETUDIANT", "INGENIEUR"]

    async def fetch(self) -> list[Article]:
        logger.debug(f"[{self.name}] Requête {LOBSTERS_API_URL}")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(LOBSTERS_API_URL)
            r.raise_for_status()
            stories = r.json()

        articles: list[Article] = []
        for story in stories:
            try:
                published_at = datetime.fromisoformat(story["created_at"])
                articles.append(
                    Article(
                        title=story.get("title", ""),
                        url=story.get("url") or story.get("comments_url", ""),
                        summary=f"{story.get('score', 0)} points · "
                        f"{story.get('comment_count', 0)} commentaires",
                        published_at=published_at,
                        source=self.name,
                        domains=self.domains,
                        profiles=self.profiles,
                        score=min(story.get("score", 0) / 100, 1.0),
                        extra={"tags": story.get("tags", [])},
                    )
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Erreur story : {e}")

        logger.info(f"[{self.name}] {len(articles)} articles récupérés")
        return articles

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(LOBSTERS_API_URL)
                return r.status_code < 500
        except Exception:
            return False
