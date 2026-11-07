"""Retours utilisateurs (#89) : enregistrement avec contexte, lien d'issue
pour un bug, rapport hebdomadaire et outil MCP."""

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from mcp import Client

from novit.mcp import feedback, server
from novit.mcp.feedback import (
    Feedback,
    FeedbackStore,
    issue_url,
    submit_feedback,
    weekly_report,
)
from novit.profiles.preferences import PreferencesStore, UserPreferences


@pytest.fixture
def store(tmp_path):
    return FeedbackStore(db_path=str(tmp_path / "feedback.db"))


@pytest.fixture
def prefs(tmp_path, monkeypatch):
    p = PreferencesStore(path=tmp_path / "prefs.json")
    p.save(UserPreferences(profil="INGENIEUR", domaines_favoris=["securite", "ia"]))
    monkeypatch.setattr(feedback, "prefs_store", p)
    return p


class TestSubmitFeedback:
    async def test_stores_comment_with_context(self, store, prefs):
        text = await submit_feedback(
            "Les CVE remontent en double",
            type="suggestion",
            outil="novit_get_news",
            requete="domaines=securite",
            store=store,
        )

        assert "n°1" in text
        [entry] = await store.since(days=1)
        assert entry.comment == "Les CVE remontent en double"
        assert entry.tool == "novit_get_news"
        assert entry.query == "domaines=securite"
        assert entry.profil == "INGENIEUR"
        assert entry.domaines == ["securite", "ia"]
        assert entry.version

    async def test_bug_returns_prefilled_issue_link(self, store, prefs):
        text = await submit_feedback(
            "novit_dig plante sur les PDF", type="bug", store=store
        )

        assert "https://github.com/rmouahid/NovIT/issues/new?" in text

    async def test_non_bug_has_no_issue_link(self, store, prefs):
        text = await submit_feedback("Super outil", type="positif", store=store)
        assert "issues/new" not in text

    async def test_empty_comment_is_rejected(self, store, prefs):
        text = await submit_feedback("   ", store=store)
        assert "vide" in text
        assert await store.since(days=1) == []

    async def test_unknown_type_falls_back_to_suggestion(self, store, prefs):
        await submit_feedback("Idée", type="inconnu", store=store)
        [entry] = await store.since(days=1)
        assert entry.kind == "suggestion"

    async def test_long_comment_is_truncated(self, store, prefs):
        await submit_feedback("x" * 5000, store=store)
        [entry] = await store.since(days=1)
        assert len(entry.comment) == feedback.MAX_COMMENT


class TestIssueUrl:
    def test_prefills_bug_template_fields(self):
        entry = Feedback(
            id=7,
            kind="bug",
            comment="Résultats vides\nsur le domaine ia",
            tool="novit_get_by_domain",
            query="domaine=ia",
            profil="ETUDIANT",
            domaines=["ia"],
            version="0.1.0",
        )
        url = urlparse(issue_url(entry))
        params = {k: v[0] for k, v in parse_qs(url.query).items()}

        assert params["template"] == "bug_report.yml"
        assert params["title"] == "bug: Résultats vides"
        assert params["version"] == "0.1.0"
        assert "novit_get_by_domain" in params["actual"]
        assert "domaine=ia" in params["actual"]
        assert "retour n°7" in params["actual"]


class TestStore:
    async def test_since_filters_by_date(self, store):
        now = datetime(2026, 11, 2, tzinfo=UTC)
        await store.add(
            Feedback(
                kind="positif", comment="ancien", created_at=now - timedelta(days=10)
            )
        )
        await store.add(
            Feedback(kind="bug", comment="récent", created_at=now - timedelta(days=2))
        )

        recent = await store.since(days=7, now=now)

        assert [e.comment for e in recent] == ["récent"]


class TestWeeklyReport:
    def test_empty_period(self):
        assert "Aucun retour" in weekly_report([], days=7)

    def test_counts_tools_bugs_and_comments(self):
        now = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)
        entries = [
            Feedback(
                id=1, kind="bug", comment="Plante", tool="novit_dig", created_at=now
            ),
            Feedback(
                id=2, kind="suggestion", comment="Plus de sources FR", created_at=now
            ),
            Feedback(
                id=3,
                kind="positif",
                comment="Top",
                tool="novit_dig",
                profil="ETUDIANT",
                created_at=now,
            ),
        ]

        report = weekly_report(entries, days=7)

        assert "**3 retour(s)**" in report
        assert "bug : 1" in report and "suggestion : 1" in report
        assert "- `novit_dig` : 2" in report
        assert "## Bugs à transformer en issues" in report
        assert "n°1 — Plante → https://github.com/rmouahid/NovIT/issues/new?" in report
        assert "> Plus de sources FR" in report
        assert "02/11 09:30" in report


async def test_mcp_tool_records_feedback(tmp_path, monkeypatch, prefs):
    tool_store = FeedbackStore(db_path=str(tmp_path / "tool.db"))
    monkeypatch.setattr(feedback, "feedback_store", tool_store)

    async with Client(server.app) as client:
        tools = await client.list_tools()
        assert "novit_feedback" in [t.name for t in tools.tools]
        result = await client.call_tool(
            "novit_feedback",
            {"commentaire": "Très utile", "type": "positif", "outil": "novit_daily"},
        )

    assert not result.is_error
    assert "Merci" in result.content[0].text
    [entry] = await tool_store.since(days=1)
    assert entry.tool == "novit_daily"
