from collections import defaultdict
from threading import Lock


class MetricsCollector:
    """Collecte les métriques applicatives NovIT en mémoire.

    Exportable au format Prometheus via to_prometheus() ou en dict via to_dict().
    """

    def __init__(self):
        self._lock = Lock()
        self._tool_calls: dict[str, int] = defaultdict(int)
        self._tool_errors: dict[str, int] = defaultdict(int)
        self._source_timings: dict[str, list[float]] = defaultdict(list)
        self._domain_requests: dict[str, int] = defaultdict(int)
        self._profile_requests: dict[str, int] = defaultdict(int)

    def record_tool_call(self, tool: str) -> None:
        with self._lock:
            self._tool_calls[tool] += 1

    def record_tool_error(self, tool: str) -> None:
        with self._lock:
            self._tool_errors[tool] += 1

    def record_source_timing(self, source: str, duration_ms: float) -> None:
        with self._lock:
            self._source_timings[source].append(duration_ms)

    def record_domain_request(self, domain: str) -> None:
        with self._lock:
            self._domain_requests[domain] += 1

    def record_profile_request(self, profile: str) -> None:
        with self._lock:
            self._profile_requests[profile] += 1

    def to_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            for tool, count in self._tool_calls.items():
                lines.append(f'novit_tool_calls_total{{tool="{tool}"}} {count}')
            for tool, count in self._tool_errors.items():
                lines.append(f'novit_tool_errors_total{{tool="{tool}"}} {count}')
            for source, timings in self._source_timings.items():
                avg = sum(timings) / len(timings)
                lines.append(
                    f'novit_source_latency_avg_ms{{source="{source}"}} {avg:.1f}'
                )
            for domain, count in self._domain_requests.items():
                lines.append(
                    f'novit_domain_requests_total{{domain="{domain}"}} {count}'
                )
            for profile, count in self._profile_requests.items():
                lines.append(
                    f'novit_profile_requests_total{{profile="{profile}"}} {count}'
                )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "tool_calls": dict(self._tool_calls),
                "tool_errors": dict(self._tool_errors),
                "domain_requests": dict(self._domain_requests),
                "profile_requests": dict(self._profile_requests),
            }

    def reset(self) -> None:
        with self._lock:
            self._tool_calls.clear()
            self._tool_errors.clear()
            self._source_timings.clear()
            self._domain_requests.clear()
            self._profile_requests.clear()


metrics = MetricsCollector()
