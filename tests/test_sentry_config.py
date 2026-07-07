from unittest.mock import patch

from src.mcp.sentry_config import capture_tool_error, init_sentry


class TestInitSentry:
    def test_noop_without_dsn(self):
        with patch("sentry_sdk.init") as mock_init:
            enabled = init_sentry(dsn="", environment="development")

        assert enabled is False
        mock_init.assert_not_called()

    def test_initializes_with_dsn(self):
        with patch("sentry_sdk.init") as mock_init:
            enabled = init_sentry(
                dsn="https://key@sentry.io/1",
                environment="production",
                traces_sample_rate=0.1,
            )

        assert enabled is True
        mock_init.assert_called_once()
        _, kwargs = mock_init.call_args
        assert kwargs["dsn"] == "https://key@sentry.io/1"
        assert kwargs["environment"] == "production"
        assert kwargs["traces_sample_rate"] == 0.1


class TestCaptureToolError:
    def test_does_not_raise_when_sentry_not_configured(self):
        # Sans sentry_sdk.init() préalable, capture_exception()/push_scope()
        # sont des no-op sûrs côté SDK (pas de client configuré).
        capture_tool_error(
            RuntimeError("boom"),
            tool_name="novit_get_news",
            arguments={"profil": "ETUDIANT", "domaines": ["ia"]},
        )

    def test_sets_expected_tags_and_context(self):
        with patch("sentry_sdk.capture_exception") as mock_capture:
            capture_tool_error(
                RuntimeError("boom"),
                tool_name="novit_get_by_domain",
                arguments={"profil": "INGENIEUR", "domaine": "securite"},
            )

        mock_capture.assert_called_once()
