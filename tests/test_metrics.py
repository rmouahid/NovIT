from src.mcp.metrics import MetricsCollector


class TestMetricsCollector:
    def test_record_tool_call(self):
        m = MetricsCollector()
        m.record_tool_call("novit_get_news")
        m.record_tool_call("novit_get_news")
        assert m.to_dict()["tool_calls"]["novit_get_news"] == 2

    def test_record_tool_error(self):
        m = MetricsCollector()
        m.record_tool_error("novit_search")
        assert m.to_dict()["tool_errors"]["novit_search"] == 1

    def test_record_domain_request(self):
        m = MetricsCollector()
        m.record_domain_request("ia")
        m.record_domain_request("ia")
        m.record_domain_request("dev")
        d = m.to_dict()["domain_requests"]
        assert d["ia"] == 2
        assert d["dev"] == 1

    def test_record_profile_request(self):
        m = MetricsCollector()
        m.record_profile_request("ETUDIANT")
        assert m.to_dict()["profile_requests"]["ETUDIANT"] == 1

    def test_to_dict_empty_by_default(self):
        m = MetricsCollector()
        d = m.to_dict()
        assert d == {
            "tool_calls": {},
            "tool_errors": {},
            "domain_requests": {},
            "profile_requests": {},
        }

    def test_to_prometheus_format(self):
        m = MetricsCollector()
        m.record_tool_call("novit_get_news")
        m.record_source_timing("hacker_news", 120.0)
        output = m.to_prometheus()
        assert 'novit_tool_calls_total{tool="novit_get_news"} 1' in output
        assert 'novit_source_latency_avg_ms{source="hacker_news"} 120.0' in output

    def test_source_timing_average(self):
        m = MetricsCollector()
        m.record_source_timing("rss", 100.0)
        m.record_source_timing("rss", 200.0)
        output = m.to_prometheus()
        assert 'novit_source_latency_avg_ms{source="rss"} 150.0' in output

    def test_reset_clears_all_metrics(self):
        m = MetricsCollector()
        m.record_tool_call("novit_get_news")
        m.record_tool_error("novit_get_news")
        m.record_domain_request("ia")
        m.record_profile_request("ETUDIANT")
        m.reset()
        assert m.to_dict() == {
            "tool_calls": {},
            "tool_errors": {},
            "domain_requests": {},
            "profile_requests": {},
        }
        assert m.to_prometheus() == ""
