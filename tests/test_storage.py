from datetime import UTC, datetime

import pytest

from src.scrapers.base import Article
from src.scrapers.storage import ArticleStore


def make_article(
    title="Test",
    url="https://example.com/1",
    domains=None,
    profiles=None,
    score=0.5,
) -> Article:
    return Article(
        title=title,
        url=url,
        summary="Test summary",
        published_at=datetime.now(tz=UTC),
        source="test_source",
        domains=domains or ["dev"],
        profiles=profiles or ["ETUDIANT", "INGENIEUR"],
        score=score,
    )


@pytest.fixture
async def store(tmp_path):
    s = ArticleStore(db_path=str(tmp_path / "test.db"))
    await s.init()
    return s


async def test_save_and_retrieve(store):
    saved = await store.save([make_article("Article 1")])
    assert saved == 1
    recent = await store.get_recent()
    assert len(recent) == 1
    assert recent[0].title == "Article 1"


async def test_no_duplicate_url(store):
    article = make_article()
    await store.save([article])
    await store.save([article])
    recent = await store.get_recent()
    assert len(recent) == 1


async def test_filter_by_domain(store):
    await store.save(
        [
            make_article("IA", url="https://x.com/1", domains=["ia"]),
            make_article("Dev", url="https://x.com/2", domains=["dev"]),
        ]
    )
    results = await store.get_recent(domains=["ia"])
    assert len(results) == 1
    assert "ia" in results[0].domains


async def test_filter_by_profile(store):
    await store.save(
        [
            make_article("Etudiant", url="https://x.com/1", profiles=["ETUDIANT"]),
            make_article("Ingenieur", url="https://x.com/2", profiles=["INGENIEUR"]),
        ]
    )
    results = await store.get_recent(profiles=["ETUDIANT"])
    assert len(results) == 1
    assert "ETUDIANT" in results[0].profiles


async def test_limit_results(store):
    await store.save(
        [make_article(f"Article {i}", url=f"https://x.com/{i}") for i in range(10)]
    )
    results = await store.get_recent(limit=3)
    assert len(results) == 3


async def test_search_by_title(store):
    await store.save(
        [
            make_article("Python 3.13 released", url="https://x.com/1"),
            make_article("Rust is amazing", url="https://x.com/2"),
        ]
    )
    results = await store.search("python")
    assert len(results) == 1
    assert "Python" in results[0].title


async def test_search_by_summary(store):
    await store.save(
        [
            make_article("Article A", url="https://x.com/1"),
        ]
    )
    # summary = "Test summary" → searching "test" should find it
    results = await store.search("test summary")
    assert len(results) == 1


async def test_search_empty(store):
    await store.save([make_article()])
    results = await store.search("zzz_no_match_xyz")
    assert len(results) == 0


async def test_purge_expired(tmp_path):
    store = ArticleStore(db_path=str(tmp_path / "test.db"), retention_days=0)
    await store.init()
    await store.save([make_article()])
    deleted = await store.purge_expired()
    assert deleted >= 1
    remaining = await store.get_recent()
    assert len(remaining) == 0


async def test_save_returns_count(store):
    articles = [make_article(f"A{i}", url=f"https://x.com/{i}") for i in range(5)]
    saved = await store.save(articles)
    assert saved == 5


async def test_article_roundtrip_preserves_fields(store):
    original = make_article(
        "Roundtrip Test",
        url="https://x.com/roundtrip",
        domains=["ia", "dev"],
        score=0.75,
    )
    await store.save([original])
    results = await store.get_recent()
    restored = results[0]

    assert restored.title == original.title
    assert restored.url == original.url
    assert set(restored.domains) == set(original.domains)
    assert restored.score == original.score
