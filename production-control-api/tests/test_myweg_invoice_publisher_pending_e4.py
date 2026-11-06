"""Etapa 4 — automação --publish-pending fiscal MyWEG."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import httpx

from production_control_app.domain.myweg_invoice_observations_contract import (
    compute_payload_sha256,
    compute_semantic_sha256,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.cli import (
    main as publisher_main,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.collection_reader import (
    load_invoice_collection,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.config import (
    InvoicePublisherConfig,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.http_client import (
    MyWegInvoiceObservationsPublisherClient,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.payload_builder import (
    build_ingest_payload,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.pending import (
    run_invoice_pending_publish,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.state_store import (
    InvoicePublisherStateStore,
)
from tests.fixtures.myweg_invoices.sample_reference import (
    build_sample_2026_11_05_records,
)
from tests.fixtures.myweg_invoices.xlsx_factory import (
    materialize_empty_collection,
    materialize_sample_collection,
    write_invoice_xlsx,
)


def _config(tmp_path: Path, root: Path, *, activation: date | None) -> InvoicePublisherConfig:
    return InvoicePublisherConfig(
        invoice_root=root
        / "filial-02"
        / "empresa-1009"
        / "centro-1106"
        / "fornecedor-50471",
        state_dir=tmp_path / "invoice-state",
        api_base_url="http://pc-api",
        service_token="tok",
        caller_app="myweg-invoice-observations-publisher",
        timeout_seconds=5,
        max_attempts=1,
        stability_wait_seconds=0,
        max_batches_per_run=5,
        activation_document_date=activation,
    )


def _duplicate_collection(
    root: Path,
    *,
    source_collection_id: str,
    new_collection_id: str,
    document_date: str,
) -> Path:
    source = (
        root
        / "filial-02"
        / "empresa-1009"
        / "centro-1106"
        / "fornecedor-50471"
        / f"data-documento={document_date}"
        / source_collection_id
    )
    target = source.parent / new_collection_id
    shutil.copytree(source, target)
    manifesto = json.loads((target / "manifesto.json").read_text(encoding="utf-8"))
    manifesto["collection_id"] = new_collection_id
    old_xlsx = manifesto["arquivo_original"]
    new_xlsx = f"EXPORT_{new_collection_id}.xlsx"
    (target / old_xlsx).rename(target / new_xlsx)
    # Hash físico diferente, conteúdo fiscal igual.
    digest = write_invoice_xlsx(
        target / new_xlsx,
        build_sample_2026_11_05_records(),
    )
    manifesto["arquivo_original"] = new_xlsx
    manifesto["sha256"] = digest
    (target / "manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


def test_pending_requires_activation_watermark(tmp_path, monkeypatch, capsys):
    root = tmp_path / "nf"
    materialize_sample_collection(root)
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "tok")
    monkeypatch.setenv("MYWEG_INVOICE_PUBLISHER_STABILITY_WAIT_SECONDS", "0")
    code = publisher_main(
        [
            "--dry-run",
            "--publish-pending",
            "--invoice-root",
            str(
                root
                / "filial-02"
                / "empresa-1009"
                / "centro-1106"
                / "fornecedor-50471"
            ),
            "--state-dir",
            str(tmp_path / "state"),
            "--json",
        ]
    )
    assert code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "activation_watermark_required"


def test_ac01_eligible_collection_published(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(root, collection_id="col-a", document_date="2026-11-06")
    published: list[str] = []

    class Transport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            body = json.loads(request.content.decode("utf-8"))
            published.append(body["collection_id"])
            return httpx.Response(
                201,
                json={
                    "success": True,
                    "data": {"created": True, "id": "obs-1", "recordCount": 22},
                },
            )

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Transport(),
        max_attempts=1,
    )
    config = _config(tmp_path, root, activation=date(2026, 11, 6))
    result = run_invoice_pending_publish(
        config=config,
        dry_run=False,
        max_batches=5,
        include_historical=False,
        client=client,
    )
    assert result["published"] == 1
    assert published == ["col-a"]
    assert result["ok"] is True


def test_ac02_rerun_same_collection_no_new_business_observation(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(root, collection_id="col-a", document_date="2026-11-06")
    calls = {"n": 0}

    class Transport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            calls["n"] += 1
            return httpx.Response(
                201,
                json={"success": True, "data": {"created": True, "id": "obs-1"}},
            )

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Transport(),
        max_attempts=1,
    )
    config = _config(tmp_path, root, activation=date(2026, 11, 6))
    first = run_invoice_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    second = run_invoice_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert first["published"] == 1
    assert second["published"] == 0
    assert any(i["status"] == "already_published" for i in second["items"])
    assert calls["n"] == 1


def test_ac03_three_equivalent_exports_publish_once(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(root, collection_id="col-a", document_date="2026-11-06")
    _duplicate_collection(
        root, source_collection_id="col-a", new_collection_id="col-b", document_date="2026-11-06"
    )
    _duplicate_collection(
        root, source_collection_id="col-a", new_collection_id="col-c", document_date="2026-11-06"
    )
    published: list[str] = []

    class Transport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            body = json.loads(request.content.decode("utf-8"))
            published.append(body["collection_id"])
            return httpx.Response(
                201,
                json={"success": True, "data": {"created": True, "id": "obs-1"}},
            )

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Transport(),
        max_attempts=1,
    )
    config = _config(tmp_path, root, activation=date(2026, 11, 6))
    result = run_invoice_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 1
    assert len(published) == 1
    assert result["equivalent_skipped"] == 2
    # Não triplica quantidades — um único POST.
    assert sum(1 for i in result["items"] if i["status"] == "equivalent_skipped") == 2


def test_ac04_divergent_semantics_conflict_no_publish(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(root, collection_id="col-a", document_date="2026-11-06")
    # Segunda coleta: altera material → semantic diferente.
    alt = materialize_sample_collection(
        root, collection_id="col-divergent", document_date="2026-11-06"
    )
    records = build_sample_2026_11_05_records()
    records[0]["material_weg"] = "MAT-WEG-CHANGED"
    manifesto = json.loads((alt / "manifesto.json").read_text(encoding="utf-8"))
    xlsx_name = manifesto["arquivo_original"]
    digest = write_invoice_xlsx(alt / xlsx_name, records)
    manifesto["sha256"] = digest
    (alt / "manifesto.json").write_text(json.dumps(manifesto), encoding="utf-8")

    class Boom(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            raise AssertionError("conflito semântico não deve publicar")

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Boom(),
        max_attempts=1,
    )
    config = _config(tmp_path, root, activation=date(2026, 11, 6))
    result = run_invoice_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 0
    assert result["conflict"] >= 2
    assert all(i["status"] != "eligible" for i in result["items"] if i.get("document_date") == "2026-11-06")


def test_ac05_manual_day_not_republished_on_activation(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(
        root, collection_id="20261106T143350Z_2c04d5f7613d", document_date="2026-11-05"
    )
    directory = (
        root
        / "filial-02"
        / "empresa-1009"
        / "centro-1106"
        / "fornecedor-50471"
        / "data-documento=2026-11-05"
        / "20261106T143350Z_2c04d5f7613d"
    )
    artifacts = load_invoice_collection(directory, stability_wait_seconds=0)
    built = build_ingest_payload(artifacts)
    config = _config(tmp_path, root, activation=date(2026, 11, 5))
    state = InvoicePublisherStateStore(config.state_dir)
    state.record_attempt(
        collection_id="20261106T143350Z_2c04d5f7613d",
        payload_sha256=built["payload_sha256"],
        status="published",
        document_date="2026-11-05",
        semantic_sha256=built["semantic_sha256"],
        observation_id="f4145bb5-f124-4d6a-ab34-40415dd43c83",
        http_status=201,
        result="seeded",
    )

    class Boom(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            raise AssertionError("não republicar observação manual")

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Boom(),
        max_attempts=1,
    )
    result = run_invoice_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 0
    assert any(i["status"] == "already_published" for i in result["items"])


def test_ac06_incomplete_lock_blocked(tmp_path):
    root = tmp_path / "nf"
    directory = materialize_sample_collection(
        root, collection_id="col-lock", document_date="2026-11-07"
    )
    (directory / ".lock").write_text("busy", encoding="utf-8")
    config = _config(tmp_path, root, activation=date(2026, 11, 1))
    result = run_invoice_pending_publish(
        config=config, dry_run=True, max_batches=5, include_historical=False
    )
    assert result["published"] == 0
    assert any(i["status"] == "blocked" for i in result["items"])


def test_ac07_empty_signaled_published(tmp_path):
    root = tmp_path / "nf"
    materialize_empty_collection(root, collection_id="col-empty")
    published_status: list[str] = []

    class Transport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            body = json.loads(request.content.decode("utf-8"))
            published_status.append(body["observation_status"])
            return httpx.Response(
                201,
                json={"success": True, "data": {"created": True, "id": "obs-empty"}},
            )

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Transport(),
        max_attempts=1,
    )
    config = _config(tmp_path, root, activation=date(2026, 11, 1))
    result = run_invoice_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 1
    assert published_status == ["empty_signaled_by_sap"]


def test_ac08_transient_retry_then_success(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(root, collection_id="col-retry", document_date="2026-11-08")
    attempts = {"n": 0}

    class Transport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            attempts["n"] += 1
            if attempts["n"] == 1:
                return httpx.Response(503, json={"success": False, "message": "busy"})
            return httpx.Response(
                201,
                json={"success": True, "data": {"created": True, "id": "obs-r"}},
            )

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Transport(),
        max_attempts=3,
        sleep_fn=lambda _s: None,
    )
    config = _config(tmp_path, root, activation=date(2026, 11, 8))
    # config max_attempts is for publisher config; client carries retries
    result = run_invoice_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 1
    assert attempts["n"] == 2


def test_ac09_no_blind_retry_on_409(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(root, collection_id="col-409", document_date="2026-11-09")
    attempts = {"n": 0}

    class Transport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            attempts["n"] += 1
            return httpx.Response(409, json={"success": False, "message": "conflict"})

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Transport(),
        max_attempts=5,
        sleep_fn=lambda _s: None,
    )
    config = _config(tmp_path, root, activation=date(2026, 11, 9))
    result = run_invoice_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert attempts["n"] == 1
    assert result["failed"] == 1
    assert any(i["status"] == "conflict" for i in result["items"])


def test_ac10_run_lock_busy(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(root, collection_id="col-busy", document_date="2026-11-10")
    config = _config(tmp_path, root, activation=date(2026, 11, 10))
    state = InvoicePublisherStateStore(config.state_dir)
    with state.acquire_run_lock() as acquired:
        assert acquired is True
        result = run_invoice_pending_publish(
            config=config, dry_run=True, max_batches=5, include_historical=False
        )
        assert result["status"] == "busy"


def test_ac13_dry_run_does_not_post(tmp_path):
    root = tmp_path / "nf"
    materialize_sample_collection(root, collection_id="col-dry", document_date="2026-11-11")

    class Boom(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            raise AssertionError("dry-run não pode POST")

    client = MyWegInvoiceObservationsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=Boom(),
        max_attempts=1,
    )
    config = _config(tmp_path, root, activation=date(2026, 11, 11))
    result = run_invoice_pending_publish(
        config=config, dry_run=True, max_batches=5, include_historical=False, client=client
    )
    assert result["mode"] == "dry-run-pending"
    assert result["published"] == 1
    assert any(i["status"] == "dry_run_ok" for i in result["items"])
    state = InvoicePublisherStateStore(config.state_dir)
    assert state.get_success_for_collection("col-dry") is None


def test_empty_and_records_same_day_conflict(tmp_path):
    root = tmp_path / "nf"
    materialize_empty_collection(root, collection_id="col-empty-day")
    # Force empty day to 2026-11-06 and add with_records same day
    empty_dir = (
        root
        / "filial-02"
        / "empresa-1009"
        / "centro-1106"
        / "fornecedor-50471"
        / "data-documento=2026-11-01"
        / "col-empty-day"
    )
    day_dir = (
        root
        / "filial-02"
        / "empresa-1009"
        / "centro-1106"
        / "fornecedor-50471"
        / "data-documento=2026-11-06"
    )
    day_dir.mkdir(parents=True, exist_ok=True)
    target_empty = day_dir / "col-empty-day"
    shutil.move(str(empty_dir), str(target_empty))
    manifesto = json.loads((target_empty / "manifesto.json").read_text(encoding="utf-8"))
    manifesto["data_documento"] = "2026-11-06"
    (target_empty / "manifesto.json").write_text(json.dumps(manifesto), encoding="utf-8")
    materialize_sample_collection(root, collection_id="col-with", document_date="2026-11-06")

    config = _config(tmp_path, root, activation=date(2026, 11, 6))
    result = run_invoice_pending_publish(
        config=config, dry_run=True, max_batches=5, include_historical=False
    )
    assert result["conflict"] >= 2
    assert result["published"] == 0


def test_semantic_helpers_stable_for_equivalents():
    records = build_sample_2026_11_05_records()
    assert compute_semantic_sha256(records) == compute_semantic_sha256(list(reversed(records)))
    assert compute_payload_sha256(records) == compute_payload_sha256(records)
