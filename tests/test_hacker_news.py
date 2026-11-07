import asyncio
import time

import httpx
import pytest
import respx

from novit.scrapers import hacker_news
from novit.scrapers.hacker_news import HN_API, HackerNewsScraper, _tag_domains

STORY_1 = {
    "id": 1,
    "type": "story",
    "title": "New LLM beats GPT-4 on all benchmarks",
    "url": "https://example.com/llm-news",
    "score": 200,
    "descendants": 80,
    "time": 1700000000,
}

STORY_2 = {
    "id": 2,
    "type": "story",
    "title": "Critical CVE vulnerability in OpenSSL",
    "url": "https://example.com/cve-news",
    "score": 150,
    "descendants": 40,
    "time": 1700000100,
}

STORY_LOW_SCORE = {
    "id": 3,
    "type": "story",
    "title": "Low traffic post",
    "url": "https://example.com/low",
    "score": 5,
    "descendants": 1,
    "time": 1700000200,
}


class TestTagDomains:
    def test_ia_keywords(self):
        domains = _tag_domains("New OpenAI LLM trained on huge dataset")
        assert "ia" in domains

    def test_security_keywords(self):
        domains = _tag_domains("Critical CVE vulnerability discovered in OpenSSL")
        assert "securite" in domains

    def test_dev_keywords(self):
        domains = _tag_domains("Introducing a new Python framework for async apps")
        assert "dev" in domains

    def test_multiple_domains(self):
        domains = _tag_domains(
            "Security vulnerability in a Python machine learning library"
        )
        assert "dev" in domains or "securite" in domains

    def test_no_match_returns_empty(self):
        domains = _tag_domains("Random unrelated content about cooking")
        assert domains == []


class TestHackerNewsScraper:
    @pytest.fixture
    def scraper(self):
        return HackerNewsScraper(min_score=50, max_articles=2)

    async def test_fetch_returns_articles(self, scraper):
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(200, json=[1, 2])
            )
            respx.get(f"{HN_API}/item/1.json").mock(
                return_value=httpx.Response(200, json=STORY_1)
            )
            respx.get(f"{HN_API}/item/2.json").mock(
                return_value=httpx.Response(200, json=STORY_2)
            )
            articles = await scraper.fetch()

        assert len(articles) == 2
        assert articles[0].source == "hacker_news"
        assert articles[0].title == STORY_1["title"]

    async def test_fetch_filters_low_score(self, scraper):
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(200, json=[3])
            )
            respx.get(f"{HN_API}/item/3.json").mock(
                return_value=httpx.Response(200, json=STORY_LOW_SCORE)
            )
            articles = await scraper.fetch()

        assert len(articles) == 0

    async def test_fetch_article_fields(self, scraper):
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(200, json=[1])
            )
            respx.get(f"{HN_API}/item/1.json").mock(
                return_value=httpx.Response(200, json=STORY_1)
            )
            articles = await scraper.fetch()

        a = articles[0]
        assert a.url == STORY_1["url"]
        assert a.score == min(STORY_1["score"] / 1000, 1.0)
        assert a.extra["hn_score"] == STORY_1["score"]
        assert a.published_at is not None

    async def test_fetch_skips_non_story(self, scraper):
        job_item = {
            "id": 99,
            "type": "job",
            "title": "Hiring Python devs",
            "score": 500,
            "time": 1700000000,
        }
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(200, json=[99])
            )
            respx.get(f"{HN_API}/item/99.json").mock(
                return_value=httpx.Response(200, json=job_item)
            )
            articles = await scraper.fetch()

        assert len(articles) == 0

    async def test_health_check_ok(self):
        scraper = HackerNewsScraper()
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(200, json=[])
            )
            result = await scraper.health_check()
        assert result is True

    async def test_health_check_fails_on_error(self):
        scraper = HackerNewsScraper()
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            result = await scraper.health_check()
        assert result is False

    async def test_health_check_fails_on_500(self):
        scraper = HackerNewsScraper()
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(500)
            )
            result = await scraper.health_check()
        assert result is False


class TestHackerNewsConcurrency:
    """Les items sont récupérés en parallèle (#90) sans perdre l'ordre du
    classement ni dépasser ITEM_CONCURRENCY requêtes simultanées."""

    @staticmethod
    def story(i: int) -> dict:
        return {
            "id": i,
            "type": "story",
            "title": f"Story {i}",
            "url": f"https://example.com/{i}",
            "score": 100,
            "time": 1700000000,
        }

    async def test_keeps_top_stories_order_despite_latency(self, monkeypatch):
        scraper = HackerNewsScraper(min_score=50, max_articles=3)
        # Les premiers items répondent le plus lentement
        delays = {1: 0.05, 2: 0.04, 3: 0.03, 4: 0.0, 5: 0.0, 6: 0.0}

        async def fake_item(client, item_id):
            await asyncio.sleep(delays[item_id])
            return self.story(item_id)

        monkeypatch.setattr(scraper, "_fetch_item", fake_item)
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(200, json=[1, 2, 3, 4, 5, 6])
            )
            articles = await scraper.fetch()

        assert [a.title for a in articles] == ["Story 1", "Story 2", "Story 3"]

    async def test_bounded_concurrency_and_faster_than_sequential(self, monkeypatch):
        scraper = HackerNewsScraper(min_score=50, max_articles=30)
        in_flight = 0
        peak = 0

        async def fake_item(client, item_id):
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0.02)
            in_flight -= 1
            return self.story(item_id)

        monkeypatch.setattr(scraper, "_fetch_item", fake_item)
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(200, json=list(range(1, 61)))
            )
            start = time.perf_counter()
            articles = await scraper.fetch()
            elapsed = time.perf_counter() - start

        assert len(articles) == 30
        assert peak == hacker_news.ITEM_CONCURRENCY
        # Séquentiel : 60 × 20 ms = 1,2 s ; parallèle par 10 : ~0,12 s
        assert elapsed < 0.6

    async def test_failing_item_is_skipped(self, monkeypatch):
        scraper = HackerNewsScraper(min_score=50, max_articles=5)

        async def fake_item(client, item_id):
            if item_id == 2:
                raise httpx.ConnectError("reset")
            return self.story(item_id)

        monkeypatch.setattr(scraper, "_fetch_item", fake_item)
        with respx.mock:
            respx.get(f"{HN_API}/topstories.json").mock(
                return_value=httpx.Response(200, json=[1, 2, 3])
            )
            articles = await scraper.fetch()

        assert [a.title for a in articles] == ["Story 1", "Story 3"]
