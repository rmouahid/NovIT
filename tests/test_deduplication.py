from datetime import UTC, datetime

from src.scrapers.base import Article
from src.scrapers.deduplication import (
    Deduplicator,
    _jaccard_similarity,
    _normalize,
)


def make_article(title: str, url: str) -> Article:
    return Article(
        title=title,
        url=url,
        summary="",
        published_at=datetime.now(tz=UTC),
        source="test",
        domains=["dev"],
        profiles=["ETUDIANT"],
    )


class TestNormalize:
    def test_lowercases(self):
        assert _normalize("PYTHON") == "python"

    def test_removes_articles(self):
        result = _normalize("The Quick Brown Fox")
        assert "the" not in result.split()

    def test_removes_punctuation(self):
        result = _normalize("Rust vs Go: which is better?")
        assert ":" not in result
        assert "?" not in result

    def test_collapses_spaces(self):
        assert "  " not in _normalize("too   many   spaces")


class TestJaccard:
    def test_identical(self):
        assert _jaccard_similarity("Python rocks", "Python rocks") == 1.0

    def test_completely_different(self):
        sim = _jaccard_similarity("Python programming", "Kubernetes networking")
        assert sim < 0.3

    def test_partial_overlap(self):
        sim = _jaccard_similarity("Python 3.13 released", "Python 3.13 is out now")
        assert 0.3 < sim < 1.0


class TestDeduplicator:
    def test_new_article_not_duplicate(self):
        d = Deduplicator()
        a = make_article("Fresh Article", "https://example.com/1")
        assert not d.is_duplicate(a)

    def test_url_duplicate(self):
        d = Deduplicator()
        a = make_article("Article A", "https://example.com/1")
        d.register(a)
        b = make_article("Different Title", "https://example.com/1")
        assert d.is_duplicate(b)

    def test_exact_title_duplicate(self):
        d = Deduplicator()
        a = make_article("Python 3.13 released", "https://a.com/1")
        b = make_article("Python 3.13 released", "https://b.com/2")
        d.register(a)
        assert d.is_duplicate(b)

    def test_fuzzy_duplicate(self):
        d = Deduplicator(similarity_threshold=0.7)
        a = make_article("Python 3.13 is now released with features", "https://a.com/1")
        b = make_article(
            "Python 3.13 is released with new features today", "https://b.com/2"
        )
        d.register(a)
        assert d.is_duplicate(b)

    def test_non_duplicate_different_topics(self):
        d = Deduplicator(similarity_threshold=0.7)
        a = make_article("Python 3.13 released", "https://a.com/1")
        b = make_article("Kubernetes 1.30 released", "https://b.com/2")
        d.register(a)
        assert not d.is_duplicate(b)

    def test_deduplicate_list_removes_exact(self):
        d = Deduplicator()
        articles = [
            make_article("Article 1", "https://example.com/1"),
            make_article("Article 1", "https://example.com/1"),
            make_article("Article 2", "https://example.com/2"),
        ]
        unique = d.deduplicate(articles)
        assert len(unique) == 2

    def test_deduplicate_preserves_order(self):
        d = Deduplicator()
        articles = [
            make_article("First", "https://example.com/1"),
            make_article("Second", "https://example.com/2"),
            make_article("Third", "https://example.com/3"),
        ]
        unique = d.deduplicate(articles)
        assert unique[0].title == "First"
        assert unique[1].title == "Second"

    def test_deduplicate_empty_list(self):
        d = Deduplicator()
        assert d.deduplicate([]) == []

    def test_register_makes_future_duplicate(self):
        d = Deduplicator()
        a = make_article("Unique", "https://example.com/1")
        assert not d.is_duplicate(a)
        d.register(a)
        assert d.is_duplicate(make_article("Unique", "https://example.com/1"))
