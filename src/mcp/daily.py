from datetime import datetime, timezone

from src.profiles.filter import filter_and_rank
from src.profiles.profile import Profile
from src.scrapers.base import Article
from src.scrapers.storage import store

_TOP_PER_DOMAIN = 3
_MAX_DOMAINS = 6


async def build_daily_summary(profile: Profile, domaines: list[str] | None = None) -> str:
    """Construit le résumé de veille quotidien pour un profil donné.

    Sélectionne les meilleurs articles des dernières 24h, groupés par domaine.
    """
    active_domains = domaines or profile.domaines_favoris or ["ia", "dev", "securite"]

    all_articles = await store.get_recent(
        domains=active_domains,
        profiles=[profile.name],
        hours=24,
        limit=200,
    )

    now = datetime.now(tz=timezone.utc)
    date_str = now.strftime("%A %d %B %Y").capitalize()

    lines = [
        f"# Veille quotidienne NovIT",
        f"**{date_str}** · Profil {profile.name}\n",
    ]

    total = 0
    for domain in active_domains[:_MAX_DOMAINS]:
        domain_articles = [a for a in all_articles if domain in a.domains]
        top = filter_and_rank(domain_articles, profile, domains=[domain], limit=_TOP_PER_DOMAIN)
        if not top:
            continue

        domain_labels = {
            "ia": "🤖 Intelligence Artificielle",
            "securite": "🔐 Cybersécurité",
            "dev": "💻 Développement",
            "ingenierie": "⚙️ Ingénierie",
            "reglementation": "📜 Réglementation",
            "formation": "📚 Formation",
        }
        label = domain_labels.get(domain, domain.capitalize())
        lines.append(f"## {label}")

        for article in top:
            pub = article.published_at.strftime("%H:%M") if article.published_at else ""
            lines.append(f"- **[{article.title}]({article.url})** · {article.source} · {pub}")
            if article.summary:
                lines.append(f"  _{article.summary[:120]}_")
        lines.append("")
        total += len(top)

    if total == 0:
        lines.append("Aucun article disponible pour aujourd'hui. Relancez dans quelques instants pour récupérer les dernières actualités.")
    else:
        lines.append(f"---\n_{total} articles sélectionnés · Generé à {now.strftime('%H:%M')} UTC_")

    return "\n".join(lines)
