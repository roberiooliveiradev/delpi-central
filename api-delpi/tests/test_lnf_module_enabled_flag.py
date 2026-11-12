"""LNF_MODULE_ENABLED — default true preserva comportamento; false omite schema no runner."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_migrations_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_plugins_migrations.py"
    )
    name = "run_plugins_migrations_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_list_plugin_slugs_includes_lnf_by_default(monkeypatch):
    monkeypatch.delenv("LNF_MODULE_ENABLED", raising=False)
    module = _load_migrations_module()
    slugs = module.list_plugin_slugs()
    assert "lancamento-notas-fiscais" in slugs


def test_list_plugin_slugs_skips_lnf_when_disabled(monkeypatch):
    monkeypatch.setenv("LNF_MODULE_ENABLED", "false")
    module = _load_migrations_module()
    slugs = module.list_plugin_slugs()
    assert "lancamento-notas-fiscais" not in slugs
