from datetime import UTC, datetime

import pytest

from novit.scrapers.base import Article
from novit.scrapers.rate_limiter import rate_limiter


@pytest.fixture
def make_article():
    def _factory(
        title="Test Article",
        url="https://example.com/article",
        summary="Test summary",
        source="test_source",
        domains=None,
        profiles=None,
        score=0.5,
        published_at=None,
    ) -> Article:
        return Article(
            title=title,
            url=url,
            summary=summary,
            published_at=published_at or datetime.now(tz=UTC),
            source=source,
            domains=domains or ["dev"],
            profiles=profiles or ["ETUDIANT", "INGENIEUR"],
            score=score,
        )

    return _factory


@pytest.fixture
def etudiant_profile():
    from novit.profiles.profile import get_profile

    return get_profile("ETUDIANT")


@pytest.fixture
def ingenieur_profile():
    from novit.profiles.profile import get_profile

    return get_profile("INGENIEUR")


@pytest.fixture(autouse=True)
def no_rate_limit_delays(monkeypatch):
    """Pas d'attente entre requêtes simulées : le limiteur global garde ses
    délais réels (6 s pour NVD) en production ; il est testé avec ses propres
    instances dans tests/test_polite_http.py."""
    monkeypatch.setattr(rate_limiter, "default_delay", 0.0)
    monkeypatch.setattr(rate_limiter, "_delays", {})
    monkeypatch.setattr(rate_limiter, "_last_request", {})
