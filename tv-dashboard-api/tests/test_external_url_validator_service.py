import pytest

from tv_app.application.services.external_url_validator_service import validate_external_url


def test_allows_powerbi_host():
    validate_external_url("https://app.powerbi.com/view?r=abc")


def test_allows_localhost_when_enabled():
    validate_external_url("http://localhost:5173/embed")


def test_rejects_unknown_host():
    with pytest.raises(ValueError, match="Domínio não permitido"):
        validate_external_url("https://evil.example.com/dashboard")


def test_rejects_http_non_localhost():
    with pytest.raises(ValueError, match="https"):
        validate_external_url("http://app.powerbi.com/view")
