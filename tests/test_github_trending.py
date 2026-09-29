import pytest

from src.scrapers.github_trending import (
    GitHubTrendingScraper,
    format_count,
    parse_count,
)


def repo_box(
    name, description="", language="Python", stars="42,358", today="3,274 stars today"
):
    lang = f'<span itemprop="programmingLanguage">{language}</span>' if language else ""
    return f"""
    <article class="Box-row">
      <h2><a href="/{name}">{name.replace('/', ' / ')}</a></h2>
      <p>{description}</p>
      {lang}
      <a href="/{name}/stargazers">{stars}</a>
      <span class="d-inline-block float-sm-right">{today}</span>
    </article>"""


def parse(*boxes):
    return GitHubTrendingScraper()._parse(
        "<html><body>" + "".join(boxes) + "</body></html>"
    )


@pytest.mark.parametrize(
    "text, expected",
    [
        ("42,358", 42358),
        ("3,274 stars today", 3274),
        ("1.2k", 1200),
        ("15k", 15000),
        ("987", 987),
        ("", 0),
        ("no number", 0),
    ],
)
def test_parse_count(text, expected):
    assert parse_count(text) == expected


def test_format_count_uses_french_thousands_separator():
    assert format_count(42358) == "42 358"
    assert format_count(987) == "987"


def test_summary_is_in_french_without_the_github_english_text():
    (article,) = parse(repo_box("owner/repo", "A fast tool"))

    assert (
        article.summary.splitlines()[0]
        == "⭐ 42 358 étoiles · +3 274 aujourd'hui · Python"
    )
    assert "stars today" not in article.summary
    assert article.extra["stars"] == 42358
    assert article.extra["stars_today"] == 3274


def test_missing_daily_stars_are_omitted():
    (article,) = parse(repo_box("owner/repo", today=""))

    assert "aujourd'hui" not in article.summary


def test_ai_repositories_are_tagged_ia_without_tagging_the_next_ones():
    first, second = parse(
        repo_box("a/agent", "An AI agent framework", language="TypeScript"),
        repo_box("b/ui", "A UI component library", language="TypeScript"),
    )

    assert "ia" in first.domains
    assert second.domains == ["dev"]
    # La table partagée n'est pas modifiée
    (again,) = parse(repo_box("c/ui", "Another UI kit", language="TypeScript"))
    assert again.domains == ["dev"]


@pytest.mark.parametrize(
    "description, tagged",
    [
        ("Run LLMs locally", True),
        ("Neural search engine", True),
        ("Open source AI assistant", True),
        ("Send email from the terminal", False),
        ("Maintain your dotfiles", False),
        ("Detailed changelog generator", False),
    ],
)
def test_ai_keywords_match_whole_words_only(description, tagged):
    (article,) = parse(repo_box("o/r", description, language="Go"))

    assert ("ia" in article.domains) is tagged
