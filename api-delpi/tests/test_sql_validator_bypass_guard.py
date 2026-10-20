"""Guardrails for privileged /data/sql table allowlist bypass."""
import pytest

from app.application.services.sql_validator import SqlValidator


def test_bypass_default_keeps_ast_table_policy(monkeypatch):
    monkeypatch.delenv("DATA_SQL_SKIP_TABLE_WHITELIST", raising=False)
    v = SqlValidator()
    assert v.validate("SELECT TOP 1 FK2_DATA FROM FK2010") is True


def test_bypass_explicitly_disabled_rejects_nonlisted_table(monkeypatch):
    monkeypatch.setenv("DATA_SQL_SKIP_TABLE_WHITELIST", "false")
    v = SqlValidator()
    with pytest.raises(PermissionError, match="whitelist"):
        v.validate("SELECT TOP 1 FK2_DATA FROM FK2010")


@pytest.mark.parametrize("sql", [
    "SELECT * INTO copied_rows FROM FK2010",
    "SELECT * FROM otherdb.dbo.FK2010",
    "DELETE FROM FK2010",
    "SELECT * FROM FK2010, FK1010",
    "SELECT * FROM FK2010 CROSS APPLY (SELECT 1 AS x) q",
])
def test_bypass_does_not_skip_sql_security_validation(monkeypatch, sql):
    monkeypatch.setenv("DATA_SQL_SKIP_TABLE_WHITELIST", "true")
    v = SqlValidator()
    with pytest.raises((PermissionError, ValueError)):
        v.validate(sql)
