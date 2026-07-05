import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum

from loguru import logger

from src.scrapers.base import BaseScraper
from src.scrapers.deduplication import deduplicator
from src.scrapers.tagger import tagger
from src.scrapers.storage import store


class Priority(IntEnum):
    CRITICAL = 0   # CVE, alertes sécurité
    HIGH = 1       # Sources principales (HN, GitHub)
    NORMAL = 2     # Blogs, RSS génériques


@dataclass(order=True)
class ScraperTask:
    priority: Priority
    scraper: BaseScraper = field(compare=False)
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc), compare=False)


class ScraperQueue:
    """File de tâches asynchrone pour orchestrer les scrapers par priorité.

    Les sources critiques (CVE) sont toujours traitées avant les sources régulières.
    La file permet de planifier des rafraîchissements sans bloquer le serveur MCP.
    """

    def __init__(self):
        self._queue: asyncio.PriorityQueue[ScraperTask] = asyncio.PriorityQueue()
        self._running = False
        self._processed = 0
        self._failed = 0

    def enqueue(self, scraper: BaseScraper, priority: Priority = Priority.NORMAL) -> None:
        task = ScraperTask(priority=priority, scraper=scraper)
        self._queue.put_nowait(task)
        logger.debug(f"[queue] Ajout : {scraper.name} (priorité {priority.name})")

    async def process_one(self) -> bool:
        """Traite le prochain scraper de la file. Retourne True si succès."""
        try:
            task = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return False

        scraper = task.scraper
        logger.info(f"[queue] Traitement : {scraper.name}")
        try:
            articles = await asyncio.wait_for(scraper.fetch(), timeout=30)
            tagged = tagger.tag_all(articles)
            unique = deduplicator.deduplicate(tagged)
            await store.save(unique)
            self._processed += 1
            logger.info(f"[queue] {scraper.name} : {len(unique)} articles enregistrés")
            return True
        except Exception as e:
            self._failed += 1
            logger.error(f"[queue] Erreur {scraper.name} : {e}")
            return False
        finally:
            self._queue.task_done()

    async def run(self) -> None:
        """Traite la file jusqu'à épuisement."""
        self._running = True
        while not self._queue.empty():
            await self.process_one()
        self._running = False

    def status(self) -> dict:
        return {
            "pending": self._queue.qsize(),
            "processed": self._processed,
            "failed": self._failed,
            "running": self._running,
        }


# Instance globale
scraper_queue = ScraperQueue()
