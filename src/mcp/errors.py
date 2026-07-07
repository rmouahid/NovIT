from enum import Enum


class NovitErrorCode(str, Enum):
    SOURCE_UNAVAILABLE = "NOVIT_SOURCE_UNAVAILABLE"
    SOURCE_TIMEOUT = "NOVIT_SOURCE_TIMEOUT"
    NO_RESULTS = "NOVIT_NO_RESULTS"
    INVALID_PROFILE = "NOVIT_INVALID_PROFILE"
    INVALID_DOMAIN = "NOVIT_INVALID_DOMAIN"
    CACHE_ERROR = "NOVIT_CACHE_ERROR"
    SCRAPER_ERROR = "NOVIT_SCRAPER_ERROR"
    INTERNAL_ERROR = "NOVIT_INTERNAL_ERROR"


class NovitError(Exception):
    def __init__(self, code: NovitErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code.value}] {message}")

    def to_mcp_error(self) -> str:
        return f"Erreur NovIT [{self.code.value}] : {self.message}"
