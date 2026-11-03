"""Mode hors-ligne dégradé (#91).

Quand aucune source ne répond, NovIT sert les articles déjà en base au lieu
d'échouer, signale clairement que les données viennent du cache et depuis
quand, et relance la collecte en arrière-plan jusqu'au retour des sources.
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from loguru import logger

from novit.scrapers.manager import FetchResult

# Délais (secondes) entre les tentatives de collecte en arrière-plan
RETRY_DELAYS: tuple[float, ...] = (30, 120, 300)

# Une réponse dégradée reste peu de temps en cache : dès que les sources
# reviennent, la requête suivante doit refléter les données fraîches.
TTL_OFFLINE = 60


def all_sources_down(result: FetchResult) -> bool:
    """Vrai si des scrapers ont été lancés et qu'aucun n'a répondu."""
    return bool(result.reports) and not result.sources_ok


def format_age(delta: timedelta) -> str:
    """Âge lisible : « 12 min », « 3 h », « 2 j »."""
    minutes = max(int(delta.total_seconds() // 60), 0)
    if minutes < 60:
        return f"{minutes} min"
    if minutes < 24 * 60:
        return f"{minutes // 60} h"
    return f"{minutes // (24 * 60)} j"


def offline_banner(
    last_update: datetime | None,
    retrying: bool,
    now: datetime | None = None,
) -> str:
    """Bandeau placé en tête d'une réponse servie depuis le cache local."""
    lines = [
        "> ⚠️ **Mode hors-ligne** : aucune source n'a répondu. "
        "Ces articles proviennent du cache local et peuvent être datés."
    ]
    if last_update is not None:
        now = now or datetime.now(tz=UTC)
        stamp = last_update.astimezone(UTC).strftime("%d/%m à %H:%M UTC")
        lines.append(
            f"> Dernière collecte réussie : {stamp} (il y a {format_age(now - last_update)})."
        )
    if retrying:
        lines.append("> Nouvelle tentative de collecte en arrière-plan.")
    return "\n".join(lines)


class BackgroundRetry:
    """Relance une collecte en arrière-plan, une seule boucle à la fois."""

    def __init__(self, delays: tuple[float, ...] = RETRY_DELAYS):
        self.delays = delays
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def schedule(self, refresh: Callable[[], Awaitable[bool]]) -> None:
        """Démarre la boucle de relance si aucune n'est en cours.

        `refresh` renvoie True quand au moins une source a répondu ; la boucle
        s'arrête alors.
        """
        if not self.running:
            self._task = asyncio.get_running_loop().create_task(self._loop(refresh))

    async def _loop(self, refresh: Callable[[], Awaitable[bool]]) -> None:
        for attempt, delay in enumerate(self.delays, 1):
            await asyncio.sleep(delay)
            try:
                if await refresh():
                    logger.info(f"[offline] Sources de retour (tentative {attempt})")
                    return
            except Exception as e:
                logger.warning(f"[offline] Tentative {attempt} en échec : {e}")
        logger.warning(
            f"[offline] Sources toujours injoignables après {len(self.delays)} tentatives"
        )

    async def wait(self) -> None:
        """Attend la fin de la boucle en cours (utile aux tests et à l'arrêt)."""
        if self._task is not None:
            await self._task


retry = BackgroundRetry()
