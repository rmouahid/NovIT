from datetime import UTC, datetime

import pytest

from src.scrapers.base import Article


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
    from src.profiles.profile import get_profile

    return get_profile("ETUDIANT")


@pytest.fixture
def ingenieur_profile():
    from src.profiles.profile import get_profile

    return get_profile("INGENIEUR")
