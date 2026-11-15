from collections import Counter
from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from novit.mcp import trends

NOW = datetime(2026, 9, 29, 12, tzinfo=UTC)


def test_security_templates_and_dates_do_not_become_topics():
    titles = [
        "CVE-2026-12345 — HIGH · CVSS 8.1 — OpenSSL",
        "CERTFR-2026-AVI-123 : multiples vulnérabilités dans OpenSSL",
        "CERT-FR : multiples vulnérabilités dans OpenSSL",
        "Septembre : les nouvelles des agents OpenAI",
        "September critical vulnerabilities with Windows",
        "Fe\u0301vrier : vulne\u0301rabilite\u0301s critiques dans Linux",
    ]
    terms = {term for title in titles for term in trends._extract_keywords(title)}
    assert terms == {"openssl", "agents", "openai", "windows", "linux"}


def test_fixed_article_corpus_is_balanced_by_source_and_utc_day(make_article):
    articles = [
        make_article(
            title=f"CVE-2026-{10000 + i} HIGH CVSS 8.1 OpenSSL OpenSSL",
            source="NVD",
            published_at=NOW - timedelta(hours=1),
        )
        for i in range(46)
    ]
    articles += [
        make_article(title="OpenSSL", source="nvd", published_at=NOW),
        make_article(title="OpenSSL", source="CERT-FR", published_at=NOW),
        make_article(
            title="OpenSSL", source="NVD", published_at=NOW - timedelta(days=1)
        ),
        make_article(title="OpenAI agents", source="HN", published_at=NOW),
        make_article(title="OpenAI agents", source="RSS", published_at=NOW),
        make_article(
            title="OpenAI agents", source="HN", published_at=NOW - timedelta(days=1)
        ),
    ]
    assert trends._count_keywords_by_window(articles, 7, now=NOW) == Counter(
        {"openssl": 3, "agents": 3, "openai": 3}
    )


def test_window_boundaries_and_dates_use_utc(make_article):
    articles = [
        make_article(title="Outside", published_at=NOW - timedelta(days=7)),
        make_article(title="Future", published_at=NOW + timedelta(seconds=1)),
        make_article(title="Inside", published_at=NOW - timedelta(days=7, seconds=-1)),
        make_article(
            title="Midnight",
            published_at=datetime(
                2026, 9, 29, 0, 30, tzinfo=timezone(timedelta(hours=2))
            ),
        ),
        make_article(
            title="Midnight", published_at=datetime(2026, 9, 28, 22, 45, tzinfo=UTC)
        ),
    ]
    assert trends._count_keywords_by_window(articles, 7, now=NOW) == Counter(
        {"inside": 1, "midnight": 1}
    )


@pytest.mark.asyncio
async def test_report_explains_weighted_counts_and_preserves_real_topics(
    make_article, monkeypatch
):
    articles = [
        make_article(title="OpenAI agents dans les nouvelles de septembre", source=s)
        for s in ["HN", "RSS", "blog"]
    ]
    monkeypatch.setattr(trends.store, "get_recent", AsyncMock(return_value=articles))
    report = await trends.detect_trends()
    assert "**agents** (3×)" in report
    assert "**openai** (3×)" in report
    assert "par source et par jour UTC" in report
    assert "**septembre**" not in report
