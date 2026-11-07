from loguru import logger

from novit.mcp.cache import TTL_NEWS, TTL_SEARCH, cache
from novit.mcp.errors import NovitError, NovitErrorCode
from novit.mcp.offline import TTL_OFFLINE, all_sources_down, offline_banner, retry
from novit.mcp.schemas import (
    ArticlesText,
    GetByDomainInput,
    GetNewsInput,
    GetProfileInput,
    SearchInput,
)
from novit.profiles.filter import filter_and_rank
from novit.profiles.profile import get_profile
from novit.scrapers.manager import ScraperManager
from novit.scrapers.storage import store
from novit.scrapers.tagger import tagger

_manager = ScraperManager()

PERIODE_TO_HOURS = {"1h": 1, "6h": 6, "24h": 24, "7j": 168}


async def _collect(domains: list[str] | None) -> bool:
    """Lance les scrapers (tous, ou ceux des domaines) et enregistre les
    articles. Renvoie False si aucune source n'a répondu."""
    if domains:
        result = await _manager.fetch_by_domains(domains)
    else:
        result = await _manager.fetch_all()
    if all_sources_down(result):
        return False
    await store.save(tagger.tag_all(result.articles))
    return True


async def _offline_articles(
    domains: list[str] | None, profil: str, limit: int
) -> tuple[list, str]:
    """Articles servis quand aucune source ne répond : tout ce qui reste en
    base (fenêtre de rétention), avec le bandeau hors-ligne. Lance une
    relance en arrière-plan. Lève SOURCE_UNAVAILABLE si la base est vide."""
    articles = await store.get_recent(
        domains=domains,
        profiles=[profil],
        hours=store.retention_days * 24,
        limit=limit,
    )
    if not articles:
        raise NovitError(
            NovitErrorCode.SOURCE_UNAVAILABLE,
            "Impossible de récupérer les articles. Réessayez dans quelques instants.",
        )
    retry.schedule(lambda: _collect(domains))
    banner = offline_banner(await store.last_inserted_at(), retrying=retry.running)
    return articles, banner


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


async def handle_get_news(params: GetNewsInput) -> ArticlesText:
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
    banner = ""
    if len(articles) < params.nb_articles:
        logger.info(
            f"Pas assez d'articles en cache ({len(articles)}), lancement des scrapers"
        )
        try:
            online = await _collect(params.domaines or None)
        except Exception as e:
            logger.error(f"Erreur scraping : {e}")
            online = False
        if online:
            articles = await store.get_recent(
                domains=params.domaines or None,
                profiles=[params.profil],
                hours=hours,
                limit=params.nb_articles * 3,
            )
        else:
            # Mode hors-ligne : aucune source n'a répondu (#91)
            logger.warning("Aucune source disponible : réponse servie depuis le cache")
            articles, banner = await _offline_articles(
                params.domaines or None, params.profil, params.nb_articles * 3
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
    if banner:
        result_text = f"{banner}\n\n{result_text}"
    result = ArticlesText(result_text, ranked, offline=bool(banner))

    cache.set(cache_key, result, ttl=TTL_OFFLINE if banner else TTL_NEWS)
    return result


async def handle_search(params: SearchInput) -> ArticlesText:
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
        return ArticlesText(
            f"# Recherche NovIT : « {params.query} »\n\nAucun résultat trouvé.", []
        )

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

    result = ArticlesText("\n".join(lines), page_articles)
    cache.set(cache_key, result, ttl=TTL_SEARCH)
    return result


async def handle_get_by_domain(params: GetByDomainInput) -> ArticlesText:
    profil_name = params.profil or "INGENIEUR"
    profile = get_profile(profil_name)
    articles = await store.get_recent(
        domains=[params.domaine],
        profiles=[profil_name],
        hours=24,
        limit=params.nb_articles * 2,
    )
    banner = ""
    if not articles and not cache.get(f"scraped:{params.domaine}"):
        try:
            online = await _collect([params.domaine])
        except Exception as e:
            logger.error(f"Erreur scraping : {e}")
            online = False
        if online:
            cache.set(f"scraped:{params.domaine}", True, ttl=TTL_NEWS)
            articles = await store.get_recent(
                domains=[params.domaine],
                profiles=[profil_name],
                hours=24,
                limit=params.nb_articles * 2,
            )
        else:
            articles, banner = await _offline_articles(
                [params.domaine], profil_name, params.nb_articles * 2
            )

    ranked = filter_and_rank(
        articles, profile, domains=[params.domaine], limit=params.nb_articles
    )
    result_text = _format_articles(ranked, profil_name, f"Domaine : {params.domaine}")
    if banner:
        result_text = f"{banner}\n\n{result_text}"
    return ArticlesText(result_text, ranked, offline=bool(banner))


async def handle_get_profile(params: GetProfileInput) -> str:
    try:
        profile = get_profile(params.profil)
        return f"# Profil NovIT : {params.profil}\n\n{profile.to_summary()}"
    except ValueError as e:
        raise NovitError(NovitErrorCode.INVALID_PROFILE, str(e))
