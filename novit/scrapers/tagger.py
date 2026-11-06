import re
from pathlib import Path

import yaml
from loguru import logger

from novit.scrapers.base import Article
from novit.settings import config_file

_CONFIG_PATH = config_file("domains.yaml")


class DomainTagger:
    """Tague automatiquement les articles avec les domaines NovIT.

    Les règles de tagging sont chargées depuis config/domains.yaml.
    Les tags posés par les scrapers sont enrichis, jamais écrasés.
    """

    def __init__(self, config_path: Path = _CONFIG_PATH):
        self._domains: dict[str, list[str]] = {}
        self._patterns: dict[str, re.Pattern[str]] = {}
        self._load_config(config_path)

    def _load_config(self, path: Path) -> None:
        if not path.exists():
            logger.warning(f"[tagger] Config introuvable : {path}")
            return
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for domain, info in data.get("domains", {}).items():
            keywords = [kw.lower() for kw in info.get("keywords", [])]
            self._domains[domain] = keywords
            if keywords:
                self._patterns[domain] = _whole_words(keywords)
        logger.debug(f"[tagger] {len(self._domains)} domaines chargés depuis {path}")

    def tag(self, article: Article) -> Article:
        """Enrichit les domaines d'un article à partir de son titre et résumé."""
        text = (article.title + " " + article.summary).lower()
        detected = set(article.domains)

        for domain, pattern in self._patterns.items():
            if pattern.search(text):
                detected.add(domain)

        article.domains = sorted(detected)
        return article

    def tag_all(self, articles: list[Article]) -> list[Article]:
        """Tague une liste d'articles en place."""
        for article in articles:
            self.tag(article)
        return articles


def _whole_words(keywords: list[str]) -> re.Pattern[str]:
    """Motif qui trouve un des mots-clés en mot entier (#118).

    Une simple sous-chaîne collait des domaines à tort : « norme » dans
    « énorme », « legal » dans « illegally ». Les mots-clés peuvent contenir
    des symboles (« c++ », « .net ») : ils sont échappés, et la limite de mot
    est une lettre ou un chiffre de part et d'autre, pas `\\b`.
    """
    alternatives = "|".join(
        re.escape(kw) for kw in sorted(keywords, key=len, reverse=True)
    )
    return re.compile(rf"(?<![\w])(?:{alternatives})(?![\w])")


# Instance globale
tagger = DomainTagger()
