"""SEC-01 B — o runner da api-delpi não apaga o schema do LNF."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest


MESSAGE = (
    "O schema lancamento_notas_fiscais pertence à controllership-finance-api "
    "(ADR-001 / trilha 165 D2). Operações destrutivas pela api-delpi estão bloqueadas."
)


def _load_migrations_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_plugins_migrations.py"
    )
    name = "run_plugins_migrations_lnf_block_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _forbid_database(module, monkeypatch):
    def _blocked():
        raise AssertionError("o banco não pode ser acessado")

    monkeypatch.setattr(module, "get_connection", _blocked)


def test_reset_lnf_refuses_without_touching_the_database(monkeypatch):
    module = _load_migrations_module()
    _forbid_database(module, monkeypatch)
    with pytest.raises(module.MigrationError, match=re.escape(MESSAGE)):
        module.reset_plugin_migrations("lancamento-notas-fiscais")


def test_cli_reset_lnf_exits_nonzero_without_touching_the_database(monkeypatch, capsys):
    module = _load_migrations_module()
    _forbid_database(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_plugins_migrations.py",
            "reset",
            "--plugin",
            "lancamento-notas-fiscais",
            "--confirm-drop-schema",
        ],
    )
    with pytest.raises(SystemExit) as caught:
        module.main()
    assert caught.value.code == 1
    assert MESSAGE in capsys.readouterr().err


def test_reset_of_another_plugin_still_reaches_the_database(monkeypatch):
    module = _load_migrations_module()
    executed: list[str] = []

    class _Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, *_args):
            executed.append(str(sql))

    class _Connection:
        def cursor(self):
            return _Cursor()

        def commit(self):
            executed.append("commit")

        def rollback(self):
            executed.append("rollback")

    class _Context:
        def __enter__(self):
            return _Connection()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(module, "get_connection", lambda: _Context())
    module.reset_plugin_migrations("quality")
    assert any("DROP SCHEMA" in sql and "quality" in sql for sql in executed)
    assert "commit" in executed


def test_up_of_lnf_is_not_blocked(monkeypatch):
    module = _load_migrations_module()

    def _touched():
        raise RuntimeError("db-touched")

    monkeypatch.setattr(module, "get_connection", _touched)
    with pytest.raises(RuntimeError, match="db-touched"):
        module.run_plugin_migrations("lancamento-notas-fiscais")
