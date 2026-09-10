from datetime import UTC, datetime, timedelta

from src.mcp.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
)


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb.is_available is True

    def test_trips_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.is_available is False

    def test_single_failure_below_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.is_available is True

    def test_half_open_after_recovery_delay(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_minutes=30)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb._opened_at = datetime.now(tz=UTC) - timedelta(minutes=31)
        assert cb.state == CircuitState.HALF_OPEN

    def test_success_closes_from_half_open(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        cb.record_failure()
        cb._state = CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb._failures == 0

    def test_failure_in_half_open_reopens(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        cb.record_failure()
        cb._state = CircuitState.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker("test", failure_threshold=5)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb._failures == 0

    def test_to_dict(self):
        cb = CircuitBreaker("source_a", failure_threshold=2)
        cb.record_failure()
        d = cb.to_dict()
        assert d["name"] == "source_a"
        assert d["state"] == CircuitState.CLOSED.value
        assert d["failures"] == 1
        assert d["opened_at"] is None

    def test_to_dict_open_state(self):
        cb = CircuitBreaker("source_b", failure_threshold=1)
        cb.record_failure()
        d = cb.to_dict()
        assert d["state"] == CircuitState.OPEN.value
        assert d["opened_at"] is not None


class TestCircuitBreakerRegistry:
    def test_get_creates_breaker(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get("source_x")
        assert cb.name == "source_x"

    def test_get_returns_same_instance(self):
        reg = CircuitBreakerRegistry()
        cb1 = reg.get("source_y")
        cb2 = reg.get("source_y")
        assert cb1 is cb2

    def test_open_sources_empty_initially(self):
        reg = CircuitBreakerRegistry()
        reg.get("source_a")
        assert reg.open_sources() == []

    def test_open_sources_lists_tripped(self):
        reg = CircuitBreakerRegistry(failure_threshold=1)
        cb = reg.get("source_a")
        cb.record_failure()
        assert "source_a" in reg.open_sources()

    def test_all_status(self):
        reg = CircuitBreakerRegistry(failure_threshold=2)
        reg.get("source_a").record_failure()
        reg.get("source_b")
        statuses = reg.all_status()
        assert len(statuses) == 2
        names = [s["name"] for s in statuses]
        assert "source_a" in names
        assert "source_b" in names
