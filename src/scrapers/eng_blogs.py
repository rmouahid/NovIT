"""Scrapers pour les blogs d'ingénierie : Netflix, Google Eng, Meta Eng, The New Stack."""

from src.scrapers.rss import RssScraper, load_rss_sources


def build_eng_scrapers() -> list[RssScraper]:
    return [RssScraper(src) for src in load_rss_sources(category="ingenierie")]
