from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum

from loguru import logger


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Coupe-circuit par source : désactive une source après N échecs consécutifs.

    Réactivation automatique après recovery_minutes. Transitions :
    CLOSED → OPEN (N échecs) → HALF_OPEN (timeout) → CLOSED (succès) ou OPEN (échec).
    """

    name: str
    failure_threshold: int = 3
    recovery_minutes: int = 30

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _failures: int = field(default=0, init=False, repr=False)
    _opened_at: datetime | None = field(default=None, init=False, repr=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at:
            elapsed = datetime.now(tz=UTC) - self._opened_at
            if elapsed >= timedelta(minutes=self.recovery_minutes):
                self._state = CircuitState.HALF_OPEN
                logger.info(
                    f"[circuit_breaker] {self.name} → HALF_OPEN (tentative récupération)"
                )
        return self._state

    @property
    def is_available(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        if self._state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
            logger.info(f"[circuit_breaker] {self.name} → CLOSED (récupéré)")
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if (
            self._state == CircuitState.HALF_OPEN
            or self._failures >= self.failure_threshold
        ):
            self._trip()

    def _trip(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = datetime.now(tz=UTC)
        logger.warning(
            f"[circuit_breaker] {self.name} → OPEN "
            f"({self._failures} échecs, récupération dans {self.recovery_minutes}min)"
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self._failures,
            "opened_at": self._opened_at.isoformat() if self._opened_at else None,
        }


class CircuitBreakerRegistry:
    """Registre centralisé des coupe-circuits par source."""

    def __init__(self, failure_threshold: int = 3, recovery_minutes: int = 30):
        self._breakers: dict[str, CircuitBreaker] = {}
        self.failure_threshold = failure_threshold
        self.recovery_minutes = recovery_minutes

    def get(self, source: str) -> CircuitBreaker:
        if source not in self._breakers:
            self._breakers[source] = CircuitBreaker(
                name=source,
                failure_threshold=self.failure_threshold,
                recovery_minutes=self.recovery_minutes,
            )
        return self._breakers[source]

    def all_status(self) -> list[dict]:
        return [cb.to_dict() for cb in self._breakers.values()]

    def open_sources(self) -> list[str]:
        return [
            name for name, cb in self._breakers.items() if cb.state == CircuitState.OPEN
        ]


registry = CircuitBreakerRegistry()
