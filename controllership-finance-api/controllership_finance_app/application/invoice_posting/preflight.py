"""Preflight DARK do módulo LNF — sem montar rotas e sem exigir LNF_HOSTED_ENABLED.

Verifica ledger V001–V014, SELECT 1 no Protheus, health da financial-api e do Core,
e gravabilidade de LNF_DANFE_UPLOAD_DIR. Nunca imprime segredos.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from controllership_finance_app.config import settings
from controllership_finance_app.infrastructure.invoice_posting.migrations_verify import (
    LnfMigrationsVerifyError,
    verify_lnf_migrations,
)


@dataclass(frozen=True)
class PreflightItem:
    name: str
    ok: bool
    detail: str


def _check_ledger() -> PreflightItem:
    try:
        verify_lnf_migrations()
        return PreflightItem("ledger_v001_v014", True, "presença + sha256 OK")
    except LnfMigrationsVerifyError as exc:
        return PreflightItem("ledger_v001_v014", False, str(exc))
    except Exception as exc:  # noqa: BLE001 — relatório operacional
        return PreflightItem("ledger_v001_v014", False, f"{type(exc).__name__}")


def _check_totvs_select1(
    *,
    connect: Callable[[], object] | None = None,
) -> PreflightItem:
    try:
        if connect is None:
            from controllership_finance_app.infrastructure.invoice_posting.totvs_connection_pool import (
                create_totvs_connection,
            )

            connect = create_totvs_connection
        conn = connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            ok = row is not None and int(row[0]) == 1
            return PreflightItem(
                "totvs_select_1",
                ok,
                "SELECT 1 OK" if ok else "resultado inesperado",
            )
        finally:
            close = getattr(conn, "close", None)
            if callable(close):
                close()
    except Exception as exc:  # noqa: BLE001
        return PreflightItem("totvs_select_1", False, f"{type(exc).__name__}")


def _http_get_status(url: str, *, timeout: float = 5.0) -> int:
    req = Request(url, method="GET")
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — URL de env interno
        return int(getattr(resp, "status", 200) or 200)


def _check_health(name: str, base_url: str) -> PreflightItem:
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return PreflightItem(name, False, "URL ausente")
    url = f"{base}/health"
    try:
        status = _http_get_status(url)
        ok = status == 200
        return PreflightItem(name, ok, f"GET {url} → {status}")
    except HTTPError as exc:
        return PreflightItem(name, False, f"GET {url} → HTTP {exc.code}")
    except URLError as exc:
        return PreflightItem(name, False, f"{type(exc.reason).__name__ if exc.reason else 'URLError'}")
    except Exception as exc:  # noqa: BLE001
        return PreflightItem(name, False, f"{type(exc).__name__}")


def _check_danfe_dir(base_dir: str | None = None) -> PreflightItem:
    root = Path(base_dir or settings.LNF_DANFE_UPLOAD_DIR)
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / f".preflight-{uuid.uuid4().hex}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return PreflightItem("danfe_upload_dir", True, f"gravável: {root.as_posix()}")
    except Exception as exc:  # noqa: BLE001
        return PreflightItem("danfe_upload_dir", False, f"{type(exc).__name__}")


def run_lnf_preflight(
    *,
    totvs_connect: Callable[[], object] | None = None,
    financial_base_url: str | None = None,
    core_base_url: str | None = None,
    danfe_dir: str | None = None,
) -> list[PreflightItem]:
    """Executa checks; independente de LNF_HOSTED_ENABLED."""
    return [
        _check_ledger(),
        _check_totvs_select1(connect=totvs_connect),
        _check_health(
            "financial_api_health",
            financial_base_url
            if financial_base_url is not None
            else settings.FINANCIAL_API_BASE_URL,
        ),
        _check_health(
            "core_api_health",
            core_base_url if core_base_url is not None else settings.CORE_API_BASE_URL,
        ),
        _check_danfe_dir(danfe_dir),
    ]


def format_report(items: list[PreflightItem]) -> str:
    lines = ["LNF preflight"]
    for item in items:
        mark = "PASS" if item.ok else "FAIL"
        lines.append(f"  [{mark}] {item.name}: {item.detail}")
    failed = sum(1 for i in items if not i.ok)
    lines.append(f"summary: {len(items) - failed}/{len(items)} PASS")
    return "\n".join(lines)


def exit_code(items: list[PreflightItem]) -> int:
    return 0 if all(i.ok for i in items) else 1
