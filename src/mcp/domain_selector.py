from src.profiles.preferences import prefs_store

_ALL_DOMAINS = ["ia", "securite", "dev", "ingenierie", "reglementation", "formation"]

_DOMAIN_LABELS = {
    "ia": "🤖 IA & Machine Learning",
    "securite": "🔐 Cybersécurité",
    "dev": "💻 Développement logiciel",
    "ingenierie": "⚙️ Ingénierie & architecture",
    "reglementation": "📜 Réglementation & conformité",
    "formation": "📚 Formation & carrière",
}

_SHORTCUTS: dict[str, list[str]] = {
    "tout": _ALL_DOMAINS,
    "tous": _ALL_DOMAINS,
    "all": _ALL_DOMAINS,
    "cyber": ["securite"],
    "cybersécurité": ["securite"],
    "cybersecurite": ["securite"],
    "ia": ["ia"],
    "intelligence artificielle": ["ia"],
    "dev": ["dev"],
    "développement": ["dev"],
    "developpement": ["dev"],
}


def _resolve_domains(raw: str | list[str]) -> list[str]:
    """Résout une chaîne ou liste de domaines en liste canonique."""
    if isinstance(raw, list):
        tokens = raw
    else:
        tokens = [t.strip().lower() for t in raw.replace("+", ",").split(",")]

    result: list[str] = []
    for token in tokens:
        token = token.strip().lower()
        if token in _SHORTCUTS:
            result.extend(_SHORTCUTS[token])
        elif token in _ALL_DOMAINS:
            result.append(token)
    return list(dict.fromkeys(result))


def list_domains() -> str:
    """Affiche tous les domaines disponibles."""
    lines = ["**Domaines NovIT disponibles :**\n"]
    for domain, label in _DOMAIN_LABELS.items():
        lines.append(f"- `{domain}` — {label}")
    lines.append("\nRaccourcis : `tout`, `cyber`, `ia`, `dev`")
    return "\n".join(lines)


async def set_domains(raw: str | list[str]) -> str:
    """Définit les domaines actifs de la session et les persiste."""
    domains = _resolve_domains(raw)
    if not domains:
        return (
            "Je n'ai pas reconnu ces domaines.\n"
            + list_domains()
        )

    await prefs_store.update(domaines_favoris=domains)

    labels = [_DOMAIN_LABELS.get(d, d) for d in domains]
    return f"Domaines actifs : {', '.join(labels)}\n\nDis-moi ce que tu veux explorer !"
