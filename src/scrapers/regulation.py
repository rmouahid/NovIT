"""Scrapers réglementation : CNIL, EUR-Lex (AI Act), W3C News."""

from src.scrapers.rss import RssScraper, load_rss_sources


def build_regulation_scrapers() -> list[RssScraper]:
    return [RssScraper(src) for src in load_rss_sources(category="reglementation")]
