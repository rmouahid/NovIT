from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GetNewsInput(BaseModel):
    profil: Literal["ETUDIANT", "INGENIEUR"]
    domaines: list[str] = Field(default_factory=list)
    nb_articles: int = Field(default=10, ge=1, le=50)
    periode: Literal["1h", "6h", "24h", "7j"] = "24h"


class SearchInput(BaseModel):
    query: str = Field(min_length=1)
    domaine: str | None = None
    source: str | None = None
    profil: Literal["ETUDIANT", "INGENIEUR"] | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=50)


class GetByDomainInput(BaseModel):
    domaine: str
    profil: Literal["ETUDIANT", "INGENIEUR"] | None = None
    nb_articles: int = Field(default=10, ge=1, le=50)


class GetProfileInput(BaseModel):
    profil: Literal["ETUDIANT", "INGENIEUR"]


class ArticleResult(BaseModel):
    title: str
    url: str
    summary: str
    published_at: datetime
    source: str
    domains: list[str]
    score: float


ARTICLES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "source": {"type": "string"},
                    "published_at": {
                        "type": ["string", "null"],
                        "description": "Date ISO 8601 avec fuseau",
                    },
                    "domains": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "score": {"type": "number"},
                },
                "required": ["title", "url", "source", "published_at", "domains"],
            },
        },
        "offline": {
            "type": "boolean",
            "description": "Vrai si aucune source n'a répondu : articles servis depuis la base",
        },
    },
    "required": ["articles", "offline"],
}


class ArticlesText(str):
    """Réponse Markdown d'un outil d'articles, qui garde les articles affichés
    pour le contenu structuré (`structuredContent`) du résultat MCP.

    Reste une `str` : le cache, les tests et les appelants qui ne lisent que
    le texte n'ont rien à changer.
    """

    articles: list[dict]
    offline: bool

    def __new__(cls, text: str, articles: list, offline: bool = False):
        value = super().__new__(cls, text)
        value.articles = [_article_data(a) for a in articles]
        value.offline = offline
        return value

    def structured(self) -> dict:
        return {"articles": self.articles, "offline": self.offline}


def _article_data(article) -> dict:
    published = article.published_at.isoformat() if article.published_at else None
    return {
        "title": article.title,
        "url": article.url,
        "source": article.source,
        "published_at": published,
        "domains": list(article.domains),
        "summary": article.summary or "",
        "score": float(article.score),
    }
