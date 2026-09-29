"""Les dates des articles sont toujours en UTC avec fuseau (#105)."""

from datetime import UTC, datetime, timedelta, timezone

from src.mcp import trends
from src.scrapers.base import Article


def article(published_at, title="Rust async runtime released"):
    return Article(
        title=title,
        url=f"https://example.com/{title}",
        summary="",
        published_at=published_at,
        source="test",
    )


def test_naive_dates_are_taken_as_utc():
    a = article(datetime(2026, 9, 21, 15, 17, 32))

    assert a.published_at == datetime(2026, 9, 21, 15, 17, 32, tzinfo=UTC)


def test_other_offsets_are_converted_to_utc():
    paris = timezone(timedelta(hours=2))

    a = article(datetime(2026, 9, 21, 17, 0, tzinfo=paris))

    assert a.published_at == datetime(2026, 9, 21, 15, 0, tzinfo=UTC)
    assert a.published_at.utcoffset() == timedelta(0)


def test_a_date_read_back_from_storage_without_offset_is_aware():
    # Format enregistré par les anciennes versions pour les CVE du NVD
    a = article(datetime.fromisoformat("2026-09-21T15:17:32.060000"))

    assert a.published_at.tzinfo is not None


async def test_trends_handle_articles_from_sources_with_and_without_offsets(
    monkeypatch,
):
    now = datetime.now(tz=UTC)
    mixed = [
        article(now - timedelta(hours=2), "Rust async runtime released"),
        article(
            (now - timedelta(hours=3)).replace(tzinfo=None), "Rust compiler speedup"
        ),
        article(now - timedelta(days=2), "Rust memory safety report"),
    ]

    async def get_recent(hours, limit):
        return mixed

    monkeypatch.setattr(trends.store, "get_recent", get_recent)

    report = await trends.detect_trends(days=7, min_count=3)

    assert "**rust** (3×)" in report
