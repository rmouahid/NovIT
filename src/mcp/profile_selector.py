from src.profiles.preferences import prefs_store
from src.profiles.profile import get_profile


_CHANGE_CONFIRM = {
    "ETUDIANT": "✅ Profil **ETUDIANT** activé — ton pédagogique, sources accessibles, top 3 articles.\nDis-moi ce que tu veux explorer !",
    "INGENIEUR": "✅ Profil **INGENIEUR** activé — ton professionnel, sources techniques, jusqu'à 10 articles.\nQuel domaine aujourd'hui ?",
}

_CURRENT_PROFILE = """**Profil actif :** {profil}
**Domaines favoris :** {domaines}
**Score minimum :** {score_min}
**Sources prioritaires :** {sources}

Pour changer : "change mon profil pour ETUDIANT" ou "passe en mode INGENIEUR"
"""


async def select_profile(profil: str) -> str:
    """Change le profil actif et le persiste dans les préférences."""
    profil = profil.upper().strip()
    if profil not in ("ETUDIANT", "INGENIEUR"):
        return (
            f'Je ne connais pas le profil "{profil}".\n'
            "Profils disponibles : **ETUDIANT** et **INGENIEUR**"
        )

    profile = get_profile(profil)
    await prefs_store.update(profil=profil)

    return _CHANGE_CONFIRM[profil]


async def get_current_profile() -> str:
    """Retourne un résumé du profil actuellement actif."""
    prefs = await prefs_store.load()
    if not prefs.profil:
        return "Aucun profil défini. Dis-moi : **ETUDIANT** ou **INGENIEUR** ?"

    profile = get_profile(prefs.profil)
    return _CURRENT_PROFILE.format(
        profil=prefs.profil,
        domaines=", ".join(profile.domaines_favoris) if profile.domaines_favoris else "tous",
        score_min=profile.score_min,
        sources=", ".join(profile.sources_prioritaires[:4]) if profile.sources_prioritaires else "toutes",
    )
