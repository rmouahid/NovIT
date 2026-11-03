"""Retours des utilisateurs (#89).

`novit_feedback` enregistre un commentaire avec son contexte (profil, domaines
favoris, outil et requête concernés) dans la base SQLite locale. Un bug
signalé renvoie un lien vers une issue GitHub pré-remplie. `weekly_report`
produit le rapport hebdomadaire (scripts/feedback_report.py).

Les retours restent sur la machine : rien n'est envoyé automatiquement.
"""

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal
from urllib.parse import urlencode

import aiosqlite
from loguru import logger

from novit.mcp.health import read_version
from novit.profiles.preferences import prefs_store
from novit.settings import get_settings

FeedbackKind = Literal["bug", "suggestion", "positif", "negatif"]
KINDS: tuple[str, ...] = ("bug", "suggestion", "positif", "negatif")
MAX_COMMENT = 2000

NEW_ISSUE_URL = "https://github.com/rmouahid/NovIT/issues/new"

SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    comment TEXT NOT NULL,
    tool TEXT NOT NULL DEFAULT '',
    query TEXT NOT NULL DEFAULT '',
    profil TEXT NOT NULL DEFAULT '',
    domaines TEXT NOT NULL DEFAULT '[]',
    version TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);
"""


@dataclass
class Feedback:
    kind: str
    comment: str
    tool: str = ""
    query: str = ""
    profil: str = ""
    domaines: list[str] = field(default_factory=list)
    version: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    id: int | None = None


class FeedbackStore:
    """Retours utilisateur dans la base SQLite de NovIT (table `feedback`)."""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path
        self._initialized = False

    @property
    def db_path(self) -> str:
        return self._db_path or get_settings().db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA)
            await db.commit()
        self._initialized = True

    async def add(self, entry: Feedback) -> int:
        if not self._initialized:
            await self.init()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO feedback (created_at, kind, comment, tool, query, profil, "
                "domaines, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    entry.created_at.isoformat(),
                    entry.kind,
                    entry.comment,
                    entry.tool,
                    entry.query,
                    entry.profil,
                    json.dumps(entry.domaines, ensure_ascii=False),
                    entry.version,
                ],
            )
            await db.commit()
            entry.id = cursor.lastrowid
        return entry.id

    async def since(self, days: int, now: datetime | None = None) -> list[Feedback]:
        if not self._initialized:
            await self.init()
        cutoff = ((now or datetime.now(tz=UTC)) - timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM feedback WHERE created_at >= ? ORDER BY created_at",
                [cutoff],
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            Feedback(
                id=row["id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                kind=row["kind"],
                comment=row["comment"],
                tool=row["tool"],
                query=row["query"],
                profil=row["profil"],
                domaines=json.loads(row["domaines"]),
                version=row["version"],
            )
            for row in rows
        ]


feedback_store = FeedbackStore()


def issue_url(entry: Feedback) -> str:
    """Lien vers une issue « Signalement de bug » pré-remplie avec le retour."""
    context = [
        f"Signalé via `novit_feedback` (retour n°{entry.id}).",
        "",
        entry.comment,
        "",
        f"- Outil : {entry.tool or 'non précisé'}",
        f"- Requête : {entry.query or 'non précisée'}",
        f"- Profil : {entry.profil or 'non défini'}",
        f"- Domaines favoris : {', '.join(entry.domaines) or 'aucun'}",
    ]
    params = {
        "template": "bug_report.yml",
        "title": f"bug: {entry.comment.splitlines()[0][:80]}",
        "version": entry.version,
        "actual": "\n".join(context),
    }
    return f"{NEW_ISSUE_URL}?{urlencode(params)}"


async def submit_feedback(
    commentaire: str,
    type: str = "suggestion",
    outil: str = "",
    requete: str = "",
    store: FeedbackStore | None = None,
) -> str:
    """Enregistre un retour utilisateur et renvoie la confirmation à afficher."""
    comment = (commentaire or "").strip()[:MAX_COMMENT]
    if not comment:
        return "Le commentaire est vide : dis-moi ce qui t'a plu, déplu ou ce qui ne marche pas."
    kind = type if type in KINDS else "suggestion"
    prefs = prefs_store.load()
    entry = Feedback(
        kind=kind,
        comment=comment,
        tool=outil.strip(),
        query=requete.strip()[:500],
        profil=prefs.profil or "",
        domaines=list(prefs.domaines_favoris),
        version=read_version(),
    )
    await (store or feedback_store).add(entry)
    logger.info(f"[feedback] Retour n°{entry.id} enregistré ({kind})")

    lines = [f"✅ Merci ! Ton retour (n°{entry.id}, *{kind}*) est enregistré."]
    if kind == "bug":
        lines.append(
            f"\nPour qu'il soit corrigé, ouvre l'issue pré-remplie : {issue_url(entry)}"
        )
    return "\n".join(lines)


def weekly_report(entries: list[Feedback], days: int = 7) -> str:
    """Rapport Markdown des retours de la période : volumes, outils cités,
    bugs à transformer en issues, puis les commentaires."""
    title = f"# Retours NovIT — {days} derniers jours"
    if not entries:
        return f"{title}\n\nAucun retour sur la période."

    by_kind = Counter(e.kind for e in entries)
    by_tool = Counter(e.tool for e in entries if e.tool)
    lines = [
        title,
        "",
        f"**{len(entries)} retour(s)** · "
        + " · ".join(f"{k} : {by_kind[k]}" for k in KINDS if by_kind[k]),
    ]
    if by_tool:
        lines += ["", "## Outils concernés", ""]
        lines += [f"- `{tool}` : {n}" for tool, n in by_tool.most_common()]

    bugs = [e for e in entries if e.kind == "bug"]
    if bugs:
        lines += ["", "## Bugs à transformer en issues", ""]
        lines += [f"- n°{e.id} — {e.comment[:120]} → {issue_url(e)}" for e in bugs]

    lines += ["", "## Commentaires", ""]
    for e in entries:
        context = ", ".join(
            part
            for part in (e.tool and f"`{e.tool}`", e.profil, ", ".join(e.domaines))
            if part
        )
        stamp = e.created_at.strftime("%d/%m %H:%M")
        lines.append(f"- **{e.kind}** · {stamp}" + (f" · {context}" if context else ""))
        lines.append(f"  > {e.comment}")
    return "\n".join(lines)
