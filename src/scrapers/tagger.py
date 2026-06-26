from pathlib import Path

import yaml
from loguru import logger

from src.scrapers.base import Article

_CONFIG_PATH = Path("config/domains.yaml")


class DomainTagger:
    """Tague automatiquement les articles avec les domaines NovIT.

    Les règles de tagging sont chargées depuis config/domains.yaml.
    Les tags posés par les scrapers sont enrichis, jamais écrasés.
    """

    def __init__(self, config_path: Path = _CONFIG_PATH):
        self._domains: dict[str, list[str]] = {}
        self._load_config(config_path)

    def _load_config(self, path: Path) -> None:
        if not path.exists():
            logger.warning(f"[tagger] Config introuvable : {path}")
            return
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for domain, info in data.get("domains", {}).items():
            self._domains[domain] = [kw.lower() for kw in info.get("keywords", [])]
        logger.debug(f"[tagger] {len(self._domains)} domaines chargés depuis {path}")

    def tag(self, article: Article) -> Article:
        """Enrichit les domaines d'un article à partir de son titre et résumé."""
        text = (article.title + " " + article.summary).lower()
        detected = set(article.domains)

        for domain, keywords in self._domains.items():
            if any(kw in text for kw in keywords):
                detected.add(domain)

        article.domains = sorted(detected)
        return article

    def tag_all(self, articles: list[Article]) -> list[Article]:
        """Tague une liste d'articles en place."""
        for article in articles:
            self.tag(article)
        return articles


# Instance globale
tagger = DomainTagger()
