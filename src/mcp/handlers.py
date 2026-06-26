from src.mcp.errors import NovitError, NovitErrorCode
from src.mcp.schemas import (
    GetByDomainInput,
    GetNewsInput,
    GetProfileInput,
    SearchInput,
)

PROFILE_DESCRIPTIONS = {
    "ETUDIANT": {
        "sources_prioritaires": ["hacker_news", "dev_to", "freecodecamp", "arxiv"],
        "domaines_favoris": ["ia", "dev", "formation"],
        "ton": "pédagogique et enthousiaste",
        "niveau": "accessibilité et vulgarisation",
    },
    "INGENIEUR": {
        "sources_prioritaires": [
            "github_trending",
            "cve_nvd",
            "netflix_tech",
            "google_eng",
        ],
        "domaines_favoris": ["securite", "ingenierie", "ia", "dev"],
        "ton": "professionnel et concis",
        "niveau": "expertise technique",
    },
}


async def handle_get_news(params: GetNewsInput) -> str:
    # Placeholder — implémentation réelle en M3
    domaines_str = ", ".join(params.domaines) if params.domaines else "tous les domaines"
    return (
        f"# Veille NovIT — Profil {params.profil}\n\n"
        f"**Domaines :** {domaines_str}\n"
        f"**Période :** {params.periode}\n"
        f"**Articles demandés :** {params.nb_articles}\n\n"
        f"> Les scrapers seront implémentés en M2. "
        f"Cette réponse est un placeholder fonctionnel."
    )


async def handle_search(params: SearchInput) -> str:
    # Placeholder — implémentation réelle en M3
    return (
        f"# Recherche NovIT : « {params.query} »\n\n"
        f"**Domaine :** {params.domaine or 'tous'}\n"
        f"**Source :** {params.source or 'toutes'}\n"
        f"**Page :** {params.page}/{params.per_page}\n\n"
        f"> Recherche plein texte disponible en M3."
    )


async def handle_get_by_domain(params: GetByDomainInput) -> str:
    # Placeholder — implémentation réelle en M3
    return (
        f"# Articles NovIT — Domaine : {params.domaine}\n\n"
        f"**Profil :** {params.profil or 'non défini'}\n"
        f"**Articles demandés :** {params.nb_articles}\n\n"
        f"> Filtrage par domaine disponible en M3."
    )


async def handle_get_profile(params: GetProfileInput) -> str:
    profile = PROFILE_DESCRIPTIONS.get(params.profil)
    if not profile:
        raise NovitError(
            NovitErrorCode.INVALID_PROFILE,
            f"Profil '{params.profil}' non reconnu. Profils disponibles : ETUDIANT, INGENIEUR",
        )
    sources = ", ".join(profile["sources_prioritaires"])
    domaines = ", ".join(profile["domaines_favoris"])
    return (
        f"# Profil NovIT : {params.profil}\n\n"
        f"**Ton :** {profile['ton']}\n"
        f"**Niveau :** {profile['niveau']}\n"
        f"**Sources prioritaires :** {sources}\n"
        f"**Domaines favoris :** {domaines}"
    )
