import pytest

from app.application.services.sql_validator import SqlValidator


def test_rejects_table_outside_allowlist_when_skip_disabled(monkeypatch) -> None:
    monkeypatch.delenv("DATA_SQL_SKIP_TABLE_WHITELIST", raising=False)
    validator = SqlValidator()
    with pytest.raises(PermissionError, match="não autorizada"):
        validator.validate("SELECT TOP 1 1 AS ok FROM SUS010 WHERE D_E_L_E_T_ = '';")


def test_allows_crm_table_when_skip_enabled(monkeypatch) -> None:
    monkeypatch.setenv("DATA_SQL_SKIP_TABLE_WHITELIST", "true")
    validator = SqlValidator()
    assert validator.validate("SELECT TOP 1 1 AS ok FROM SUS010 WHERE D_E_L_E_T_ = '';") is True
    assert validator.validate("SELECT TOP 1 1 AS ok FROM AD8010 WHERE D_E_L_E_T_ = '';") is True


def test_skip_does_not_allow_dml(monkeypatch) -> None:
    monkeypatch.setenv("DATA_SQL_SKIP_TABLE_WHITELIST", "true")
    validator = SqlValidator()
    with pytest.raises(PermissionError, match="permitidas|proibido"):
        validator.validate("DELETE FROM SUS010 WHERE D_E_L_E_T_ = '';")
