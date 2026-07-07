import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite
from loguru import logger

from src.scrapers.base import Article

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    published_at TEXT NOT NULL,
    source TEXT NOT NULL,
    domains TEXT NOT NULL,   -- JSON array
    profiles TEXT NOT NULL,  -- JSON array
    score REAL DEFAULT 0.0,
    extra TEXT DEFAULT '{}', -- JSON object
    inserted_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_inserted ON articles(inserted_at);
"""


class ArticleStore:
    """Stockage persistant des articles dans SQLite (via aiosqlite).

    Rétention configurable — les articles expirés sont supprimés automatiquement.
    """

    def __init__(self, db_path: str = "./novit.db", retention_days: int = 7):
        self.db_path = db_path
        self.retention_days = retention_days
        self._initialized = False

    async def init(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA)
            await db.commit()
        self._initialized = True
        logger.info(f"[storage] Base initialisée : {self.db_path}")

    async def save(self, articles: list[Article]) -> int:
        if not self._initialized:
            await self.init()
        now = datetime.now(tz=UTC).isoformat()
        saved = 0
        async with aiosqlite.connect(self.db_path) as db:
            for article in articles:
                try:
                    await db.execute(
                        """
                        INSERT OR IGNORE INTO articles
                            (url, title, summary, published_at, source, domains, profiles, score, extra, inserted_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            article.url,
                            article.title,
                            article.summary,
                            article.published_at.isoformat(),
                            article.source,
                            json.dumps(article.domains),
                            json.dumps(article.profiles),
                            article.score,
                            json.dumps(article.extra),
                            now,
                        ),
                    )
                    saved += 1
                except Exception as e:
                    logger.warning(f"[storage] Erreur save {article.url[:50]} : {e}")
            await db.commit()
        logger.info(f"[storage] {saved} articles enregistrés")
        return saved

    async def get_recent(
        self,
        domains: list[str] | None = None,
        profiles: list[str] | None = None,
        hours: int = 24,
        limit: int = 50,
    ) -> list[Article]:
        if not self._initialized:
            await self.init()
        since = (datetime.now(tz=UTC) - timedelta(hours=hours)).isoformat()
        query = "SELECT * FROM articles WHERE published_at >= ? ORDER BY score DESC, published_at DESC LIMIT ?"
        params: list = [since, limit]

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

        articles = [self._row_to_article(row) for row in rows]

        if domains:
            articles = [a for a in articles if any(d in a.domains for d in domains)]
        if profiles:
            articles = [a for a in articles if any(p in a.profiles for p in profiles)]

        return articles

    async def search(self, query: str, limit: int = 20) -> list[Article]:
        if not self._initialized:
            await self.init()
        pattern = f"%{query.lower()}%"
        sql = """
            SELECT * FROM articles
            WHERE lower(title) LIKE ? OR lower(summary) LIKE ?
            ORDER BY score DESC, published_at DESC
            LIMIT ?
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql, [pattern, pattern, limit]) as cursor:
                rows = await cursor.fetchall()
        return [self._row_to_article(row) for row in rows]

    async def purge_expired(self) -> int:
        if not self._initialized:
            await self.init()
        cutoff = (
            datetime.now(tz=UTC) - timedelta(days=self.retention_days)
        ).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM articles WHERE inserted_at < ?", [cutoff]
            )
            await db.commit()
            deleted = cursor.rowcount
        if deleted:
            logger.info(
                f"[storage] {deleted} articles expirés supprimés (rétention {self.retention_days}j)"
            )
        return deleted

    def _row_to_article(self, row: aiosqlite.Row) -> Article:
        return Article(
            url=row["url"],
            title=row["title"],
            summary=row["summary"] or "",
            published_at=datetime.fromisoformat(row["published_at"]),
            source=row["source"],
            domains=json.loads(row["domains"]),
            profiles=json.loads(row["profiles"]),
            score=row["score"],
            extra=json.loads(row["extra"]),
        )


# Instance globale
store = ArticleStore()
