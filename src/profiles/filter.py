from src.profiles.profile import Profile
from src.scrapers.base import Article


def score_article(article: Article, profile: Profile) -> float:
    """Calcule le score de pertinence d'un article pour un profil donné.

    Score final = score de base * poids source * max(poids domaines)
    """
    source_w = profile.source_weight(article.source)
    domain_w = max((profile.domain_weight(d) for d in article.domains), default=0.6)
    return round(article.score * source_w * domain_w, 4)


def filter_and_rank(
    articles: list[Article],
    profile: Profile,
    domains: list[str] | None = None,
    limit: int | None = None,
) -> list[Article]:
    """Filtre et trie les articles selon le profil.

    1. Filtre par domaines si spécifiés
    2. Filtre par profil cible (article.profiles)
    3. Filtre par score minimum du profil
    4. Score et tri décroissant
    5. Limite au nombre demandé
    """
    filtered = articles

    # Filtre par domaine demandé
    if domains:
        filtered = [a for a in filtered if any(d in a.domains for d in domains)]

    # Filtre par profil cible déclaré par le scraper
    filtered = [a for a in filtered if profile.name in a.profiles]

    # Calcul du score pondéré par profil et filtrage par score minimum
    scored: list[tuple[float, Article]] = []
    for article in filtered:
        s = score_article(article, profile)
        if s >= profile.score_min:
            scored.append((s, article))

    # Tri décroissant par score
    scored.sort(key=lambda x: x[0], reverse=True)

    result = [article for _, article in scored]

    if limit:
        result = result[:limit]

    return result
