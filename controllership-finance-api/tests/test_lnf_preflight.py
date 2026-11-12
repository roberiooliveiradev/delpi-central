"""Preflight LNF — unitário, sem rede real / sem secrets."""

from __future__ import annotations

from pathlib import Path

from controllership_finance_app.application.invoice_posting import preflight as pf


class _FakeCursor:
    def execute(self, _sql: str) -> None:
        return None

    def fetchone(self):
        return (1,)


class _FakeConn:
    def cursor(self) -> _FakeCursor:
        return _FakeCursor()

    def close(self) -> None:
        return None


def test_preflight_all_pass(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pf, "verify_lnf_migrations", lambda: None)

    def fake_health(url: str, *, timeout: float = 5.0) -> int:
        assert url.endswith("/health")
        return 200

    monkeypatch.setattr(pf, "_http_get_status", fake_health)
    items = pf.run_lnf_preflight(
        totvs_connect=_FakeConn,
        financial_base_url="http://financial-api:8000",
        core_base_url="http://core-api:8000",
        danfe_dir=str(tmp_path / "danfe"),
    )
    assert all(i.ok for i in items)
    assert pf.exit_code(items) == 0
    report = pf.format_report(items)
    assert "[PASS] ledger_v001_v014" in report
    assert "password" not in report.lower()
    assert "secret" not in report.lower()


def test_preflight_ledger_fail(monkeypatch, tmp_path: Path) -> None:
    from controllership_finance_app.infrastructure.invoice_posting.migrations_verify import (
        LnfMigrationsVerifyError,
    )

    def boom() -> None:
        raise LnfMigrationsVerifyError("missing=['V014']")

    monkeypatch.setattr(pf, "verify_lnf_migrations", boom)
    monkeypatch.setattr(pf, "_http_get_status", lambda *a, **k: 200)
    items = pf.run_lnf_preflight(
        totvs_connect=_FakeConn,
        financial_base_url="http://financial-api:8000",
        core_base_url="http://core-api:8000",
        danfe_dir=str(tmp_path),
    )
    ledger = next(i for i in items if i.name == "ledger_v001_v014")
    assert ledger.ok is False
    assert pf.exit_code(items) == 1


def test_preflight_danfe_not_writable(tmp_path: Path) -> None:
    # path aponta para arquivo regular → mkdir/write falha
    blocked = tmp_path / "not-a-dir"
    blocked.write_text("x", encoding="utf-8")
    item = pf._check_danfe_dir(str(blocked))
    assert item.ok is False
    assert item.name == "danfe_upload_dir"


def test_cli_main_returns_nonzero_on_fail(monkeypatch, tmp_path: Path) -> None:
    from controllership_finance_app.interface.cli import lnf_preflight as cli

    monkeypatch.setattr(
        cli,
        "run_lnf_preflight",
        lambda: [pf.PreflightItem("x", False, "no")],
    )
    assert cli.main([]) == 1
