import re
import unicodedata
from collections import Counter
from datetime import UTC, datetime, timedelta

from novit.scrapers.base import Article
from novit.scrapers.storage import store

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

# Mots de liaison, dates et gabarits des bulletins de sécurité. Les noms de
# produits (OpenSSL, Windows, etc.) restent des sujets utiles.
_STOP_WORDS.update(
    "dans avec pour plus moins cette ceci cela ces sont etre être était étaient "
    "aussi comme leur leurs nous vous votre vos notre nos tout tous toute toutes "
    "sans sous entre chez depuis après avant lors dont ainsi encore fait faire "
    "vers selon plusieurs multiples nouveau nouveaux nouvelle nouvelles "
    "janvier février fevrier mars avril mai juin juillet août aout septembre "
    "octobre novembre décembre decembre january february march april june july "
    "august september october november december today yesterday update updates "
    "these those they them their there here were being does did than then which "
    "while some such only also over under through could would should just "
    "cvss cve cert certfr high critical medium low critique critiques élevée élevées "
    "vulnérabilité vulnérabilités vulnerabilite vulnerabilites vulnerability "
    "vulnerabilities bulletin bulletins avis alerte alertes".split()
)

_BULLETIN_ID = re.compile(
    r"\b(?:CVE-\d{4}-\d+|CERTFR-\d{4}-[A-Z]+-\d+)\b", re.IGNORECASE
)


def _extract_keywords(title: str) -> list[str]:
    title = unicodedata.normalize("NFC", _BULLETIN_ID.sub(" ", title)).casefold()
    words = re.findall(r"[^\W\d_]+", title)
    return [w for w in words if len(w) >= _MIN_WORD_LENGTH and w not in _STOP_WORDS]


def _count_keywords_by_window(
    articles: list[Article], days: int, *, now: datetime | None = None
) -> Counter:
    now = now or datetime.now(tz=UTC)
    cutoff = now - timedelta(days=days)
    recent = [a for a in articles if a.published_at and cutoff < a.published_at <= now]
    counter: Counter = Counter()
    seen: set[tuple[str, str, str]] = set()
    for article in recent:
        # Une rafale de CVE d'une source ne pèse pas davantage qu'une autre
        # source qui mentionne le même sujet le même jour (date en UTC).
        day = article.published_at.astimezone(UTC).date().isoformat()
        source = article.source.strip().casefold() or article.url
        for term in sorted(set(_extract_keywords(article.title))):
            key = (source, day, term)
            if key not in seen:
                seen.add(key)
                counter[term] += 1
    return counter


async def detect_trends(days: int = 7, top_k: int = 10, min_count: int = 3) -> str:
    """Identifie les sujets les plus fréquents sur les N derniers jours.

    Compare la fréquence sur la période complète vs les dernières 24h
    pour détecter les sujets en montée rapide.
    """
    all_articles = await store.get_recent(hours=days * 24, limit=500)

    if not all_articles:
        return "Pas assez d'articles en base pour détecter des tendances. Lancez une veille d'abord."

    now = datetime.now(tz=UTC)
    count_7d = _count_keywords_by_window(all_articles, days=days, now=now)
    count_24h = _count_keywords_by_window(all_articles, days=1, now=now)

    # Termes avec au moins min_count occurrences sur la période
    trending = [
        (term, count) for term, count in count_7d.most_common(50) if count >= min_count
    ]

    if not trending:
        return f"Aucune tendance significative détectée sur les {days} derniers jours (seuil : {min_count} mentions source/jour)."

    # Détection des sujets en montée (ratio 24h/7d élevé)
    rising: list[tuple[str, int, float]] = []
    for term, count_total in trending:
        count_recent = count_24h.get(term, 0)
        ratio = (count_recent / max(count_total, 1)) * days
        if ratio > 1.5:
            rising.append((term, count_recent, ratio))
    rising.sort(key=lambda x: x[2], reverse=True)

    lines = [
        f"# Tendances NovIT — {days} derniers jours",
        f"_Analysé à {now.strftime('%H:%M')} UTC · {len(all_articles)} articles_\n",
        "## Sujets les plus fréquents",
        "_Un sujet compte au plus une fois par source et par jour UTC._",
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
