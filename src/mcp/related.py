from datetime import UTC, datetime

from src.scrapers.base import Article
from src.scrapers.storage import store


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _title_tokens(title: str) -> set[str]:
    stop = {
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "to",
        "for",
        "and",
        "or",
        "is",
        "with",
        "de",
        "le",
        "la",
        "les",
        "un",
        "une",
    }
    return {w.lower() for w in title.split() if len(w) > 2 and w.lower() not in stop}


def _similarity(article: Article, candidate: Article) -> float:
    """Score de similarité entre deux articles (0.0 – 1.0)."""
    # Similarité de domaines (Jaccard)
    domain_sim = _jaccard(set(article.domains), set(candidate.domains))

    # Similarité de titre (Jaccard sur les mots significatifs)
    title_sim = _jaccard(_title_tokens(article.title), _title_tokens(candidate.title))

    return 0.6 * domain_sim + 0.4 * title_sim


async def find_related(url: str, title: str, domains: list[str], top_k: int = 5) -> str:
    """Trouve les articles similaires à un article cible dans le store NovIT.

    Critères de similarité :
    - Jaccard sur les domaines (poids 60 %)
    - Jaccard sur les mots du titre (poids 40 %)
    """
    candidates = await store.get_recent(domains=domains or None, hours=168, limit=200)

    scored: list[tuple[float, Article]] = []
    ref = Article(
        title=title,
        url=url,
        summary="",
        published_at=datetime.now(tz=UTC),
        source="",
        domains=domains,
    )

    for candidate in candidates:
        if candidate.url == url:
            continue
        sim = _similarity(ref, candidate)
        if sim > 0.1:
            scored.append((sim, candidate))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    if not top:
        return f"Aucun article similaire trouvé dans les 7 derniers jours pour les domaines : {', '.join(domains)}."

    lines = [f"# Articles similaires à « {title[:60]} »\n"]
    for rank, (sim, article) in enumerate(top, 1):
        pub = article.published_at.strftime("%d/%m") if article.published_at else ""
        lines.append(f"### {rank}. {article.title}")
        lines.append(
            f"🔗 {article.url}  · 📅 {pub} · 📰 {article.source}  · similarité {sim:.0%}"
        )
        if article.summary:
            lines.append(article.summary[:150])
        lines.append("")

    return "\n".join(lines)
