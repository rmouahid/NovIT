from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from src.scrapers.base import Article

_SESSION_TTL_HOURS = 24
_MAX_HISTORY = 100


@dataclass
class SessionState:
    seen_urls: set[str] = field(default_factory=set)
    history: deque = field(default_factory=lambda: deque(maxlen=_MAX_HISTORY))
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    last_active: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    current_index: int = 0
    current_results: list[Article] = field(default_factory=list)


class SessionManager:
    """Gère le contexte de conversation par session MCP.

    Chaque connexion MCP dispose d'une session isolée qui mémorise :
    - Les articles déjà montrés (évite la répétition)
    - L'historique de navigation (suivant/précédent)
    - Les résultats courants pour la navigation

    Les sessions expirent après 24h d'inactivité.
    """

    def __init__(self):
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str = "default") -> SessionState:
        session = self._sessions.get(session_id)
        if session is None or self._is_expired(session):
            session = SessionState()
            self._sessions[session_id] = session
        session.last_active = datetime.now(tz=timezone.utc)
        return session

    def _is_expired(self, session: SessionState) -> bool:
        return datetime.now(tz=timezone.utc) - session.last_active > timedelta(hours=_SESSION_TTL_HOURS)

    def mark_seen(self, session_id: str, articles: list[Article]) -> None:
        session = self.get_or_create(session_id)
        for article in articles:
            session.seen_urls.add(article.url)
            session.history.append({"url": article.url, "title": article.title})

    def filter_unseen(self, session_id: str, articles: list[Article]) -> list[Article]:
        """Retourne uniquement les articles pas encore montrés dans cette session."""
        session = self.get_or_create(session_id)
        return [a for a in articles if a.url not in session.seen_urls]

    def set_results(self, session_id: str, articles: list[Article]) -> None:
        session = self.get_or_create(session_id)
        session.current_results = articles
        session.current_index = 0

    def next_article(self, session_id: str) -> Article | None:
        session = self.get_or_create(session_id)
        if session.current_index >= len(session.current_results):
            return None
        article = session.current_results[session.current_index]
        session.current_index += 1
        self.mark_seen(session_id, [article])
        return article

    def prev_article(self, session_id: str) -> Article | None:
        session = self.get_or_create(session_id)
        if session.current_index <= 1:
            return None
        session.current_index -= 2
        return session.current_results[session.current_index] if session.current_results else None

    def position(self, session_id: str) -> tuple[int, int]:
        session = self.get_or_create(session_id)
        return session.current_index, len(session.current_results)

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def purge_expired(self) -> int:
        before = len(self._sessions)
        self._sessions = {sid: s for sid, s in self._sessions.items() if not self._is_expired(s)}
        return before - len(self._sessions)


session_manager = SessionManager()
