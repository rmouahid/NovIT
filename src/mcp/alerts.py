from dataclasses import dataclass
from enum import StrEnum

from src.scrapers.base import Article


class AlertLevel(StrEnum):
    INFO = "info"
    IMPORTANT = "important"
    CRITIQUE = "critique"


@dataclass
class Alert:
    keyword: str
    level: AlertLevel = AlertLevel.INFO

    def emoji(self) -> str:
        return {"info": "ℹ️", "important": "⚠️", "critique": "🚨"}[self.level]


class AlertManager:
    def __init__(self):
        self._alerts: list[Alert] = []

    def add(self, keyword: str, level: str = "info") -> str:
        try:
            lvl = AlertLevel(level.lower())
        except ValueError:
            lvl = AlertLevel.INFO
        alert = Alert(keyword=keyword.lower(), level=lvl)
        self._alerts.append(alert)
        return f"Alerte ajoutée : {alert.emoji()} **{keyword}** ({level})"

    def remove(self, keyword: str) -> str:
        before = len(self._alerts)
        self._alerts = [a for a in self._alerts if a.keyword != keyword.lower()]
        removed = before - len(self._alerts)
        return (
            f"{removed} alerte(s) supprimée(s) pour '{keyword}'"
            if removed
            else f"Aucune alerte pour '{keyword}'"
        )

    def list_alerts(self) -> str:
        if not self._alerts:
            return "Aucune alerte configurée."
        lines = ["**Alertes actives :**"]
        for alert in self._alerts:
            lines.append(f"- {alert.emoji()} `{alert.keyword}` ({alert.level.value})")
        return "\n".join(lines)

    async def check(self, articles: list[Article]) -> str:
        if not self._alerts or not articles:
            return ""
        triggered: list[tuple[Alert, Article]] = []
        for alert in self._alerts:
            for article in articles:
                text = f"{article.title} {article.summary}".lower()
                if alert.keyword in text:
                    triggered.append((alert, article))

        if not triggered:
            return ""

        lines = ["## 🔔 Alertes déclenchées\n"]
        for alert, article in triggered[:10]:
            lines.append(
                f"{alert.emoji()} **[{alert.keyword}]** — [{article.title}]({article.url}) · {article.source}"
            )
        return "\n".join(lines)


alert_manager = AlertManager()
