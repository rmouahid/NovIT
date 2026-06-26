from loguru import logger
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from config.settings import get_settings
from src.mcp.errors import NovitError
from src.mcp.handlers import (
    handle_get_by_domain,
    handle_get_news,
    handle_get_profile,
    handle_search,
)
from src.mcp.health import get_cache_health, get_health, get_sources_health
from src.mcp.logging_config import configure_logging
from src.mcp.schemas import (
    GetByDomainInput,
    GetNewsInput,
    GetProfileInput,
    SearchInput,
)

_settings = get_settings()
configure_logging(
    log_level=_settings.log_level,
    log_dir=_settings.log_dir,
    is_production=_settings.is_production,
)

app = Server("novit")

TOOLS: list[Tool] = [
    Tool(
        name="novit_get_news",
        description="Récupère les dernières actualités tech filtrées selon le profil utilisateur et les domaines souhaités.",
        inputSchema={
            "type": "object",
            "properties": {
                "profil": {
                    "type": "string",
                    "enum": ["ETUDIANT", "INGENIEUR"],
                    "description": "Profil utilisateur",
                },
                "domaines": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Domaines : ia, securite, dev, ingenierie, reglementation, formation",
                },
                "nb_articles": {
                    "type": "integer",
                    "default": 10,
                    "description": "Nombre d'articles (1-50)",
                },
                "periode": {
                    "type": "string",
                    "enum": ["1h", "6h", "24h", "7j"],
                    "default": "24h",
                    "description": "Fenêtre temporelle",
                },
            },
            "required": ["profil"],
        },
    ),
    Tool(
        name="novit_search",
        description="Recherche plein texte dans les articles en cache NovIT.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Terme(s) de recherche"},
                "domaine": {"type": "string", "description": "Filtrer par domaine"},
                "source": {"type": "string", "description": "Filtrer par source"},
                "profil": {
                    "type": "string",
                    "enum": ["ETUDIANT", "INGENIEUR"],
                    "description": "Adapter les résultats au profil",
                },
                "page": {"type": "integer", "default": 1},
                "per_page": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="novit_get_by_domain",
        description="Retourne les articles filtrés par domaine technologique.",
        inputSchema={
            "type": "object",
            "properties": {
                "domaine": {
                    "type": "string",
                    "description": "Domaine : ia, securite, dev, ingenierie, reglementation, formation",
                },
                "profil": {
                    "type": "string",
                    "enum": ["ETUDIANT", "INGENIEUR"],
                    "description": "Profil utilisateur (optionnel)",
                },
                "nb_articles": {"type": "integer", "default": 10},
            },
            "required": ["domaine"],
        },
    ),
    Tool(
        name="novit_get_profile",
        description="Retourne les informations et préférences d'un profil NovIT.",
        inputSchema={
            "type": "object",
            "properties": {
                "profil": {
                    "type": "string",
                    "enum": ["ETUDIANT", "INGENIEUR"],
                    "description": "Profil à inspecter",
                }
            },
            "required": ["profil"],
        },
    ),
    Tool(
        name="novit_health",
        description="Retourne l'état de santé du serveur NovIT (uptime, cache, sources).",
        inputSchema={
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "enum": ["global", "sources", "cache"],
                    "default": "global",
                    "description": "Niveau de détail du rapport",
                }
            },
        },
    ),
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info(f"Appel outil : {name} | args={arguments}")
    try:
        if name == "novit_get_news":
            result = await handle_get_news(GetNewsInput(**arguments))
        elif name == "novit_search":
            result = await handle_search(SearchInput(**arguments))
        elif name == "novit_get_by_domain":
            result = await handle_get_by_domain(GetByDomainInput(**arguments))
        elif name == "novit_get_profile":
            result = await handle_get_profile(GetProfileInput(**arguments))
        elif name == "novit_health":
            detail = arguments.get("detail", "global")
            if detail == "sources":
                sources = await get_sources_health()
                result = "\n".join(f"- {'✅' if s.available else '❌'} {s.name}" for s in sources) or "Aucune source enregistrée."
            elif detail == "cache":
                stats = await get_cache_health()
                result = "\n".join(f"- {k}: {v}" for k, v in stats.items())
            else:
                report = await get_health()
                result = report.to_text()
        else:
            result = f"Outil inconnu : {name}"
        return [TextContent(type="text", text=result)]
    except NovitError as e:
        logger.warning(f"NovitError : {e}")
        return [TextContent(type="text", text=e.to_mcp_error())]
    except Exception as e:
        logger.exception(f"Erreur inattendue dans {name}")
        return [TextContent(type="text", text=f"Erreur interne NovIT : {e}")]


async def main() -> None:
    logger.info("Démarrage du serveur NovIT MCP")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
    logger.info("Serveur NovIT arrêté")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
