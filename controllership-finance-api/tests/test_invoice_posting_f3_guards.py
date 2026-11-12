"""F3 guards — flag off, D8, handlers escopados, SQL parity, migrations verify."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from controllership_finance_app.infrastructure.invoice_posting.open_purchase_orders_sql import (
    open_purchase_orders_sql as bff_open_purchase_orders_sql,
)
from controllership_finance_app.interface.http.routes.invoice_posting.router import (
    _reject_non_user_principal,
)


PKG_ROOT = Path(__file__).resolve().parents[1]
BFF_MIGRATIONS = PKG_ROOT / "migrations" / "lancamento_notas_fiscais"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
MONOREPO = PKG_ROOT.parent if (PKG_ROOT.parent / "api-delpi").is_dir() else None


def test_migration_files_match_sha256sums() -> None:
    sums = {
        line.split()[0]: line.split()[1]
        for line in (BFF_MIGRATIONS / "SHA256SUMS.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    # SHA256SUMS format from port: "V00x...sql  src=.. dst=.. match=True"
    # Prefer canonical sha256sum lines; fall back to recomputing + origin when available.
    files = sorted(BFF_MIGRATIONS.glob("V*.sql"))
    assert len(files) == 14
    for f in files:
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        # SHA256SUMS.txt written as: name src=HEX dst=HEX match=True
        line = next(
            ln
            for ln in (BFF_MIGRATIONS / "SHA256SUMS.txt").read_text().splitlines()
            if ln.startswith(f.name)
        )
        assert f"dst={digest}" in line
        assert "match=True" in line
        if MONOREPO is not None:
            origin = (
                MONOREPO
                / "api-delpi/migrations/plugins/lancamento-notas-fiscais"
                / f.name
            )
            assert origin.is_file()
            assert hashlib.sha256(origin.read_bytes()).hexdigest() == digest


def test_open_purchase_orders_sql_text_parity() -> None:
    origin_fn = (FIXTURES / "open_purchase_orders_sql_origin.py.txt").read_text()
    bff_src = inspect.getsource(bff_open_purchase_orders_sql)
    assert "".join(origin_fn.split()) == "".join(bff_src.split())


def test_d8_rejects_service_principal() -> None:
    user = SimpleNamespace(principal_type="service")
    with patch(
        "controllership_finance_app.interface.http.routes.invoice_posting.router.get_current_user",
        return_value=user,
    ):
        with pytest.raises(HTTPException) as exc:
            _reject_non_user_principal()
    assert exc.value.status_code == 403
    assert exc.value.detail == "Forbidden"


def test_d8_allows_human_user() -> None:
    user = SimpleNamespace(principal_type="user")
    with patch(
        "controllership_finance_app.interface.http.routes.invoice_posting.router.get_current_user",
        return_value=user,
    ):
        _reject_non_user_principal()


def test_flag_off_does_not_mount_lnf_routes() -> None:
    main_src = (PKG_ROOT / "controllership_finance_app" / "main.py").read_text()
    assert "if settings.LNF_HOSTED_ENABLED:" in main_src
    assert "invoice_posting_router" in main_src
    from controllership_finance_app.config import settings

    assert settings.LNF_HOSTED_ENABLED is False


def test_scoped_validation_handler_does_not_change_closing_shape() -> None:
    from controllership_finance_app.core.responses import fail
    from controllership_finance_app.interface.http.routes.invoice_posting.responses import (
        error_response,
    )

    closing = fail("campo: inválido", 422)
    lnf = error_response(
        "Parâmetros inválidos",
        status_code=422,
        code="VALIDATION_ERROR",
        recoverable=True,
    )
    assert closing.status_code == 422
    assert lnf.status_code == 422
    lnf_payload = json.loads(lnf.body.decode())
    assert lnf_payload["error"]["code"] == "VALIDATION_ERROR"
    assert lnf_payload["message"] == "Parâmetros inválidos"


def test_migrations_verify_fails_on_checksum_mismatch(tmp_path: Path, monkeypatch):
    from controllership_finance_app.infrastructure.invoice_posting import (
        migrations_verify as mv,
    )

    fake_dir = tmp_path / "mig"
    fake_dir.mkdir()
    for src in sorted(BFF_MIGRATIONS.glob("V*.sql")):
        (fake_dir / src.name).write_bytes(src.read_bytes())
    p = fake_dir / "V001__create_invoice_posting_core.sql"
    p.write_bytes(p.read_bytes() + b"\n-- tamper\n")

    monkeypatch.setattr(mv, "MIGRATIONS_DIR", fake_dir)

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, *a, **k):
            return None

        def fetchall(self):
            rows = []
            for f in sorted(BFF_MIGRATIONS.glob("V*.sql")):
                rows.append(
                    {
                        "version": f.stem.split("__", 1)[0],
                        "checksum": hashlib.sha256(f.read_bytes()).hexdigest(),
                    }
                )
            return rows

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr(
        mv,
        "settings",
        SimpleNamespace(
            PLUGINS_DB_HOST="localhost",
            PLUGINS_DB_PORT="5432",
            PLUGINS_DB_NAME="plugins_hub",
            PLUGINS_DB_USER="u",
            PLUGINS_DB_PASSWORD="p",
            PLUGINS_DB_CONNECT_TIMEOUT=5,
            PLUGINS_DB_SSLMODE="prefer",
        ),
    )
    with patch.object(mv.psycopg, "connect", return_value=FakeConn()):
        with pytest.raises(mv.LnfMigrationsVerifyError) as exc:
            mv.verify_lnf_migrations()
    assert "mismatched" in str(exc.value)


def test_notification_payload_captured_with_fake_core(monkeypatch):
    captured: list[dict] = []

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"ok": True}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, headers=None):
            captured.append({"url": url, "json": json, "headers": headers})
            return FakeResponse()

    from controllership_finance_app.application.invoice_posting import (
        lnf_portal_notification_service as svc,
    )

    monkeypatch.setattr(
        svc,
        "settings",
        SimpleNamespace(
            LNF_NOTIFICATIONS_ENABLED=True,
            CORE_API_BASE_URL="http://core-api:8000",
            CORE_API_INTEGRATIONS_SERVICE_TOKEN="tok",
        ),
    )
    with patch.object(svc.httpx, "Client", FakeClient):
        ok = svc.send_lnf_portal_notification(
            recipient_user_id="u1",
            title="t",
            message="m",
            event_type="lnf_request_blocked_assigned",
            dedupe_key="k1",
            action_target="/apps/lancamento-notas-fiscais/filial-01?requestId=r1",
        )
    assert ok is True
    assert len(captured) == 1
    payload = captured[0]["json"]
    assert payload["sourceApp"] == "lancamento-notas-fiscais"
    assert payload["userIds"] == ["u1"]
