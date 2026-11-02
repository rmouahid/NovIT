"""Lecture asynchrone des flux RSS/Atom (#90) et scrapers qui l'utilisent."""

import asyncio
import threading
import time

import httpx
import pytest
import respx

from novit.scrapers import feeds
from novit.scrapers.cve import ANSSI_RSS_URL, ANSSIScraper
from novit.scrapers.feeds import USER_AGENT, fetch_feed
from novit.scrapers.rss import RssScraper, RssSource

FEED_URL = "https://blog.example.com/feed.xml"

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Exemple</title>
<item><title>Premier article</title><link>https://blog.example.com/1</link>
<description>Resume un</description><pubDate>Mon, 02 Nov 2026 08:00:00 GMT</pubDate></item>
<item><title>Second article</title><link>https://blog.example.com/2</link>
<description>Resume deux</description></item>
<item><title>Doublon</title><link>https://blog.example.com/1</link></item>
</channel></rss>"""


def source() -> RssSource:
    return RssSource(
        name="exemple", url=FEED_URL, domains=["dev"], profiles=["ETUDIANT"]
    )


class TestFetchFeed:
    @respx.mock
    async def test_parses_feed_with_explicit_user_agent(self):
        route = respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=RSS))

        feed = await fetch_feed(FEED_URL)

        assert [e.title for e in feed.entries][:2] == [
            "Premier article",
            "Second article",
        ]
        assert route.calls.last.request.headers["user-agent"] == USER_AGENT

    @respx.mock
    async def test_follows_redirects(self):
        respx.get("http://old.example.com/rss").mock(
            return_value=httpx.Response(301, headers={"Location": FEED_URL})
        )
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=RSS))

        feed = await fetch_feed("http://old.example.com/rss")

        assert len(feed.entries) == 3

    @respx.mock
    async def test_http_error_raises(self):
        respx.get(FEED_URL).mock(return_value=httpx.Response(404))

        with pytest.raises(httpx.HTTPStatusError):
            await fetch_feed(FEED_URL)

    @respx.mock
    async def test_parsing_runs_outside_the_event_loop(self, monkeypatch):
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=RSS))
        loop_thread = threading.get_ident()
        parse_threads = []
        real_parse = feeds.feedparser.parse

        def spy(content):
            parse_threads.append(threading.get_ident())
            return real_parse(content)

        monkeypatch.setattr(feeds.feedparser, "parse", spy)
        await fetch_feed(FEED_URL)

        assert parse_threads and parse_threads[0] != loop_thread

    async def test_feeds_are_read_concurrently(self, monkeypatch):
        """Deux flux lents de 0,2 s se lisent en ~0,2 s, pas 0,4 s : le
        téléchargement ne bloque plus la boucle d'événements."""

        async def slow(request):
            await asyncio.sleep(0.2)
            return httpx.Response(200, content=RSS)

        with respx.mock:
            respx.get(url__regex=r"https://slow\d\.example\.com/feed").mock(
                side_effect=slow
            )
            start = time.perf_counter()
            await asyncio.gather(
                fetch_feed("https://slow1.example.com/feed"),
                fetch_feed("https://slow2.example.com/feed"),
            )
            elapsed = time.perf_counter() - start

        assert elapsed < 0.35


class TestRssScraper:
    @respx.mock
    async def test_fetch_builds_unique_articles(self):
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=RSS))

        articles = await RssScraper(source()).fetch()

        assert [a.url for a in articles] == [
            "https://blog.example.com/1",
            "https://blog.example.com/2",
        ]
        assert articles[0].source == "exemple"
        assert articles[0].domains == ["dev"]
        assert articles[0].published_at.day == 2

    @respx.mock
    async def test_invalid_feed_returns_nothing(self):
        respx.get(FEED_URL).mock(
            return_value=httpx.Response(200, content=b"<html>pas un flux")
        )

        assert await RssScraper(source()).fetch() == []

    @respx.mock
    async def test_dead_feed_is_reported_as_failure(self):
        respx.get(FEED_URL).mock(return_value=httpx.Response(404))

        with pytest.raises(httpx.HTTPStatusError):
            await RssScraper(source()).fetch()

    @respx.mock
    async def test_health_check(self):
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=RSS))
        assert await RssScraper(source()).health_check() is True

    @respx.mock
    async def test_health_check_down(self):
        respx.get(FEED_URL).mock(side_effect=httpx.ConnectError("refused"))
        assert await RssScraper(source()).health_check() is False


class TestANSSIScraper:
    @respx.mock
    async def test_fetch(self):
        respx.get(ANSSI_RSS_URL).mock(return_value=httpx.Response(200, content=RSS))

        articles = await ANSSIScraper().fetch()

        assert len(articles) == 3
        assert all(a.source == "anssi_cert" for a in articles)
        assert articles[0].domains == ["securite"]

    @respx.mock
    async def test_health_check_down(self):
        respx.get(ANSSI_RSS_URL).mock(return_value=httpx.Response(503))
        assert await ANSSIScraper().health_check() is False
