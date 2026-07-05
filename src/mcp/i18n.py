import re

_EN_WORDS = {
    "news", "latest", "show", "get", "find", "search", "what", "how", "tell",
    "give", "list", "about", "today", "yesterday", "recent", "new", "top",
    "security", "vulnerability", "update", "release", "article", "blog",
}

_FR_WORDS = {
    "quoi", "donne", "montre", "cherche", "trouve", "actualité", "news",
    "veille", "dernier", "dernière", "article", "résumé", "aujourd", "hier",
    "sécurité", "vulnérabilité", "tendance", "domaine",
}

_LANG_LABELS = {
    "fr": "français",
    "en": "english",
}


def detect_language(text: str) -> str:
    """Détecte si le texte est en français ou anglais. Défaut : 'fr'."""
    lower = text.lower()
    words = set(re.findall(r"[a-zA-ZÀ-ÿ]+", lower))
    en_score = len(words & _EN_WORDS)
    fr_score = len(words & _FR_WORDS)
    if en_score > fr_score:
        return "en"
    return "fr"


_TEMPLATES: dict[str, dict[str, str]] = {
    "no_results": {
        "fr": "Aucun article trouvé pour ces critères.",
        "en": "No articles found matching these criteria.",
    },
    "source_unavailable": {
        "fr": "⚠️ La source {source} est temporairement indisponible.",
        "en": "⚠️ Source {source} is temporarily unavailable.",
    },
    "profile_required": {
        "fr": "Quel est ton profil : **ETUDIANT** ou **INGENIEUR** ?",
        "en": "What's your profile: **ETUDIANT** or **INGENIEUR**?",
    },
    "generated_at": {
        "fr": "Généré à {time} UTC",
        "en": "Generated at {time} UTC",
    },
    "articles_label": {
        "fr": "{n} articles · Profil {profil}",
        "en": "{n} articles · Profile {profil}",
    },
}


def t(key: str, langue: str = "fr", **kwargs) -> str:
    """Retourne le message traduit pour la clé donnée."""
    lang = langue if langue in ("fr", "en") else "fr"
    template = _TEMPLATES.get(key, {}).get(lang, _TEMPLATES.get(key, {}).get("fr", key))
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
