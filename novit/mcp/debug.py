import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DebugInfo:
    """Rapport de debug pour un appel d'outil MCP.

    Collecté pendant l'exécution, affiché en pied de réponse si debug=True.
    """

    tool_name: str
    started_at: float = field(default_factory=time.monotonic)
    sources_consulted: list[str] = field(default_factory=list)
    articles_before_filter: int = 0
    articles_after_filter: int = 0
    cache_hit: bool = False
    errors: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.started_at) * 1000)

    def to_block(self) -> str:
        """Génère le bloc debug markdown inséré en pied de réponse."""
        lines = [
            "\n---",
            f"**🔍 Debug NovIT** · `{self.tool_name}` · {self.elapsed_ms}ms",
        ]
        if self.cache_hit:
            lines.append("- ✅ Réponse depuis le cache")
        else:
            if self.sources_consulted:
                lines.append(
                    f"- Sources consultées : {', '.join(self.sources_consulted)}"
                )
            lines.append(
                f"- Articles : {self.articles_before_filter} bruts → {self.articles_after_filter} après filtrage"
            )
        if self.errors:
            for err in self.errors:
                lines.append(f"- ⚠️ {err}")
        for k, v in self.extra.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)


def append_debug(response: str, debug_info: DebugInfo, debug: bool) -> str:
    """Ajoute le bloc debug à la réponse si le mode debug est activé."""
    if not debug:
        return response
    return response + debug_info.to_block()
