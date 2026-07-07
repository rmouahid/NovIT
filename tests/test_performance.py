"""Tests de performance des points chauds NovIT, mesurés avec pytest-benchmark.

Ces tests ne font pas échouer la CI sur un seuil de temps (la machine varie) :
ils servent de garde-fou contre les régressions algorithmiques flagrantes
(ex : passage d'une déduplication O(n) à O(n²) mal maîtrisée) et de suivi
dans le temps via `pytest --benchmark-compare`.
"""

from datetime import UTC, datetime

from src.mcp.cache import TTLCache
from src.mcp.metrics import MetricsCollector
from src.profiles.filter import filter_and_rank
from src.profiles.profile import get_profile
from src.scrapers.base import Article
from src.scrapers.deduplication import Deduplicator
from src.scrapers.tagger import DomainTagger

N = 500


def make_articles(n: int, source: str = "hacker_news") -> list[Article]:
    # Chaque titre n'a qu'un seul mot commun avec les autres ("annoncé"), le
    # reste étant unique à l'index i : évite les faux positifs de similarité
    # fuzzy (Jaccard) entre articles censés être distincts dans ces tests.
    return [
        Article(
            title=f"Sujet{i} annoncé",
            url=f"https://example.com/article-{i}",
            summary="Un résumé suffisamment long pour ressembler à un vrai article "
            "de veille technologique, avec plusieurs mots-clés pertinents.",
            published_at=datetime.now(tz=UTC),
            source=source,
            domains=["ia", "dev"] if i % 2 == 0 else ["securite", "ingenierie"],
            profiles=["ETUDIANT", "INGENIEUR"],
            score=0.5 + (i % 10) / 20,
        )
        for i in range(n)
    ]


class TestDeduplicationPerformance:
    def test_register_bulk(self, benchmark):
        articles = make_articles(N)

        def register_all():
            d = Deduplicator()
            for article in articles:
                d.register(article)
            return d

        d = benchmark(register_all)
        assert len(d._url_index) == N

    def test_is_duplicate_against_warm_index(self, benchmark):
        d = Deduplicator()
        for article in make_articles(N):
            d.register(article)
        candidate = Article(
            title="Article totalement inédit sur un tout autre sujet",
            url="https://example.com/candidate",
            summary="",
            published_at=datetime.now(tz=UTC),
            source="hacker_news",
            domains=["ia"],
            profiles=["ETUDIANT"],
        )

        result = benchmark(d.is_duplicate, candidate)
        assert result is False

    def test_deduplicate_batch_with_duplicates(self, benchmark):
        base = make_articles(N // 2)
        articles = base + base  # 100% de doublons exacts

        def run():
            return Deduplicator().deduplicate(articles)

        unique = benchmark(run)
        assert len(unique) == N // 2


class TestFilterPerformance:
    def test_filter_and_rank_large_batch(self, benchmark):
        articles = make_articles(N)
        profile = get_profile("INGENIEUR")

        ranked = benchmark(filter_and_rank, articles, profile, None, 20)
        assert len(ranked) <= 20


class TestTaggerPerformance:
    def test_tag_all_large_batch(self, benchmark):
        tagger = DomainTagger()
        articles = make_articles(N)

        tagged = benchmark(tagger.tag_all, articles)
        assert len(tagged) == N


class TestCachePerformance:
    def test_set_then_get_many_keys(self, benchmark):
        cache = TTLCache()

        def run():
            for i in range(N):
                cache.set(f"key-{i}", f"value-{i}")
            for i in range(N):
                cache.get(f"key-{i}")

        benchmark(run)
        assert cache.stats()["entries"] == N


class TestMetricsPerformance:
    def test_record_many_tool_calls(self, benchmark):
        metrics = MetricsCollector()

        def workload():
            for i in range(N):
                metrics.record_tool_call(f"tool_{i % 5}")
                metrics.record_source_timing(f"source_{i % 10}", float(i))

        benchmark.pedantic(workload, setup=metrics.reset, rounds=50)
        assert sum(metrics.to_dict()["tool_calls"].values()) == N
