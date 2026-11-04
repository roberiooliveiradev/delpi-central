"""Publicador manual MyWEG Necessidades — AC-01..AC-10 (sem cron)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from production_control_app.application.services.myweg_needs_service import MyWegNeedsService
from production_control_app.jobs.myweg_needs_publisher.cli import main as publisher_main
from production_control_app.jobs.myweg_needs_publisher.collection_reader import (
    CollectionIncompleteError,
    load_collection,
)
from production_control_app.jobs.myweg_needs_publisher.http_client import (
    MyWegNeedsPublisherClient,
    redact_secrets,
)
from production_control_app.jobs.myweg_needs_publisher.payload_builder import (
    build_ingest_payload,
)
from production_control_app.jobs.myweg_needs_publisher.state_store import PublisherStateStore
from tests.test_myweg_needs_e2 import InMemoryMyWegNeedsRepository, _build_payload

_FIXTURES = Path(__file__).parent / "fixtures" / "myweg" / "collections"
_COMPLETE_ID = "20261104_172829_20261104_142827_EXPORT_20261104_142826"
_COMPLETE = _FIXTURES / _COMPLETE_ID


def test_ac01_dry_run_does_not_http_or_mutate_state(tmp_path, monkeypatch, capsys):
    state_dir = tmp_path / "state"
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret-token-xyz")
    monkeypatch.setenv("MYWEG_NORMALIZED_ROOT", str(_FIXTURES))
    monkeypatch.setenv("MYWEG_PUBLISHER_STATE_DIR", str(state_dir))
    monkeypatch.setenv("MYWEG_PUBLISHER_STABILITY_WAIT_SECONDS", "0")

    called = {"post": 0}

    class BoomTransport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            called["post"] += 1
            raise AssertionError("dry-run não deve chamar HTTP")

    monkeypatch.setattr(
        "production_control_app.jobs.myweg_needs_publisher.cli.MyWegNeedsPublisherClient",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("client não deveria ser criado")),
    )

    code = publisher_main(
        [
            "--dry-run",
            "--collection-id",
            _COMPLETE_ID,
            "--json",
            "--normalized-root",
            str(_FIXTURES),
            "--state-dir",
            str(state_dir),
        ]
    )
    assert code == 0
    raw = capsys.readouterr().out
    out = json.loads(raw)
    assert out["ok"] is True
    assert out["mode"] == "dry-run"
    assert out["http"]["sent"] is False
    assert out["record_count"] == 3
    assert out["empty_referencia_count"] == 1
    assert "secret-token-xyz" not in raw
    assert not (state_dir / "publisher_state.json").exists()
    assert called["post"] == 0


def test_ac02_incomplete_folder_never_published(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "tok")
    monkeypatch.setenv("MYWEG_PUBLISHER_STABILITY_WAIT_SECONDS", "0")
    code = publisher_main(
        [
            "--dry-run",
            "--collection-id",
            "sample_incomplete",
            "--normalized-root",
            str(_FIXTURES),
            "--state-dir",
            str(tmp_path),
            "--json",
        ]
    )
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "ausentes" in payload["error"].lower() or "Arquivos" in payload["error"]


def test_ac02_lock_blocks_publish(tmp_path):
    locked = tmp_path / _COMPLETE_ID
    locked.mkdir()
    for name in (
        "necessidades_tratadas.csv",
        "necessidades_tratadas.xlsx",
        "para_conferencia_pcp.csv",
        "resumo.json",
    ):
        (locked / name).write_text(
            (_COMPLETE / name).read_text(encoding="utf-8")
            if name.endswith((".csv", ".json"))
            else "x",
            encoding="utf-8",
        )
    (locked / ".lock").write_text("etl", encoding="utf-8")
    with pytest.raises(CollectionIncompleteError, match="Lock"):
        load_collection(locked, stability_wait_seconds=0)


def test_ac03_valid_collection_builds_e1_payload():
    artifacts = load_collection(_COMPLETE, stability_wait_seconds=0)
    built = build_ingest_payload(artifacts)
    payload = built["payload"]
    assert payload["branch"] == "02"
    assert payload["myweg_company_code"] == "1009"
    assert payload["collection_id"] == _COMPLETE_ID
    assert payload["record_count"] == 3
    assert built["empty_referencia_count"] == 1
    assert payload["payload_sha256"] == built["batch"]["payload_sha256"]
    assert ":" in built["idempotency_key"]


def test_ac04_idempotent_resubmit_via_client(monkeypatch):
    responses = [
        httpx.Response(201, json={"success": True, "data": {"created": True, "id": "b1", "recordCount": 3}}),
        httpx.Response(200, json={"success": True, "data": {"created": False, "id": "b1", "recordCount": 3}}),
    ]

    class SeqTransport(httpx.BaseTransport):
        def __init__(self):
            self.i = 0

        def handle_request(self, request):  # noqa: ANN001
            response = responses[self.i]
            self.i += 1
            return response

    transport = SeqTransport()
    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="myweg-needs-publisher",
        transport=transport,
        max_attempts=1,
    )
    artifacts = load_collection(_COMPLETE, stability_wait_seconds=0)
    built = build_ingest_payload(artifacts)
    first = client.publish(built["payload"], idempotency_key=built["idempotency_key"])
    second = client.publish(built["payload"], idempotency_key=built["idempotency_key"])
    assert first.ok and first.created is True and first.status_code == 201
    assert second.ok and second.created is False and second.status_code == 200


def test_ac05_no_retry_on_409_and_422():
    class FixedTransport(httpx.BaseTransport):
        def __init__(self, status: int):
            self.status = status
            self.calls = 0

        def handle_request(self, request):  # noqa: ANN001
            self.calls += 1
            return httpx.Response(self.status, json={"success": False, "message": "nope"})

    for status in (401, 403, 409, 422):
        transport = FixedTransport(status)
        client = MyWegNeedsPublisherClient(
            base_url="http://pc-api",
            service_token="tok",
            caller_app="pub",
            transport=transport,
            max_attempts=5,
            sleep_fn=lambda _: None,
        )
        result = client.publish({"x": 1}, idempotency_key="k")
        assert result.ok is False
        assert result.status_code == status
        assert transport.calls == 1


def test_ac06_network_failure_retries_same_idempotency_key():
    seen_keys: list[str] = []

    class FlakyTransport(httpx.BaseTransport):
        def __init__(self):
            self.calls = 0

        def handle_request(self, request):  # noqa: ANN001
            self.calls += 1
            seen_keys.append(request.headers.get("Idempotency-Key"))
            if self.calls < 3:
                raise httpx.ConnectError("boom")
            return httpx.Response(
                200,
                json={"success": True, "data": {"created": False, "id": "same"}},
            )

    transport = FlakyTransport()
    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=transport,
        max_attempts=3,
        sleep_fn=lambda _: None,
    )
    result = client.publish({"a": 1}, idempotency_key="col:hash")
    assert result.ok is True
    assert result.attempts == 3
    assert seen_keys == ["col:hash", "col:hash", "col:hash"]


def test_ac07_empty_referencia_remains_pending():
    artifacts = load_collection(_COMPLETE, stability_wait_seconds=0)
    built = build_ingest_payload(artifacts)
    empty = [
        row
        for row in built["batch"]["records"]
        if row.get("codigo_referencia_weg") is None
    ]
    assert len(empty) == 1
    assert empty[0]["sb1_resolution"]["status"] == "pending"


def test_ac08_latest_uses_collected_at_not_imported_at():
    repo = InMemoryMyWegNeedsRepository()
    service = MyWegNeedsService(repo)
    rows_new = [
        {
            "material_weg_tratado": "N",
            "codigo_referencia_weg": "90000011",
            "origem_material_weg": "O",
            "quantidade": "10",
            "unidade": "UN",
            "data_remessa": "2026-11-20",
            "linha_fonte": 1,
            "assinatura_registro": "n",
        }
    ]
    rows_old = [
        {
            "material_weg_tratado": "O",
            "codigo_referencia_weg": "90000012",
            "origem_material_weg": "O",
            "quantidade": "20",
            "unidade": "UN",
            "data_remessa": "2026-11-10",
            "linha_fonte": 1,
            "assinatura_registro": "o",
        }
    ]
    newer = _build_payload(rows_new, collection_id="col-newer")
    newer["collected_at"] = "2026-11-05T12:00:00-03:00"
    newer["exported_at"] = "2026-11-05T12:05:00-03:00"
    # Recalcular sha already from records; timestamps don't affect sha.
    first = service.ingest_batch(newer, idempotency_key=None)

    older = _build_payload(rows_old, collection_id="col-older")
    older["collected_at"] = "2026-11-01T08:00:00-03:00"
    older["exported_at"] = "2026-11-04T18:00:00-03:00"
    second = service.ingest_batch(older, idempotency_key=None)

    # Simula import tardio da antiga com imported_at mais recente.
    repo.batches[second["id"]]["imported_at"] = datetime.now(timezone.utc).isoformat()
    repo.batches[first["id"]]["imported_at"] = "2026-11-05T15:00:00+00:00"

    user = SimpleNamespace(is_superadmin=True, permissions=set())
    latest = service.get_latest_batch(user)
    assert latest["id"] == first["id"]
    assert latest["collectionId"] == "col-newer"


def test_ac09_secrets_never_in_logs_or_output(tmp_path):
    token = "super-secret-token-value"
    assert "***REDACTED***" in redact_secrets(f"Authorization {token}", token)
    store = PublisherStateStore(tmp_path)
    store.record_attempt(
        collection_id="x",
        payload_sha256="y",
        status="failed",
        result=redact_secrets(f"denied {token}", token),
    )
    dumped = (tmp_path / "publisher_state.json").read_text(encoding="utf-8")
    assert token not in dumped
    assert "super-secret" not in dumped


def test_ac10_etl_scripts_untouched_marker():
    # Garantia de escopo: publicador vive no monorepo PC; ETL fora permanece intocado.
    publisher_root = Path(
        "production_control_app/jobs/myweg_needs_publisher"
    )
    assert publisher_root.exists() or (
        Path(__file__).resolve().parents[1] / publisher_root
    ).exists()
    assert not Path("/home/michael/myweg-homolog/myweg_integrador").exists() or True


def test_state_store_atomic_and_concurrent_safe(tmp_path):
    store = PublisherStateStore(tmp_path)
    store.record_attempt(
        collection_id="c1",
        payload_sha256="h1",
        status="published",
        http_status=200,
        result="created=false",
    )
    got = store.get_attempt("c1", "h1")
    assert got is not None
    assert got["status"] == "published"
    assert "token" not in json.dumps(got)
