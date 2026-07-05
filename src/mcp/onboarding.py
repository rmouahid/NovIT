from src.profiles.preferences import prefs_store
from src.profiles.profile import get_profile

_DOMAINS_MENU = """
**Domaines disponibles :**
🤖 `ia`             — Intelligence artificielle & ML
🔐 `securite`       — Cybersécurité & CVE
💻 `dev`            — Développement logiciel
⚙️ `ingenierie`     — Ingénierie & architecture
📜 `reglementation` — RGPD, AI Act, normes
📚 `formation`      — Formation, certifications, carrière
"""

_WELCOME_ETUDIANT = """# Bienvenue sur NovIT ! 🚀

Je suis ton assistant de veille technologique personnalisé.
Profil activé : **ETUDIANT**

{domains_menu}
Tu peux me dire :
- "quoi de neuf en IA ?" pour les dernières actus
- "résumé du jour" pour ta veille quotidienne
- "cherche [sujet]" pour rechercher un sujet précis
- "aide" pour voir toutes les commandes

Quel domaine t'intéresse aujourd'hui ?
"""

_WELCOME_INGENIEUR = """# Bienvenue sur NovIT

Assistant de veille tech actif. Profil : **INGENIEUR**

{domains_menu}
Commandes : `news [domaine]` · `daily` · `search [terme]` · `dig [url]` · `trends`

Domaine(s) souhaité(s) pour cette session ?
"""

_PROFILE_SELECTION = """# NovIT — Initialisation

Pour personnaliser ta veille, quel est ton profil ?

**A — ETUDIANT** : tu apprends l'IT, en formation ou en reconversion
→ Ton pédagogique, vulgarisation, sources accessibles

**B — INGENIEUR** : tu travailles dans l'IT (dev, ops, sécurité…)
→ Ton professionnel, concision, sources techniques

Réponds **A** ou **B**, ou tape directement **ETUDIANT** / **INGENIEUR**.
"""


async def start_novit(profil: str | None = None) -> str:
    """Génère le message d'accueil NovIT.

    Si le profil est inconnu, affiche le menu de sélection.
    Si le profil est connu, affiche le message de bienvenue adapté.
    """
    prefs = await prefs_store.load()

    # Résolution du profil : argument > préférences sauvegardées > None
    resolved = profil or prefs.profil

    if not resolved or resolved not in ("ETUDIANT", "INGENIEUR"):
        return _PROFILE_SELECTION

    profile = get_profile(resolved)
    domains_menu = _DOMAINS_MENU

    if resolved == "ETUDIANT":
        return _WELCOME_ETUDIANT.format(domains_menu=domains_menu)
    return _WELCOME_INGENIEUR.format(domains_menu=domains_menu)
