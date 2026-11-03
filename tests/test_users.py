"""Multi-utilisateurs (#87) : un jeton par utilisateur, préférences et
sessions isolées, aucune fuite entre utilisateurs."""

import httpx
import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from novit.mcp import onboarding, server
from novit.mcp.http import create_http_app
from novit.mcp.session import SessionManager
from novit.mcp.users import DEFAULT_USER, as_user, current_user, parse_api_tokens
from novit.profiles import preferences
from novit.profiles.preferences import PreferencesStore
from tests.test_http import _serve

ALICE, BOB = "jeton-alice", "jeton-bob"


class TestParseApiTokens:
    def test_maps_each_token_to_its_user(self):
        assert parse_api_tokens("alice:t1, bob:t2,") == {"t1": "alice", "t2": "bob"}

    def test_empty_means_no_user(self):
        assert parse_api_tokens("") == {}

    @pytest.mark.parametrize(
        "raw, message",
        [
            ("alice", "sans jeton"),
            ("alice:", "sans jeton"),
            ("../etc:t1", "invalide"),
            ("Alice:t1", "invalide"),
            ("alice:t1,alice:t2", "en double"),
            ("alice:t1,bob:t1", "même jeton"),
        ],
    )
    def test_rejects_invalid_entries(self, raw, message):
        with pytest.raises(ValueError, match=message):
            parse_api_tokens(raw)


def test_as_user_restores_the_previous_user():
    with as_user("alice"):
        assert current_user.get() == "alice"
    assert current_user.get() == DEFAULT_USER


class TestPreferencesIsolation:
    def test_each_user_has_its_own_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(preferences, "_PREFS_PATH", tmp_path / "prefs.json")
        store = PreferencesStore(users_dir=tmp_path / "users")

        with as_user("alice"):
            store.update(profil="INGENIEUR", domaines_favoris=["securite"])
        with as_user("bob"):
            assert store.load().profil is None
            store.update(profil="ETUDIANT")
        store.update(domaines_favoris=["ia"])

        with as_user("alice"):
            assert store.load().profil == "INGENIEUR"
            assert store.load().domaines_favoris == ["securite"]
        assert store.load().profil is None
        assert (tmp_path / "users" / "alice.json").exists()
        assert (tmp_path / "prefs.json").exists()

    def test_explicit_path_ignores_the_user(self, tmp_path):
        store = PreferencesStore(path=tmp_path / "fixe.json")
        with as_user("alice"):
            store.update(profil="ETUDIANT")
        assert store.load().profil == "ETUDIANT"


class TestSessionIsolation:
    def test_same_session_id_is_distinct_per_user(self):
        sessions = SessionManager()
        with as_user("alice"):
            sessions.get_or_create("s1").seen_urls.add("https://a.example")
        with as_user("bob"):
            assert sessions.get_or_create("s1").seen_urls == set()
            sessions.reset("s1")
        with as_user("alice"):
            assert sessions.get_or_create("s1").seen_urls == {"https://a.example"}


def test_network_listening_accepts_per_user_tokens_only():
    assert create_http_app(server.app, "0.0.0.0", "", users={ALICE: "alice"})


def test_shared_token_cannot_also_be_a_user_token():
    with pytest.raises(ValueError, match="aussi le jeton"):
        create_http_app(server.app, "127.0.0.1", ALICE, users={ALICE: "alice"})


@pytest.fixture
def multi_user_url(tmp_path, monkeypatch):
    monkeypatch.setattr(preferences, "_PREFS_PATH", tmp_path / "prefs.json")
    monkeypatch.setattr(preferences.prefs_store, "_users_dir", tmp_path / "users")
    app = create_http_app(
        server.app, "127.0.0.1", "", users={ALICE: "alice", BOB: "bob"}
    )
    uv, thread, url = _serve(app)
    yield url
    uv.should_exit = True
    thread.join(timeout=10)


def _client(url, token):
    http_client = httpx2.AsyncClient(headers={"Authorization": f"Bearer {token}"})
    return Client(streamable_http_client(f"{url}/mcp", http_client=http_client))


async def _welcome(url, token) -> str:
    async with _client(url, token) as client:
        result = await client.call_tool("novit_start", {})
    return result.content[0].text


async def test_profiles_do_not_leak_between_users_over_http(multi_user_url):
    async with _client(multi_user_url, ALICE) as alice:
        await alice.call_tool("novit_set_profile", {"profil": "INGENIEUR"})
    # Bob n'a encore rien choisi : il doit voir le menu, pas le profil d'Alice.
    assert await _welcome(multi_user_url, BOB) == onboarding._PROFILE_SELECTION

    async with _client(multi_user_url, BOB) as bob:
        await bob.call_tool("novit_set_profile", {"profil": "ETUDIANT"})

    menu = onboarding._DOMAINS_MENU
    assert await _welcome(multi_user_url, ALICE) == (
        onboarding._WELCOME_INGENIEUR.format(domains_menu=menu)
    )
    assert await _welcome(multi_user_url, BOB) == (
        onboarding._WELCOME_ETUDIANT.format(domains_menu=menu)
    )


def test_unknown_token_is_rejected(multi_user_url):
    response = httpx.post(
        f"{multi_user_url}/mcp", headers={"Authorization": "Bearer inconnu"}
    )
    assert response.status_code == 401
