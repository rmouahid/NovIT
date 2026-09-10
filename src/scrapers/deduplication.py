import hashlib
import re
from datetime import UTC, datetime, timedelta

from loguru import logger

from src.scrapers.base import Article


def _normalize(text: str) -> str:
    """Normalise un titre pour la comparaison : minuscules, sans ponctuation ni articles."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(
        r"\b(the|a|an|le|la|les|un|une|des|de|du|and|or|is|in|on|at|to|for|of|now|new|today)\b",
        "",
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def _title_hash(title: str) -> str:
    normalized = _normalize(title)
    return hashlib.md5(normalized.encode()).hexdigest()


def _jaccard_similarity(a: str, b: str) -> float:
    """Similarité de Jaccard entre deux titres normalisés (ensembles de mots)."""
    set_a = set(_normalize(a).split())
    set_b = set(_normalize(b).split())
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


class Deduplicator:
    """Déduplication des articles par URL exacte et par similarité de titre.

    Maintient un index en mémoire sur une fenêtre temporelle configurable.
    La comparaison fuzzy utilise la similarité de Jaccard sur les titres normalisés.
    """

    def __init__(self, window_hours: int = 24, similarity_threshold: float = 0.7):
        self.window = timedelta(hours=window_hours)
        self.threshold = similarity_threshold
        self._url_index: dict[str, datetime] = {}
        self._title_index: dict[str, tuple[str, datetime]] = {}

    def _prune_expired(self) -> None:
        """Supprime les entrées expirées de l'index."""
        cutoff = datetime.now(tz=UTC) - self.window
        self._url_index = {k: v for k, v in self._url_index.items() if v > cutoff}
        self._title_index = {
            k: v for k, v in self._title_index.items() if v[1] > cutoff
        }

    def is_duplicate(self, article: Article) -> bool:
        """Retourne True si l'article est un doublon (URL ou titre similaire)."""
        self._prune_expired()

        # 1. Déduplication par URL exacte
        if article.url in self._url_index:
            return True

        # 2. Déduplication par hash de titre normalisé
        title_h = _title_hash(article.title)
        if title_h in self._title_index:
            return True

        # 3. Similarité de Jaccard avec les titres connus
        for stored_title, (_, _) in self._title_index.items():
            sim = _jaccard_similarity(article.title, stored_title)
            if sim >= self.threshold:
                logger.debug(f"Doublon fuzzy ({sim:.2f}) : '{article.title[:50]}'")
                return True

        return False

    def register(self, article: Article) -> None:
        """Enregistre un article dans l'index."""
        now = datetime.now(tz=UTC)
        self._url_index[article.url] = now
        self._title_index[article.title] = (article.url, now)

    def deduplicate(self, articles: list[Article]) -> list[Article]:
        """Filtre une liste d'articles et supprime les doublons."""
        unique: list[Article] = []
        for article in articles:
            if not self.is_duplicate(article):
                self.register(article)
                unique.append(article)
        removed = len(articles) - len(unique)
        if removed:
            logger.info(
                f"Déduplication : {removed} doublon(s) supprimé(s) sur {len(articles)}"
            )
        return unique


# Instance globale (fenêtre 24h, seuil 70%)
deduplicator = Deduplicator(window_hours=24, similarity_threshold=0.7)
