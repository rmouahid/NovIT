"""Tests des outils de session : onboarding, profil et domaines.

Les préférences sont écrites dans un fichier temporaire, jamais dans celui
du projet.
"""

import pytest

from src.mcp import domain_selector, onboarding, profile_selector
from src.profiles.preferences import PreferencesStore


@pytest.fixture
def prefs(tmp_path, monkeypatch):
    store = PreferencesStore(path=tmp_path / "prefs.json")
    for module in (onboarding, profile_selector, domain_selector):
        monkeypatch.setattr(module, "prefs_store", store)
    return store


async def test_start_without_profile_asks_to_choose_one(prefs):
    message = await onboarding.start_novit()

    assert "quel est ton profil" in message


async def test_start_with_a_profile_welcomes_the_user(prefs):
    message = await onboarding.start_novit("INGENIEUR")

    assert "Profil : **INGENIEUR**" in message
    assert "`securite`" in message


async def test_start_uses_the_saved_profile(prefs):
    prefs.update(profil="ETUDIANT")

    message = await onboarding.start_novit()

    assert "Profil activé : **ETUDIANT**" in message


async def test_select_profile_persists_it(prefs):
    message = await profile_selector.select_profile(" ingenieur ")

    assert "INGENIEUR" in message and "activé" in message
    assert prefs.load().profil == "INGENIEUR"


async def test_unknown_profile_is_refused_and_not_saved(prefs):
    message = await profile_selector.select_profile("MANAGER")

    assert "Je ne connais pas" in message
    assert prefs.load().profil != "MANAGER"


async def test_current_profile_summary(prefs):
    assert "Aucun profil" in await profile_selector.get_current_profile()

    await profile_selector.select_profile("INGENIEUR")

    assert (
        "**Profil actif :** INGENIEUR" in await profile_selector.get_current_profile()
    )


async def test_set_domains_persists_the_resolved_domains(prefs):
    message = await domain_selector.set_domains("ia, cyber")

    assert "Domaines actifs" in message
    assert prefs.load().domaines_favoris == ["ia", "securite"]


async def test_unknown_domains_are_not_saved(prefs):
    before = prefs.load().domaines_favoris

    message = await domain_selector.set_domains("jardinage")

    assert "pas reconnu" in message
    assert prefs.load().domaines_favoris == before
