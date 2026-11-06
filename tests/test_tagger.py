"""DomainTagger : domaines détectés par mots-clés en mots entiers (#118)."""

from datetime import UTC, datetime

import pytest

from novit.scrapers.base import Article
from novit.scrapers.tagger import DomainTagger


def write_domains(tmp_path, keywords: dict[str, list[str]]):
    lines = ["domains:"]
    for domain, words in keywords.items():
        lines += [f"  {domain}:", "    keywords:"] + [f'      - "{w}"' for w in words]
    path = tmp_path / "domains.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def article(title: str, summary: str = "", domains=None) -> Article:
    return Article(
        title=title,
        url=f"https://example.com/{abs(hash(title))}",
        summary=summary,
        published_at=datetime(2026, 11, 6, tzinfo=UTC),
        source="test",
        domains=list(domains or []),
    )


@pytest.fixture
def tagger(tmp_path):
    return DomainTagger(
        write_domains(
            tmp_path,
            {
                "reglementation": ["norme", "ai act", "gdpr"],
                "dev": ["c++", ".net", "rust"],
            },
        )
    )


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Une nouvelle norme européenne", ["reglementation"]),
        ("Un écart énorme entre les modèles", []),  # « norme » dans « énorme »
        ("What the AI Act changes for startups", ["reglementation"]),
        ("GDPR fines in 2026", ["reglementation"]),
        ("Trust and safety at scale", []),  # « rust » dans « trust »
        ("Rust 2.0 released", ["dev"]),
        ("Modern C++ coroutines", ["dev"]),
        ("Migrating to .NET 10", ["dev"]),
    ],
)
def test_keywords_match_whole_words_only(tagger, title, expected):
    assert tagger.tag(article(title)).domains == expected


def test_summary_is_searched_too(tagger):
    assert tagger.tag(article("Weekly notes", "GDPR guidance")).domains == [
        "reglementation"
    ]


def test_scraper_domains_are_kept(tagger):
    tagged = tagger.tag(article("Rust 2.0 released", domains=["ia"]))
    assert tagged.domains == ["dev", "ia"]


def test_real_config_no_longer_tags_engineering_posts_as_regulation():
    """Les mots-clés trop génériques (standard, policy…) sont retirés (#118)."""
    real = DomainTagger()
    post = article(
        "Bring multimodal semantic search to the edge",
        "A standard library and a new retry policy for our data governance",
    )
    assert "reglementation" not in real.tag(post).domains
