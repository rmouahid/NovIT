"""Transport HTTP du serveur MCP, pour un déploiement distant (ADR-005).

Le endpoint MCP (Streamable HTTP, réponses en flux SSE) est servi sur `/mcp`
et protégé par un jeton bearer. `/health` reste public pour les sondes de la
plateforme d'hébergement.
"""

import hmac
from dataclasses import asdict

from loguru import logger
from mcp.server import Server
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from novit.mcp.health import get_health, read_version, uptime_seconds

MCP_PATH = "/mcp"
HEALTH_PATH = "/health"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


class BearerTokenMiddleware:
    """Refuse toute requête vers le endpoint MCP sans le jeton attendu."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self._expected = f"Bearer {token}".encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"] != HEALTH_PATH:
            provided = dict(scope["headers"]).get(b"authorization", b"")
            if not hmac.compare_digest(provided, self._expected):
                response = JSONResponse(
                    {"error": "jeton d'accès manquant ou invalide"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


async def health(request: Request) -> JSONResponse:
    """Sonde de vie, sans appel réseau ; `?sources=1` ajoute l'état des sources.

    Le code HTTP reste 200 même si des sources sont en panne : l'instance
    répond, la redémarrer ne réparerait pas un site tiers indisponible.
    """
    if request.query_params.get("sources") in ("1", "true"):
        report = await get_health()
        return JSONResponse(asdict(report))
    return JSONResponse(
        {
            "status": "ok",
            "version": read_version(),
            "uptime_seconds": round(uptime_seconds(), 1),
        }
    )


def create_http_app(server: Server, host: str, token: str) -> Starlette:
    """Application ASGI servant `server` en HTTP.

    Sans jeton, seule une écoute en local est acceptée : exposer les outils
    sur le réseau sans authentification n'est jamais voulu.
    """
    if not token and host not in LOOPBACK_HOSTS:
        raise ValueError(
            f"NOVIT_API_TOKEN est obligatoire pour écouter sur {host} "
            "(voir docs/CLOUD_DEPLOYMENT.md)"
        )
    app = server.streamable_http_app(
        streamable_http_path=MCP_PATH,
        host=host,
        custom_starlette_routes=[Route(HEALTH_PATH, health, methods=["GET"])],
    )
    if token:
        app.add_middleware(BearerTokenMiddleware, token=token)
    else:
        logger.warning("Transport HTTP sans jeton : écoute limitée à la machine locale")
    return app


def run_http(server: Server, host: str, port: int, token: str) -> None:
    import uvicorn

    app = create_http_app(server, host=host, token=token)
    logger.info(f"Serveur NovIT MCP en HTTP sur http://{host}:{port}{MCP_PATH}")
    uvicorn.run(app, host=host, port=port, log_config=None)
