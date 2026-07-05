from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.profiles.profile import Profile


@dataclass
class RequestContext:
    """Contexte injecté automatiquement dans chaque appel d'outil MCP.

    Regroupe les métadonnées de session (profil, domaines actifs, langue)
    pour enrichir les réponses sans que l'utilisateur ait à les répéter.
    """
    profile: Profile | None = None
    active_domains: list[str] = field(default_factory=list)
    langue: str = "fr"
    generated_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    session_id: str = "default"
    debug: bool = False

    def to_header(self) -> str:
        """Génère le bloc de contexte injecté en tête de réponse MCP."""
        now = self.generated_at.strftime("%H:%M UTC")
        parts = [f"_Généré à {now}"]
        if self.profile:
            parts.append(f" · Profil {self.profile.name}")
        if self.active_domains:
            parts.append(f" · Domaines : {', '.join(self.active_domains)}")
        parts.append("_")
        return "".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profil": self.profile.name if self.profile else None,
            "domaines_actifs": self.active_domains,
            "langue": self.langue,
            "generated_at": self.generated_at.isoformat(),
            "session_id": self.session_id,
            "debug": self.debug,
        }


def build_context(arguments: dict, session_id: str = "default") -> RequestContext:
    """Construit le contexte de requête à partir des arguments MCP reçus."""
    from src.profiles.profile import get_profile

    profil_name = arguments.get("profil")
    profile = get_profile(profil_name) if profil_name else None

    domaines = arguments.get("domaines", [])
    if not domaines and profile:
        domaines = profile.domaines_favoris or []

    return RequestContext(
        profile=profile,
        active_domains=domaines,
        langue=arguments.get("langue", "fr"),
        session_id=session_id,
        debug=arguments.get("debug", False),
    )
