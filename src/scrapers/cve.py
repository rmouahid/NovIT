import os
from datetime import datetime, timedelta, timezone

import feedparser
import httpx
from loguru import logger

from src.scrapers.base import Article, BaseScraper

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
ANSSI_RSS_URL = "https://www.cert.ssi.gouv.fr/feed/"

CVSS_SEVERITY = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "NONE": 0,
}


def _cvss_score_to_severity(score: float) -> str:
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"


class CVEScraper(BaseScraper):
    """Récupère les CVE récents via l'API NVD (National Vulnerability Database)."""

    name = "cve_nvd"
    domains = ["securite"]
    profiles = ["INGENIEUR"]

    def __init__(self, min_cvss: float = 7.0, days_back: int = 7):
        self.min_cvss = min_cvss
        self.days_back = days_back
        self._api_key = os.getenv("NVD_API_KEY", "")

    async def fetch(self) -> list[Article]:
        since = datetime.now(tz=timezone.utc) - timedelta(days=self.days_back)
        pub_start = since.strftime("%Y-%m-%dT%H:%M:%S.000")
        pub_end = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")

        params = {
            "pubStartDate": pub_start,
            "pubEndDate": pub_end,
            "cvssV3Severity": "HIGH",
            "resultsPerPage": 50,
        }
        headers = {}
        if self._api_key:
            headers["apiKey"] = self._api_key

        logger.debug(f"[{self.name}] Requête NVD API (CVSS >= {self.min_cvss})")

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(NVD_API_URL, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()

        articles: list[Article] = []
        for vuln in data.get("vulnerabilities", []):
            cve = vuln.get("cve", {})
            article = self._cve_to_article(cve)
            if article:
                articles.append(article)

        logger.info(f"[{self.name}] {len(articles)} CVE récupérées")
        return articles

    def _cve_to_article(self, cve: dict) -> Article | None:
        cve_id = cve.get("id", "")
        if not cve_id:
            return None

        descriptions = cve.get("descriptions", [])
        desc_en = next((d["value"] for d in descriptions if d["lang"] == "en"), "")

        metrics = cve.get("metrics", {})
        cvss_score = 0.0
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            metric_list = metrics.get(key, [])
            if metric_list:
                cvss_score = metric_list[0].get("cvssData", {}).get("baseScore", 0.0)
                break

        if cvss_score < self.min_cvss:
            return None

        severity = _cvss_score_to_severity(cvss_score)
        published_str = cve.get("published", "")
        try:
            published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc)

        summary = f"🔴 CVSS {cvss_score} ({severity}) — {desc_en[:300]}"

        return Article(
            title=f"{cve_id} — {severity} (CVSS {cvss_score})",
            url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            summary=summary,
            published_at=published_at,
            source=self.name,
            domains=["securite"],
            profiles=["INGENIEUR"],
            score=cvss_score / 10.0,
            extra={"cvss": cvss_score, "severity": severity, "cve_id": cve_id},
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.head(NVD_API_URL)
                return r.status_code < 500
        except Exception:
            return False


class ANSSIScraper(BaseScraper):
    """Récupère les alertes de sécurité ANSSI (Cert-FR) via flux RSS."""

    name = "anssi_cert"
    domains = ["securite", "reglementation"]
    profiles = ["INGENIEUR"]

    async def fetch(self) -> list[Article]:
        logger.debug(f"[{self.name}] Lecture du flux RSS ANSSI")
        feed = feedparser.parse(ANSSI_RSS_URL)
        articles: list[Article] = []

        for entry in feed.entries:
            try:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if hasattr(entry, "published_parsed") and entry.published_parsed else datetime.now(tz=timezone.utc)
                articles.append(Article(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    summary=entry.get("summary", "")[:500],
                    published_at=published_at,
                    source=self.name,
                    domains=["securite"],
                    profiles=["INGENIEUR"],
                    score=0.8,
                    extra={"feed": "cert-fr"},
                ))
            except Exception as e:
                logger.warning(f"[{self.name}] Erreur entry RSS : {e}")

        logger.info(f"[{self.name}] {len(articles)} alertes ANSSI récupérées")
        return articles

    async def health_check(self) -> bool:
        try:
            feed = feedparser.parse(ANSSI_RSS_URL)
            return feed.bozo is False and len(feed.entries) > 0
        except Exception:
            return False
