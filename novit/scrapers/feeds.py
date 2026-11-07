"""Lecture asynchrone des flux RSS/Atom.

`feedparser.parse(url)` télécharge le flux de façon synchrone : appelé dans
une coroutine, il bloquait toute la boucle d'événements pendant le
téléchargement, si bien que les sources RSS étaient lues l'une après l'autre
au lieu d'en parallèle (#90). Le flux est désormais téléchargé avec httpx,
puis analysé dans un thread pour ne pas bloquer les autres scrapers.
"""

import asyncio

import feedparser

from novit.scrapers.http import http_client

FEED_TIMEOUT = 20


async def fetch_feed(
    url: str, timeout: float = FEED_TIMEOUT
) -> feedparser.FeedParserDict:
    """Télécharge et analyse un flux RSS/Atom.

    Suit les redirections, comme le faisait feedparser. Lève une exception
    httpx si la source est injoignable ou répond une erreur HTTP : le
    ScraperManager compte alors la source comme en échec. L'agent envoyé est
    `NOVIT_USER_AGENT` : certains hébergeurs refusent celui d'httpx. Les
    requêtes passent par le limiteur de débit du domaine (`http_client`).
    """
    async with http_client(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
    return await asyncio.to_thread(feedparser.parse, response.content)
