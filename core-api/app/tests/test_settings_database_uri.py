import importlib
import os

import pytest


@pytest.mark.parametrize(
    ("password", "expected_fragment"),
    [
        ("simple", "simple"),
        ("D3lp1@2025", "D3lp1%402025"),
        ("p@ss:word/x", "p%40ss%3Aword%2Fx"),
    ],
)
def test_sqlalchemy_database_uri_encodes_password_special_chars(
    password: str,
    expected_fragment: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DB_HOST", "postgres-core")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "delpi_core")
    monkeypatch.setenv("DB_USER", "delpi")
    monkeypatch.setenv("DB_PASSWORD", password)

    settings = importlib.reload(
        importlib.import_module("app.infrastructure.config.settings")
    )
    uri = settings.Config.SQLALCHEMY_DATABASE_URI

    assert expected_fragment in uri
    assert uri.rsplit("@", 1)[-1] == "postgres-core:5432/delpi_core"
