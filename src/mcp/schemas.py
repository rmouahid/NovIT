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
