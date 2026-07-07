"""Scrapers réglementation : CNIL, EUR-Lex (AI Act), W3C News."""

from src.scrapers.rss import RssScraper, RssSource

REGULATION_RSS_SOURCES = [
    RssSource(
        name="cnil",
        url="https://www.cnil.fr/fr/rss.xml",
        domains=["reglementation"],
        profiles=["ETUDIANT", "INGENIEUR"],
        base_score=0.8,
    ),
    RssSource(
        name="eurlex_ai",
        url="https://eur-lex.europa.eu/rss/legal-act/en/new.rss",
        domains=["reglementation", "ia"],
        profiles=["INGENIEUR"],
        base_score=0.75,
    ),
    RssSource(
        name="w3c_news",
        url="https://www.w3.org/news/feed",
        domains=["reglementation", "dev"],
        profiles=["INGENIEUR"],
        base_score=0.65,
    ),
]


def build_regulation_scrapers() -> list[RssScraper]:
    return [RssScraper(src) for src in REGULATION_RSS_SOURCES]
