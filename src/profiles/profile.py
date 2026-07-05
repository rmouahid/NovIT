from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

ProfileName = Literal["ETUDIANT", "INGENIEUR"]

_CONFIG_PATH = Path("config/profiles.yaml")


@dataclass
class ProfileConfig:
    name: str
    label: str
    description: str
    sources_prioritaires: list[str] = field(default_factory=list)
    domaines_favoris: list[str] = field(default_factory=list)
    domaines_secondaires: list[str] = field(default_factory=list)
    niveau_detail: str = "court"
    score_min: float = 0.3
    nb_articles_defaut: int = 10


class Profile:
    """Représente un profil NovIT chargé depuis config/profiles.yaml."""

    def __init__(self, config: ProfileConfig):
        self._config = config

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def label(self) -> str:
        return self._config.label

    @property
    def domaines_favoris(self) -> list[str]:
        return self._config.domaines_favoris

    @property
    def sources_prioritaires(self) -> list[str]:
        return self._config.sources_prioritaires

    @property
    def score_min(self) -> float:
        return self._config.score_min

    @property
    def nb_articles_defaut(self) -> int:
        return self._config.nb_articles_defaut

    def source_weight(self, source: str) -> float:
        """Retourne le poids d'une source pour ce profil (1.5 prioritaire, 1.0 normal)."""
        return 1.5 if source in self._config.sources_prioritaires else 1.0

    def domain_weight(self, domain: str) -> float:
        """Retourne le poids d'un domaine pour ce profil."""
        if domain in self._config.domaines_favoris:
            return 1.5
        if domain in self._config.domaines_secondaires:
            return 1.0
        return 0.6

    def to_summary(self) -> str:
        return (
            f"**{self._config.label}**\n"
            f"{self._config.description}\n\n"
            f"- Sources prioritaires : {', '.join(self._config.sources_prioritaires[:5])}\n"
            f"- Domaines favoris : {', '.join(self._config.domaines_favoris)}\n"
            f"- Niveau de détail : {self._config.niveau_detail}\n"
            f"- Score minimum : {self._config.score_min}"
        )


def load_profiles(config_path: Path = _CONFIG_PATH) -> dict[str, Profile]:
    """Charge tous les profils depuis le fichier YAML."""
    if not config_path.exists():
        raise FileNotFoundError(f"Fichier de profils introuvable : {config_path}")
    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    profiles: dict[str, Profile] = {}
    for name, info in data.get("profiles", {}).items():
        config = ProfileConfig(name=name, **{k: v for k, v in info.items()})
        profiles[name] = Profile(config)
    return profiles


# Instance globale
_profiles: dict[str, Profile] | None = None


def get_profile(name: str) -> Profile:
    global _profiles
    if _profiles is None:
        _profiles = load_profiles()
    profile = _profiles.get(name.upper())
    if not profile:
        raise ValueError(f"Profil inconnu : '{name}'. Disponibles : {list(_profiles.keys())}")
    return profile
