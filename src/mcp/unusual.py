import random

from src.scrapers.base import Article
from src.scrapers.storage import store

_UNUSUAL_SOURCES = {"arxiv", "papers_with_code", "mit_tech_review", "roadmap_sh", "w3c_news"}
_AVOID_DOMAINS = {"securite"}


def _surprise_score(article: Article) -> float:
    """Score de 'surprise' : contenu potentiellement riche mais peu populaire.

    Favorise les sources académiques/alternatives et pénalise les scores élevés
    (un article très populaire est déjà connu — on veut ce qui passe sous le radar).
    """
    source_bonus = 0.3 if article.source in _UNUSUAL_SOURCES else 0.0
    domain_penalty = -0.2 if any(d in _AVOID_DOMAINS for d in article.domains) else 0.0
    # Score inversé : un article peu populaire (score bas) est plus "insolite"
    rarity = 1.0 - min(article.score, 1.0)
    content_bonus = 0.2 if len(article.summary) > 200 else 0.0
    return rarity + source_bonus + domain_penalty + content_bonus


async def get_unusual(count: int = 3) -> str:
    """Sélectionne des articles hors des sentiers battus pour le profil ETUDIANT.

    Ciblé sur du contenu riche, peu populaire, issu de sources alternatives.
    """
    candidates = await store.get_recent(
        profiles=["ETUDIANT"],
        hours=168,
        limit=300,
    )

    # Filtrer les articles trop mainstream (score élevé = déjà connu)
    candidates = [a for a in candidates if a.score < 0.7 and len(a.summary) > 50]

    if not candidates:
        return "Pas assez d'articles en base pour le mode insolite. Lancez une veille d'abord."

    # Scorer et trier
    scored = sorted(candidates, key=_surprise_score, reverse=True)

    # Ajouter un peu d'aléatoire dans le top 30 pour varier
    pool = scored[:30]
    selected = random.sample(pool, min(count, len(pool)))

    lines = ["# 💡 Nouveautés insolites NovIT", "_Des articles hors des sentiers battus…_\n"]
    for i, article in enumerate(selected, 1):
        pub = article.published_at.strftime("%d/%m") if article.published_at else ""
        domains = ", ".join(article.domains) if article.domains else "—"
        lines.append(f"### {i}. {article.title}")
        lines.append(f"🔗 {article.url}  · 📰 {article.source} · 📅 {pub} · 🏷 {domains}")
        if article.summary:
            lines.append(f"\n_{article.summary[:200]}_")
        lines.append("")

    return "\n".join(lines)
