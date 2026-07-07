from loguru import logger

from src.mcp.cache import TTL_NEWS, TTL_SEARCH, cache
from src.mcp.errors import NovitError, NovitErrorCode
from src.mcp.schemas import (
    GetByDomainInput,
    GetNewsInput,
    GetProfileInput,
    SearchInput,
)
from src.profiles.filter import filter_and_rank
from src.profiles.profile import get_profile
from src.scrapers.manager import ScraperManager
from src.scrapers.storage import store
from src.scrapers.tagger import tagger

_manager = ScraperManager()

PERIODE_TO_HOURS = {"1h": 1, "6h": 6, "24h": 24, "7j": 168}


def _format_articles(articles: list, profil: str, titre: str) -> str:
    if not articles:
        return f"# {titre}\n\nAucun article trouvé pour le profil {profil} avec ces critères."

    lines = [f"# {titre}", f"**{len(articles)} article(s)** · Profil {profil}\n"]
    for i, article in enumerate(articles, 1):
        pub = (
            article.published_at.strftime("%d/%m à %H:%M")
            if article.published_at
            else ""
        )
        domains = ", ".join(article.domains) if article.domains else "—"
        lines.append(f"### {i}. {article.title}")
        lines.append(f"🔗 {article.url}")
        lines.append(f"📅 {pub} · 🏷 {domains} · 📰 {article.source}")
        if article.summary:
            lines.append(f"\n{article.summary[:300]}")
        lines.append("")
    return "\n".join(lines)


async def handle_get_news(params: GetNewsInput) -> str:
    profile = get_profile(params.profil)
    hours = PERIODE_TO_HOURS.get(params.periode, 24)
    cache_key = (
        f"news:{params.profil}:{':'.join(sorted(params.domaines))}:{params.periode}"
    )

    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Cache hit : {cache_key}")
        return cached

    # 1. Récupérer depuis le stockage
    articles = await store.get_recent(
        domains=params.domaines or None,
        profiles=[params.profil],
        hours=hours,
        limit=params.nb_articles * 3,
    )

    # 2. Si pas assez d'articles en base, lancer les scrapers
    if len(articles) < params.nb_articles:
        logger.info(
            f"Pas assez d'articles en cache ({len(articles)}), lancement des scrapers"
        )
        try:
            if params.domaines:
                result = await _manager.fetch_by_domains(params.domaines)
            else:
                result = await _manager.fetch_all()
            fresh = tagger.tag_all(result.articles)
            await store.save(fresh)
            articles = await store.get_recent(
                domains=params.domaines or None,
                profiles=[params.profil],
                hours=hours,
                limit=params.nb_articles * 3,
            )
        except Exception as e:
            logger.error(f"Erreur scraping : {e}")
            if not articles:
                raise NovitError(
                    NovitErrorCode.SOURCE_UNAVAILABLE,
                    "Impossible de récupérer les articles. Réessayez dans quelques instants.",
                )

    # 3. Filtrer et scorer par profil
    ranked = filter_and_rank(
        articles, profile, domains=params.domaines or None, limit=params.nb_articles
    )

    domaines_str = (
        ", ".join(params.domaines) if params.domaines else "tous les domaines"
    )
    titre = f"Veille NovIT — {params.periode} · {domaines_str}"
    result_text = _format_articles(ranked, params.profil, titre)

    cache.set(cache_key, result_text, ttl=TTL_NEWS)
    return result_text


async def handle_search(params: SearchInput) -> str:
    cache_key = f"search:{params.query}:{params.domaine}:{params.source}:{params.page}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    articles = await store.search(params.query, limit=params.per_page * params.page)

    if params.domaine:
        articles = [a for a in articles if params.domaine in a.domains]
    if params.source:
        articles = [a for a in articles if a.source == params.source]
    if params.profil:
        articles = [a for a in articles if params.profil in a.profiles]

    start = (params.page - 1) * params.per_page
    page_articles = articles[start : start + params.per_page]
    total = len(articles)

    if not page_articles:
        return f"# Recherche NovIT : « {params.query} »\n\nAucun résultat trouvé."

    lines = [
        f"# Recherche : « {params.query} »",
        f"**{total} résultat(s)** · Page {params.page}\n",
    ]
    for i, article in enumerate(page_articles, start + 1):
        pub = article.published_at.strftime("%d/%m") if article.published_at else ""
        lines.append(f"### {i}. {article.title}")
        lines.append(f"🔗 {article.url}  · 📅 {pub} · 📰 {article.source}")
        if article.summary:
            lines.append(f"{article.summary[:200]}")
        lines.append("")

    result_text = "\n".join(lines)
    cache.set(cache_key, result_text, ttl=TTL_SEARCH)
    return result_text


async def handle_get_by_domain(params: GetByDomainInput) -> str:
    profil_name = params.profil or "INGENIEUR"
    profile = get_profile(profil_name)
    articles = await store.get_recent(
        domains=[params.domaine],
        profiles=[profil_name],
        hours=24,
        limit=params.nb_articles * 2,
    )
    if not articles and not cache.get(f"scraped:{params.domaine}"):
        result = await _manager.fetch_by_domains([params.domaine])
        fresh = tagger.tag_all(result.articles)
        await store.save(fresh)
        cache.set(f"scraped:{params.domaine}", True, ttl=TTL_NEWS)
        articles = await store.get_recent(
            domains=[params.domaine],
            profiles=[profil_name],
            hours=24,
            limit=params.nb_articles * 2,
        )

    ranked = filter_and_rank(
        articles, profile, domains=[params.domaine], limit=params.nb_articles
    )
    return _format_articles(ranked, profil_name, f"Domaine : {params.domaine}")


async def handle_get_profile(params: GetProfileInput) -> str:
    try:
        profile = get_profile(params.profil)
        return f"# Profil NovIT : {params.profil}\n\n{profile.to_summary()}"
    except ValueError as e:
        raise NovitError(NovitErrorCode.INVALID_PROFILE, str(e))
