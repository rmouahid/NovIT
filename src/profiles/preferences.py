import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from loguru import logger

_PREFS_PATH = Path(".novit_prefs.json")


@dataclass
class UserPreferences:
    profil: Literal["ETUDIANT", "INGENIEUR"] | None = None
    sources_favorites: list[str] = field(default_factory=list)
    sources_exclues: list[str] = field(default_factory=list)
    domaines_favoris: list[str] = field(default_factory=list)
    domaines_exclus: list[str] = field(default_factory=list)
    niveau_detail: Literal["court", "detaille"] = "court"
    langue: Literal["fr", "en"] = "fr"


class PreferencesStore:
    """Stockage persistant des préférences utilisateur dans un fichier JSON local.

    Le fichier est créé à la racine du projet et ignoré par git (.gitignore).
    Pas de base de données — les préférences sont propres à chaque installation.
    """

    def __init__(self, path: Path = _PREFS_PATH):
        self._path = path

    def load(self) -> UserPreferences:
        if not self._path.exists():
            return UserPreferences()
        try:
            with self._path.open(encoding="utf-8") as f:
                data = json.load(f)
            return UserPreferences(**{k: v for k, v in data.items() if k in UserPreferences.__dataclass_fields__})
        except Exception as e:
            logger.warning(f"[prefs] Erreur lecture préférences : {e} — réinitialisation")
            return UserPreferences()

    def save(self, prefs: UserPreferences) -> None:
        try:
            with self._path.open("w", encoding="utf-8") as f:
                json.dump(asdict(prefs), f, indent=2, ensure_ascii=False)
            logger.debug(f"[prefs] Préférences sauvegardées dans {self._path}")
        except Exception as e:
            logger.error(f"[prefs] Erreur écriture préférences : {e}")

    def update(self, **kwargs) -> UserPreferences:
        prefs = self.load()
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        self.save(prefs)
        return prefs

    def reset(self) -> UserPreferences:
        prefs = UserPreferences()
        self.save(prefs)
        return prefs


prefs_store = PreferencesStore()
