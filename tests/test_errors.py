import pytest

from src.mcp.errors import NovitError, NovitErrorCode


def test_error_str():
    err = NovitError(NovitErrorCode.INVALID_PROFILE, "Profil inconnu")
    assert "[NOVIT_INVALID_PROFILE]" in str(err)
    assert "Profil inconnu" in str(err)


def test_to_mcp_error_contains_code():
    err = NovitError(NovitErrorCode.SOURCE_UNAVAILABLE, "Source down")
    msg = err.to_mcp_error()
    assert "NOVIT_SOURCE_UNAVAILABLE" in msg
    assert "Source down" in msg


def test_to_mcp_error_all_codes():
    for code in NovitErrorCode:
        err = NovitError(code, "test message")
        result = err.to_mcp_error()
        assert code.value in result
        assert "test message" in result


def test_is_exception():
    err = NovitError(NovitErrorCode.INTERNAL_ERROR, "boom")
    assert isinstance(err, Exception)


def test_attributes():
    err = NovitError(NovitErrorCode.NO_RESULTS, "rien trouvé")
    assert err.code == NovitErrorCode.NO_RESULTS
    assert err.message == "rien trouvé"


def test_raise_and_catch():
    with pytest.raises(NovitError) as exc_info:
        raise NovitError(NovitErrorCode.CACHE_ERROR, "cache fail")
    assert exc_info.value.code == NovitErrorCode.CACHE_ERROR
