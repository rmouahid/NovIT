"""Transport HTTP du serveur MCP, pour un déploiement distant (ADR-005).

Le endpoint MCP (Streamable HTTP, réponses en flux SSE) est servi sur `/mcp`
et protégé par un jeton bearer : le jeton unique `NOVIT_API_TOKEN`, ou un jeton
par utilisateur (`NOVIT_API_TOKENS`, #87). `/health` reste public pour les
sondes de la plateforme d'hébergement.
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
from novit.mcp.users import DEFAULT_USER

MCP_PATH = "/mcp"
HEALTH_PATH = "/health"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
# Clé de `request.state` où le middleware dépose l'utilisateur authentifié.
USER_STATE_KEY = "novit_user"


class BearerTokenMiddleware:
    """Refuse toute requête vers le endpoint MCP sans un jeton connu, et note
    l'utilisateur auquel appartient le jeton présenté."""

    def __init__(self, app: ASGIApp, tokens: dict[str, str]) -> None:
        self.app = app
        self._expected = [
            (f"Bearer {token}".encode(), user) for token, user in tokens.items()
        ]

    def _authenticate(self, provided: bytes) -> str | None:
        user = None
        # Toutes les comparaisons sont faites : la durée ne dit pas quel jeton
        # ressemble le plus à celui présenté.
        for expected, candidate in self._expected:
            if hmac.compare_digest(provided, expected):
                user = candidate
        return user

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"] != HEALTH_PATH:
            provided = dict(scope["headers"]).get(b"authorization", b"")
            user = self._authenticate(provided)
            if user is None:
                response = JSONResponse(
                    {"error": "jeton d'accès manquant ou invalide"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return
            scope.setdefault("state", {})[USER_STATE_KEY] = user
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


def create_http_app(
    server: Server, host: str, token: str, users: dict[str, str] | None = None
) -> Starlette:
    """Application ASGI servant `server` en HTTP.

    `token` est le jeton unique (utilisateur `default`), `users` associe un
    jeton à chaque utilisateur d'une instance partagée ; les deux peuvent
    coexister. Sans aucun jeton, seule une écoute en local est acceptée :
    exposer les outils sur le réseau sans authentification n'est jamais voulu.
    """
    tokens = dict(users or {})
    if token:
        if token in tokens:
            raise ValueError("NOVIT_API_TOKEN est aussi le jeton d'un utilisateur")
        tokens[token] = DEFAULT_USER
    if not tokens and host not in LOOPBACK_HOSTS:
        raise ValueError(
            f"NOVIT_API_TOKEN ou NOVIT_API_TOKENS est obligatoire pour écouter sur "
            f"{host} (voir docs/CLOUD_DEPLOYMENT.md)"
        )
    app = server.streamable_http_app(
        streamable_http_path=MCP_PATH,
        host=host,
        custom_starlette_routes=[Route(HEALTH_PATH, health, methods=["GET"])],
    )
    if tokens:
        app.add_middleware(BearerTokenMiddleware, tokens=tokens)
    else:
        logger.warning("Transport HTTP sans jeton : écoute limitée à la machine locale")
    return app


def run_http(
    server: Server, host: str, port: int, token: str, users: dict[str, str]
) -> None:
    import uvicorn

    app = create_http_app(server, host=host, token=token, users=users)
    logger.info(f"Serveur NovIT MCP en HTTP sur http://{host}:{port}{MCP_PATH}")
    uvicorn.run(app, host=host, port=port, log_config=None)
