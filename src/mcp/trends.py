import re
from collections import Counter
from datetime import UTC, datetime, timedelta

from src.scrapers.base import Article
from src.scrapers.storage import store

_STOP_WORDS = {
    "the",
    "a",
    "an",
    "of",
    "in",
    "on",
    "to",
    "for",
    "and",
    "or",
    "is",
    "with",
    "de",
    "le",
    "la",
    "les",
    "un",
    "une",
    "des",
    "du",
    "en",
    "et",
    "ou",
    "que",
    "how",
    "why",
    "what",
    "when",
    "new",
    "this",
    "that",
    "are",
    "has",
    "have",
    "from",
    "by",
    "at",
    "as",
    "it",
    "its",
    "be",
    "was",
    "been",
    "will",
    "can",
    "using",
    "use",
    "your",
    "more",
    "about",
    "into",
    "get",
    "all",
    "but",
    "not",
}

_MIN_WORD_LENGTH = 4


def _extract_keywords(title: str) -> list[str]:
    words = re.findall(r"[a-zA-ZÀ-ÿ]+", title.lower())
    return [w for w in words if len(w) >= _MIN_WORD_LENGTH and w not in _STOP_WORDS]


def _count_keywords_by_window(articles: list[Article], days: int) -> Counter:
    cutoff = datetime.now(tz=UTC) - timedelta(days=days)
    recent = [a for a in articles if a.published_at and a.published_at > cutoff]
    counter: Counter = Counter()
    for article in recent:
        counter.update(_extract_keywords(article.title))
    return counter


async def detect_trends(days: int = 7, top_k: int = 10, min_count: int = 3) -> str:
    """Identifie les sujets les plus fréquents sur les N derniers jours.

    Compare la fréquence sur la période complète vs les dernières 24h
    pour détecter les sujets en montée rapide.
    """
    all_articles = await store.get_recent(hours=days * 24, limit=500)

    if not all_articles:
        return "Pas assez d'articles en base pour détecter des tendances. Lancez une veille d'abord."

    count_7d = _count_keywords_by_window(all_articles, days=days)
    count_24h = _count_keywords_by_window(all_articles, days=1)

    # Termes avec au moins min_count occurrences sur la période
    trending = [
        (term, count) for term, count in count_7d.most_common(50) if count >= min_count
    ]

    if not trending:
        return f"Aucune tendance significative détectée sur les {days} derniers jours (seuil : {min_count} occurrences)."

    # Détection des sujets en montée (ratio 24h/7d élevé)
    rising: list[tuple[str, int, float]] = []
    for term, count_total in trending:
        count_recent = count_24h.get(term, 0)
        ratio = (count_recent / max(count_total, 1)) * days
        if ratio > 1.5:
            rising.append((term, count_recent, ratio))
    rising.sort(key=lambda x: x[2], reverse=True)

    now = datetime.now(tz=UTC)
    lines = [
        f"# Tendances NovIT — {days} derniers jours",
        f"_Analysé à {now.strftime('%H:%M')} UTC · {len(all_articles)} articles_\n",
        "## Sujets les plus fréquents",
    ]
    for term, count in trending[:top_k]:
        bar = "█" * min(count, 20)
        lines.append(f"- **{term}** ({count}×) {bar}")

    if rising:
        lines.append("\n## 🚀 En montée rapide (dernières 24h)")
        for term, count_24h_val, ratio in rising[:5]:
            lines.append(
                f"- **{term}** — {count_24h_val}× aujourd'hui (×{ratio:.1f} vs moyenne)"
            )

    return "\n".join(lines)
