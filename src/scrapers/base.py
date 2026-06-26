from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    title: str
    url: str
    summary: str
    published_at: datetime
    source: str
    domains: list[str] = field(default_factory=list)
    profiles: list[str] = field(default_factory=list)
    score: float = 0.0
    extra: dict = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.url)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Article):
            return NotImplemented
        return self.url == other.url


class BaseScraper(ABC):
    """Contrat commun à tous les scrapers NovIT.

    Chaque source implémente fetch() et health_check().
    Le ScraperManager appelle ces méthodes de manière uniforme.
    """

    name: str = "base"
    domains: list[str] = []
    profiles: list[str] = ["ETUDIANT", "INGENIEUR"]

    @abstractmethod
    async def fetch(self) -> list[Article]:
        """Récupère et retourne les articles depuis la source."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Vérifie que la source est accessible. Retourne True si OK."""
