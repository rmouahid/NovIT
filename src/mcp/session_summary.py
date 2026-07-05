from datetime import datetime, timezone

from src.mcp.session import session_manager
from src.mcp.trends import _extract_keywords
from collections import Counter


async def build_session_summary(session_id: str = "default") -> str:
    """Génère le résumé de fin de session."""
    session = session_manager.get_or_create(session_id)

    history = list(session.history)
    if not history:
        return "Aucun article consulté dans cette session."

    now = datetime.now(tz=timezone.utc)
    duration = now - session.started_at
    minutes = int(duration.total_seconds() / 60)

    keyword_counter: Counter = Counter()
    for entry in history:
        keyword_counter.update(_extract_keywords(entry.get("title", "")))

    top_keywords = [kw for kw, _ in keyword_counter.most_common(5)]

    lines = [
        "# Résumé de session NovIT",
        f"_Durée : {minutes} min · {len(history)} article(s) consultés_\n",
        "## Articles consultés",
    ]
    for i, entry in enumerate(history[-20:], 1):
        lines.append(f"{i}. [{entry.get('title', '—')}]({entry.get('url', '')})")

    if top_keywords:
        lines.append("\n## Sujets de la session")
        lines.append(", ".join(f"`{kw}`" for kw in top_keywords))

    lines.append(
        "\n---\n_Exportez ce résumé en copiant ce bloc. "
        "Nouvelle session : demandez 'NovIT, on recommence'._"
    )
    return "\n".join(lines)
