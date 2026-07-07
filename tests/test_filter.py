from datetime import UTC, datetime

import pytest

from src.profiles.filter import filter_and_rank, score_article
from src.profiles.profile import get_profile
from src.scrapers.base import Article


def make_article(
    title="Test",
    url="https://example.com/1",
    domains=None,
    profiles=None,
    score=0.5,
    source="test_source",
) -> Article:
    return Article(
        title=title,
        url=url,
        summary="",
        published_at=datetime.now(tz=UTC),
        source=source,
        domains=domains or ["dev"],
        profiles=profiles or ["ETUDIANT", "INGENIEUR"],
        score=score,
    )


@pytest.fixture
def etudiant():
    return get_profile("ETUDIANT")


@pytest.fixture
def ingenieur():
    return get_profile("INGENIEUR")


class TestScoreArticle:
    def test_priority_source_boosts_score(self, etudiant):
        # hacker_news est prioritaire pour ETUDIANT
        article = make_article(source="hacker_news", domains=["ia"], score=0.5)
        s = score_article(article, etudiant)
        assert s > 0.5 * 1.0  # supérieur à un score sans boost source

    def test_favori_domain_boosts_score(self, etudiant):
        article = make_article(source="test_source", domains=["ia"], score=0.5)
        normal = score_article(
            make_article(source="test_source", domains=["ingenierie"], score=0.5),
            etudiant,
        )
        boosted = score_article(article, etudiant)
        assert boosted > normal

    def test_score_zero_for_zero_article(self, etudiant):
        article = make_article(score=0.0)
        assert score_article(article, etudiant) == 0.0


class TestFilterAndRank:
    def test_filters_by_domain(self, etudiant):
        articles = [
            make_article("IA", url="https://x.com/1", domains=["ia"]),
            make_article("Dev", url="https://x.com/2", domains=["dev"]),
            make_article("Sécu", url="https://x.com/3", domains=["securite"]),
        ]
        result = filter_and_rank(articles, etudiant, domains=["ia"])
        assert all("ia" in a.domains for a in result)
        assert len(result) == 1

    def test_filters_by_profile(self, etudiant):
        articles = [
            make_article(
                "Pour tous", url="https://x.com/1", profiles=["ETUDIANT", "INGENIEUR"]
            ),
            make_article("Ingé only", url="https://x.com/2", profiles=["INGENIEUR"]),
        ]
        result = filter_and_rank(articles, etudiant)
        assert all("ETUDIANT" in a.profiles for a in result)
        assert len(result) == 1

    def test_filters_below_score_min(self, etudiant):
        # score_min ETUDIANT = 0.3
        # score = 0.1, source non-prioritaire (1.0), domaine secondaire ingenierie (1.0)
        # score final = 0.1 * 1.0 * 1.0 = 0.1 < 0.3
        article = make_article(score=0.1, source="unknown", domains=["ingenierie"])
        result = filter_and_rank([article], etudiant)
        assert len(result) == 0

    def test_sorts_by_score_descending(self, etudiant):
        articles = [
            make_article(
                "Low",
                url="https://x.com/1",
                source="hacker_news",
                domains=["ia"],
                score=0.4,
            ),
            make_article(
                "High",
                url="https://x.com/2",
                source="hacker_news",
                domains=["ia"],
                score=0.8,
            ),
        ]
        result = filter_and_rank(articles, etudiant)
        assert result[0].score >= result[-1].score

    def test_respects_limit(self, etudiant):
        articles = [
            make_article(
                f"Article {i}",
                url=f"https://x.com/{i}",
                source="hacker_news",
                domains=["ia"],
                score=0.5,
            )
            for i in range(20)
        ]
        result = filter_and_rank(articles, etudiant, limit=5)
        assert len(result) == 5

    def test_empty_input(self, etudiant):
        assert filter_and_rank([], etudiant) == []

    def test_no_domain_filter_returns_all_matching(self, etudiant):
        articles = [
            make_article("IA", url="https://x.com/1", domains=["ia"], score=0.5),
            make_article("Dev", url="https://x.com/2", domains=["dev"], score=0.5),
        ]
        result = filter_and_rank(articles, etudiant)
        assert len(result) == 2

    def test_ingenieur_higher_score_min(self, ingenieur):
        # score_min INGENIEUR = 0.4
        # score = 0.3, source non-prioritaire (1.0), domaine favori ia (1.5)
        # score final = 0.3 * 1.0 * 1.5 = 0.45 > 0.4 → passe
        article = make_article(score=0.3, source="unknown", domains=["ia"])
        result = filter_and_rank([article], ingenieur)
        assert len(result) == 1
