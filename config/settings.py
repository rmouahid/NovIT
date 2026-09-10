from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NOVIT_",
        case_sensitive=False,
        extra="ignore",
    )

    # Serveur
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_dir: str = ""

    # Cache (secondes)
    cache_ttl_default: int = Field(default=3600, ge=0)
    cache_ttl_news: int = Field(default=3600, ge=0)
    cache_ttl_profile: int = Field(default=86400, ge=0)

    # Base de données
    db_path: str = "./novit.db"
    database_url: str = ""

    # Scraping
    scraper_delay: float = Field(default=1.0, ge=0)
    scraper_timeout: int = Field(default=10, ge=1)
    user_agent: str = "NovIT/0.1.0 (veille technologique MCP)"
    retention_days: int = Field(default=7, ge=1)

    # Dossier de scrapers plugin (voir docs/PLUGINS.md) — vide/inexistant = aucun plugin chargé.
    plugins_dir: str = "plugins"

    # Profil par défaut
    default_profile: Literal["ETUDIANT", "INGENIEUR"] = "ETUDIANT"

    # Monitoring d'erreurs (Sentry) — désactivé si sentry_dsn est vide.
    # Pas de préfixe NOVIT_ : convention Sentry standard, cf. .env.example.
    sentry_dsn: str = Field(default="", validation_alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, validation_alias="SENTRY_TRACES_SAMPLE_RATE"
    )

    # Clés API externes (rotatives — voir docs/SECRET_ROTATION.md).
    # Pas de préfixe NOVIT_ : ce sont les noms des clés côté fournisseur.
    nvd_api_key: str = Field(default="", validation_alias="NVD_API_KEY")
    github_token: str = Field(default="", validation_alias="GITHUB_TOKEN")

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        return v.upper()

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retourne l'instance de configuration (singleton mis en cache)."""
    return Settings()


def reload_settings() -> Settings:
    """Invalide le cache de configuration et relit .env/l'environnement.

    Permet de faire tourner une clé API (NVD_API_KEY, GITHUB_TOKEN...) sans
    redémarrer le serveur : mettre à jour .env (ou la variable d'env), puis
    appeler reload_settings(). Les prochains appels aux scrapers concernés
    liront la nouvelle valeur — voir docs/SECRET_ROTATION.md.
    """
    get_settings.cache_clear()
    return get_settings()
