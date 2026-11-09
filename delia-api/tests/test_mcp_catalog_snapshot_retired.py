"""T2.1 — MCP catalog snapshot experiment retired (doc 293 §2A).

Discovery is live-only via SpecialistInterop / native MCPToolset.
Retired env vars and modules must fail closed — never silent fallback.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from app.infrastructure.config.settings import Settings


_REPO_APP = Path(__file__).resolve().parents[1] / "app"


def test_snapshot_modules_physically_absent() -> None:
    assert not (
        _REPO_APP
        / "application/specialist_interop/snapshot_interop.py"
    ).exists()
    assert not (
        _REPO_APP
        / "infrastructure/interoperability/mcp/catalog_store.py"
    ).exists()
    assert not (
        Path(__file__).resolve().parents[1]
        / "scripts/mcp_catalog_sync.py"
    ).exists()


@pytest.mark.parametrize(
    "module",
    (
        "app.application.specialist_interop.snapshot_interop",
        "app.infrastructure.interoperability.mcp.catalog_store",
    ),
)
def test_snapshot_modules_not_importable(module: str) -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module)


def test_retired_catalog_mode_snapshot_experiment_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DELIA_MCP_CATALOG_MODE", "snapshot_experiment")
    monkeypatch.delenv("DELIA_MCP_CATALOG_DB", raising=False)
    with pytest.raises(ValueError, match="retired"):
        Settings()


def test_retired_catalog_db_env_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DELIA_MCP_CATALOG_MODE", raising=False)
    monkeypatch.setenv("DELIA_MCP_CATALOG_DB", "/tmp/mcp_catalog.db")
    with pytest.raises(ValueError, match="retired"):
        Settings()


def test_live_or_unset_catalog_mode_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DELIA_MCP_CATALOG_MODE", raising=False)
    monkeypatch.delenv("DELIA_MCP_CATALOG_DB", raising=False)
    settings = Settings()
    assert not hasattr(settings, "mcp_catalog_mode")
    assert not hasattr(settings, "mcp_catalog_db")


def test_explicit_live_mode_is_harmless_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset-equivalent: live may remain in transitional env as no-op."""
    monkeypatch.setenv("DELIA_MCP_CATALOG_MODE", "live")
    monkeypatch.delenv("DELIA_MCP_CATALOG_DB", raising=False)
    Settings()  # must not raise
