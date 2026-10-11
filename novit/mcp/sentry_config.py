from loguru import logger


def init_sentry(dsn: str, environment: str, traces_sample_rate: float = 0.0) -> bool:
    """Initialise Sentry si un DSN est configuré.

    Ne fait rien (et ne lève pas d'exception) si dsn est vide : Sentry est
    strictement optionnel, l'absence de configuration ne doit jamais bloquer
    le démarrage du serveur. Retourne True si Sentry a été activé.
    """
    if not dsn:
        logger.debug("[sentry] SENTRY_DSN absent, monitoring d'erreurs désactivé")
        return False

    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        # stdio MCP : ne pas envoyer les logs INFO en breadcrumbs, trop verbeux.
        default_integrations=True,
    )
    logger.info(f"[sentry] Monitoring d'erreurs activé (environment={environment})")
    return True


def capture_tool_error(exc: Exception, tool_name: str, arguments: dict) -> None:
    """Capture une exception d'outil MCP avec un contexte enrichi.

    Ajoute le nom de l'outil, le profil et le domaine (s'ils sont présents
    dans les arguments) pour faciliter le triage côté Sentry, sans effet si
    Sentry n'est pas initialisé (no-op silencieux du SDK dans ce cas).
    """
    import sentry_sdk

    with sentry_sdk.new_scope() as scope:
        scope.set_tag("mcp_tool", tool_name)
        if profil := arguments.get("profil"):
            scope.set_tag("novit_profil", profil)
        if domaine := arguments.get("domaine") or arguments.get("domaines"):
            scope.set_tag("novit_domaine", str(domaine))
        scope.set_context("mcp_call", {"tool": tool_name, "arguments": arguments})
        sentry_sdk.capture_exception(exc)
