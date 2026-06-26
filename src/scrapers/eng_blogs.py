"""Scrapers pour les blogs d'ingénierie : Netflix, Google Eng, Meta Eng, The New Stack."""

from src.scrapers.rss import RssSource, RssScraper

ENG_RSS_SOURCES = [
    RssSource(
        name="netflix_tech",
        url="https://netflixtechblog.com/feed",
        domains=["ingenierie", "dev"],
        profiles=["INGENIEUR"],
        base_score=0.85,
    ),
    RssSource(
        name="google_eng",
        url="https://developers.googleblog.com/feeds/posts/default",
        domains=["ingenierie", "dev", "ia"],
        profiles=["INGENIEUR"],
        base_score=0.8,
    ),
    RssSource(
        name="meta_eng",
        url="https://engineering.fb.com/feed/",
        domains=["ingenierie", "dev"],
        profiles=["INGENIEUR"],
        base_score=0.8,
    ),
    RssSource(
        name="the_new_stack",
        url="https://thenewstack.io/feed/",
        domains=["ingenierie", "dev"],
        profiles=["INGENIEUR"],
        base_score=0.7,
    ),
]


def build_eng_scrapers() -> list[RssScraper]:
    return [RssScraper(src) for src in ENG_RSS_SOURCES]
