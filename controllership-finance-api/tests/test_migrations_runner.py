"""Migration runner — discovery, checksum SHA-256, immutability.

O runner nunca reaplica migration já registrada e aborta se o checksum de
um arquivo aplicado divergir (arquivo aplicado é imutável).
"""

from __future__ import annotations

import hashlib

import pytest

from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)


def _write_migration(directory, name: str, body: str):
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def test_migration_files_sorted(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "MIGRATIONS_DIR", tmp_path)
    _write_migration(tmp_path, "V002__b.sql", "SELECT 2;")
    _write_migration(tmp_path, "V001__a.sql", "SELECT 1;")
    _write_migration(tmp_path, "not-a-migration.sql", "SELECT 0;")

    files = mr._migration_files()
    assert [name for _, name in [(v, p.name) for v, p in files]] == [
        "V001__a.sql",
        "V002__b.sql",
    ]


def test_migration_files_empty_when_dir_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "MIGRATIONS_DIR", tmp_path / "missing")
    assert mr._migration_files() == []


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._conn.executed.append((sql, params))
        if "SELECT version, checksum" in sql:
            self._conn._result = list(self._conn.applied.items())
        else:
            self._conn._result = []

    def fetchall(self):
        return self._conn._result


class _FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, *a):
        return False


class _FakeConn:
    def __init__(self, applied):
        self.applied = applied
        self.executed = []
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self, **_kw):
        return _FakeCursor(self)

    def transaction(self):
        return _FakeTransaction()

    def commit(self):
        return None


def _run(tmp_path, monkeypatch, applied):
    monkeypatch.setattr(mr, "MIGRATIONS_DIR", tmp_path)
    monkeypatch.setattr(mr, "plugins_db_configured", lambda: True)
    conn = _FakeConn(applied)
    monkeypatch.setattr(mr, "plugins_db_connect", lambda: conn)
    return conn


def test_run_migrations_applies_and_records_checksum(tmp_path, monkeypatch):
    conn = _run(tmp_path, monkeypatch, applied={})
    path = _write_migration(tmp_path, "V001__t.sql", "CREATE TABLE x (i int);")

    applied_names = mr.run_migrations()
    assert applied_names == ["V001__t.sql"]

    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    inserts = [
        sql
        for sql, params in conn.executed
        if "INSERT INTO" in sql and "schema_migrations" in sql
    ]
    assert inserts, "checksum não registrado"
    params = conn.executed[-1][1]
    assert params[2] == checksum


def test_run_migrations_skips_applied(tmp_path, monkeypatch):
    path = _write_migration(tmp_path, "V001__t.sql", "SELECT 1;")
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    conn = _run(tmp_path, monkeypatch, applied={1: checksum})

    assert mr.run_migrations() == []
    ddl = [sql for sql, _ in conn.executed if "SELECT 1" in sql]
    assert not ddl


def test_run_migrations_aborts_on_checksum_divergence(tmp_path, monkeypatch):
    _write_migration(tmp_path, "V001__t.sql", "SELECT 999;")
    _run(tmp_path, monkeypatch, applied={1: "0" * 64})

    with pytest.raises(mr.MigrationError, match="checksum divergente"):
        mr.run_migrations()


def test_run_migrations_no_config_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "plugins_db_configured", lambda: False)
    assert mr.run_migrations() == []
