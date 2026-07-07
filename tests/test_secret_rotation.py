import httpx
import pytest
import respx

from config.settings import get_settings, reload_settings
from src.scrapers.cve import NVD_API_URL, CVEScraper


@pytest.fixture(autouse=True)
def restore_settings_cache():
    yield
    get_settings.cache_clear()


class TestReloadSettings:
    def test_reload_picks_up_new_env_value(self, monkeypatch):
        monkeypatch.setenv("NVD_API_KEY", "key-initiale")
        reload_settings()
        assert get_settings().nvd_api_key == "key-initiale"

        monkeypatch.setenv("NVD_API_KEY", "key-rotee")
        reload_settings()
        assert get_settings().nvd_api_key == "key-rotee"

    def test_get_settings_is_cached_between_reloads(self, monkeypatch):
        monkeypatch.setenv("NVD_API_KEY", "stable")
        reload_settings()
        assert get_settings() is get_settings()  # même instance tant que non rechargé


class TestCVEScraperKeyRotation:
    async def test_fetch_uses_freshly_rotated_key_without_restart(self, monkeypatch):
        scraper = CVEScraper()

        monkeypatch.setenv("NVD_API_KEY", "key-avant-rotation")
        reload_settings()
        with respx.mock:
            route = respx.get(NVD_API_URL).mock(
                return_value=httpx.Response(200, json={"vulnerabilities": []})
            )
            await scraper.fetch()
        assert route.calls.last.request.headers["apiKey"] == "key-avant-rotation"

        # Rotation en cours de vie du processus, sans recréer le scraper ni le manager.
        monkeypatch.setenv("NVD_API_KEY", "key-apres-rotation")
        reload_settings()
        with respx.mock:
            route = respx.get(NVD_API_URL).mock(
                return_value=httpx.Response(200, json={"vulnerabilities": []})
            )
            await scraper.fetch()
        assert route.calls.last.request.headers["apiKey"] == "key-apres-rotation"

    async def test_fetch_still_works_without_api_key(self, monkeypatch):
        monkeypatch.delenv("NVD_API_KEY", raising=False)
        reload_settings()
        scraper = CVEScraper()

        with respx.mock:
            route = respx.get(NVD_API_URL).mock(
                return_value=httpx.Response(200, json={"vulnerabilities": []})
            )
            articles = await scraper.fetch()

        assert articles == []
        assert "apiKey" not in route.calls.last.request.headers

    async def test_invalid_key_fails_scraper_without_crashing(self, monkeypatch):
        monkeypatch.setenv("NVD_API_KEY", "key-invalide")
        reload_settings()
        scraper = CVEScraper()

        with respx.mock:
            respx.get(NVD_API_URL).mock(return_value=httpx.Response(403))
            try:
                await scraper.fetch()
                raised = False
            except httpx.HTTPStatusError:
                raised = True

        assert raised  # ScraperManager._run_scraper() capture cette exception en amont
