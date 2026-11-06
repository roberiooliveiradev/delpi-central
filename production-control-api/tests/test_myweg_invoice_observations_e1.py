"""Etapa 1 — MyWEG NF Emitidas: contrato, reader, ingestão, consulta e publicador."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook

from production_control_app.application.services.myweg_invoice_observations_service import (
    MyWegInvoiceObservationsService,
)
from production_control_app.core.security import (
    PC_ACCESS,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_01,
    PC_VIEW_FILIAL_02,
)
from production_control_app.domain.errors import MyWegInvoiceObservationConflict
from production_control_app.domain.myweg_invoice_observations_contract import (
    CONTRACT_VERSION,
    build_idempotency_key,
    compute_payload_sha256,
    compute_semantic_sha256,
    decimal_to_canonical_str,
    quantity_to_un,
)
from production_control_app.domain.services.myweg_invoice_observations_normalization import (
    validate_ingest_observation,
)
from production_control_app.infrastructure.persistence.postgres_myweg_invoice_observations_repository import (
    MyWegInvoiceObservationCollectionConflict,
)
from production_control_app.interface.http.routes import (
    integration_myweg_routes,
    myweg_invoice_observations_routes,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.cli import main as cli_main
from production_control_app.jobs.myweg_invoice_observations_publisher.collection_reader import (
    InvoiceCollectionIncompleteError,
    InvoiceCollectionReadError,
    load_invoice_collection,
)
from production_control_app.jobs.myweg_invoice_observations_publisher import EXPECTED_HEADERS
from production_control_app.middleware.auth_middleware import _is_internal_integration
from tests.fixtures.myweg_invoices.sample_reference import (
    REAL_XLSX_SHA256,
    SAMPLE_DISTINCT_INVOICES,
    SAMPLE_DISTINCT_MATERIALS,
    SAMPLE_RECORD_COUNT,
    SAMPLE_TOTAL_UN,
    build_sample_2026_11_05_records,
)
from tests.fixtures.myweg_invoices.xlsx_factory import (
    materialize_empty_collection,
    materialize_sample_collection,
    write_invoice_xlsx,
)


class InMemoryInvoiceRepo:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.observations: dict[str, dict] = {}
        self.items: dict[str, list[dict]] = {}
        self.fail_after_header = False

    def find_by_collection_id(self, collection_id: str) -> dict | None:
        with self._lock:
            for row in self.observations.values():
                if row["collection_id"] == collection_id:
                    return dict(row)
        return None

    def find_by_id(self, observation_id: str) -> dict | None:
        with self._lock:
            row = self.observations.get(observation_id)
            return dict(row) if row else None

    def insert_accepted_observation(self, **kwargs):
        with self._lock:
            for row in self.observations.values():
                if row["collection_id"] == kwargs["collection_id"]:
                    raise MyWegInvoiceObservationCollectionConflict("dup")
            obs_id = str(uuid.uuid4())
            observation = {
                "id": obs_id,
                "collection_id": kwargs["collection_id"],
                "branch": kwargs["branch"],
                "myweg_company_code": kwargs["myweg_company_code"],
                "myweg_work_center": kwargs["myweg_work_center"],
                "myweg_supplier_code": kwargs["myweg_supplier_code"],
                "contract_version": kwargs["contract_version"],
                "document_date": kwargs["document_date"].isoformat(),
                "observation_status": kwargs["observation_status"],
                "observed_at": (
                    kwargs["observed_at"].isoformat() if kwargs["observed_at"] else None
                ),
                "source_prepared_at": kwargs["source_prepared_at"].isoformat(),
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "source_sha256": kwargs["source_sha256"],
                "payload_sha256": kwargs["payload_sha256"],
                "semantic_sha256": kwargs["semantic_sha256"],
                "record_count": kwargs["record_count"],
                "total_quantity_un": decimal_to_canonical_str(
                    kwargs["total_quantity_un"]
                ),
                "manifesto": dict(kwargs["manifesto"]),
                "status": "accepted",
                "idempotency_key": kwargs["idempotency_key"],
                "caller_app": kwargs["caller_app"],
            }
            if self.fail_after_header:
                raise RuntimeError("forced partial failure")
            self.observations[obs_id] = observation
            self.items[obs_id] = [
                {
                    "id": str(uuid.uuid4()),
                    "sourceLineNo": int(record["source_line_no"]),
                    "invoiceNumber": record["invoice_number"],
                    "invoiceSeries": record["invoice_series"],
                    "materialWeg": record["material_weg"],
                    "materialDescription": record.get("material_description") or "",
                    "quantityOriginal": record["quantity_original"],
                    "sourceUnit": record["source_unit"],
                    "quantityUn": record.get("quantity_un"),
                    "unitComparability": record["unit_comparability"],
                    "departureDate": record["departure_date"],
                }
                for record in kwargs["records"]
            ]
            return dict(observation)

    def list_observations(
        self, *, document_date, observation_status, page, page_size
    ) -> dict:
        items = list(self.observations.values())
        if document_date is not None:
            items = [
                row
                for row in items
                if row["document_date"] == document_date.isoformat()
            ]
        if observation_status:
            items = [
                row
                for row in items
                if row["observation_status"] == observation_status
            ]
        items = sorted(
            items,
            key=lambda row: (row["document_date"], row["imported_at"]),
            reverse=True,
        )
        offset = (page - 1) * page_size
        return {
            "page": page,
            "pageSize": page_size,
            "total": len(items),
            "items": [dict(item) for item in items[offset : offset + page_size]],
        }

    def list_observation_items(self, *, observation_id, search, page, page_size) -> dict:
        rows = list(self.items.get(observation_id, []))
        needle = (search or "").strip().lower()
        if needle:
            rows = [
                row
                for row in rows
                if needle in str(row.get("invoiceNumber") or "").lower()
                or needle in str(row.get("materialWeg") or "").lower()
            ]
        offset = (page - 1) * page_size
        return {
            "page": page,
            "pageSize": page_size,
            "total": len(rows),
            "items": rows[offset : offset + page_size],
        }

    def count_by_semantic_sha256(
        self, *, semantic_sha256: str, exclude_collection_id: str | None = None
    ) -> int:
        count = 0
        for row in self.observations.values():
            if row["semantic_sha256"].lower() != semantic_sha256.lower():
                continue
            if exclude_collection_id and row["collection_id"] == exclude_collection_id:
                continue
            count += 1
        return count


def _payload_from_records(
    records: list[dict],
    *,
    collection_id: str,
    observation_status: str = "with_records",
    source_sha256: str | None = "a" * 64,
    document_date: str = "2026-11-05",
    observed_at: str | None = "2026-11-06T06:15:00-03:00",
) -> dict:
    payload_sha = compute_payload_sha256(records)
    semantic_sha = compute_semantic_sha256(records)
    return {
        "contract_version": CONTRACT_VERSION,
        "collection_id": collection_id,
        "branch": "02",
        "myweg_company_code": "1009",
        "myweg_work_center": "1106",
        "myweg_supplier_code": "50471",
        "document_date": document_date,
        "observation_status": observation_status,
        "observed_at": observed_at,
        "source_prepared_at": "2026-11-06T09:16:00+00:00",
        "source_sha256": source_sha256,
        "payload_sha256": payload_sha,
        "semantic_sha256": semantic_sha,
        "record_count": len(records),
        "manifesto": {"schema_version": 1},
        "records": records,
    }


def test_sample_reference_totals():
    records = build_sample_2026_11_05_records()
    assert len(records) == SAMPLE_RECORD_COUNT
    assert len({r["invoice_number"] for r in records}) == SAMPLE_DISTINCT_INVOICES
    assert len({r["material_weg"] for r in records}) == SAMPLE_DISTINCT_MATERIALS
    total = sum(Decimal(str(r["quantity_un"])) for r in records)
    assert total == SAMPLE_TOTAL_UN
    assert len(REAL_XLSX_SHA256) == 64


def test_unit_conversion_un_mi_and_unknown():
    qty, status = quantity_to_un(quantity_original=Decimal("2"), source_unit="MI")
    assert qty == Decimal("2000")
    assert status == "comparable"
    qty_un, status_un = quantity_to_un(quantity_original=Decimal("10"), source_unit="UN")
    assert qty_un == Decimal("10")
    assert status_un == "comparable"
    qty_x, status_x = quantity_to_un(quantity_original=Decimal("1"), source_unit="KG")
    assert qty_x is None
    assert status_x == "non_comparable"


def test_semantic_hash_order_independent_preserves_multiplicity():
    records = build_sample_2026_11_05_records()
    reversed_records = list(reversed(records))
    assert compute_semantic_sha256(records) == compute_semantic_sha256(reversed_records)
    # Multiplicidade: duplicar uma linha muda o hash
    dup = records + [dict(records[0])]
    assert compute_semantic_sha256(dup) != compute_semantic_sha256(records)


def test_preserve_leading_zeros_and_same_invoice_multiple_lines(tmp_path: Path):
    records = [
        {
            "source_line_no": 2,
            "invoice_number": "0001234",
            "invoice_series": "001",
            "material_weg": "000987",
            "material_description": "A",
            "quantity_original": "1",
            "source_unit": "UN",
            "quantity_un": "1",
            "unit_comparability": "comparable",
            "departure_date": "2026-11-05",
        },
        {
            "source_line_no": 3,
            "invoice_number": "0001234",
            "invoice_series": "001",
            "material_weg": "000988",
            "material_description": "B",
            "quantity_original": "2",
            "source_unit": "UN",
            "quantity_un": "2",
            "unit_comparability": "comparable",
            "departure_date": "2026-11-05",
        },
    ]
    directory = tmp_path / "filial-02" / "empresa-1009" / "centro-1106" / "fornecedor-50471"
    directory = directory / "data-documento=2026-11-05" / "col-zeros"
    directory.mkdir(parents=True)
    xlsx_name = "EXPORT_zeros.xlsx"
    sha = write_invoice_xlsx(directory / xlsx_name, records)
    manifesto = {
        "schema_version": 1,
        "collection_id": "col-zeros",
        "origem": "MyWEG",
        "tipo_relatorio": "notas_fiscais_emitidas",
        "unidade_delpi": "02",
        "empresa_myweg": "1009",
        "centro": "1106",
        "fornecedor": "50471",
        "data_documento": "2026-11-05",
        "executado_em": "2026-11-06T06:15:00-03:00",
        "publicado_em_preparacao_utc": "2026-11-06T09:16:00+00:00",
        "arquivo_original": xlsx_name,
        "sha256": sha,
        "quantidade_linhas": 2,
        "status_validacao": "VALIDADO",
        "publicacao_atomica": True,
        "contexto_obtido_dos_filtros": True,
    }
    (directory / "manifesto.json").write_text(
        json.dumps(manifesto), encoding="utf-8"
    )
    artifacts = load_invoice_collection(directory, stability_wait_seconds=0)
    assert len(artifacts.records) == 2
    assert artifacts.records[0]["invoice_number"] == "0001234"
    assert artifacts.records[0]["material_weg"] == "000987"
    assert artifacts.records[1]["invoice_number"] == "0001234"


def test_reader_sample_and_empty(tmp_path: Path):
    sample_dir = materialize_sample_collection(tmp_path)
    artifacts = load_invoice_collection(sample_dir, stability_wait_seconds=0)
    assert artifacts.observation_status == "with_records"
    assert len(artifacts.records) == SAMPLE_RECORD_COUNT
    total = sum(Decimal(str(r["quantity_un"])) for r in artifacts.records)
    assert total == SAMPLE_TOTAL_UN

    empty_dir = materialize_empty_collection(tmp_path)
    empty = load_invoice_collection(empty_dir, stability_wait_seconds=0)
    assert empty.observation_status == "empty_signaled_by_sap"
    assert empty.records == []
    assert empty.source_sha256 is None
    assert empty.observed_at is None


def test_missing_manifest_is_not_empty(tmp_path: Path):
    directory = tmp_path / "col-missing"
    directory.mkdir()
    with pytest.raises(InvoiceCollectionIncompleteError, match="manifesto.json ausente"):
        load_invoice_collection(directory, stability_wait_seconds=0)


def test_hash_mismatch_rejects(tmp_path: Path):
    directory = materialize_sample_collection(tmp_path, collection_id="col-tamper")
    manifesto = json.loads((directory / "manifesto.json").read_text(encoding="utf-8"))
    xlsx_path = directory / manifesto["arquivo_original"]
    xlsx_path.write_bytes(xlsx_path.read_bytes() + b"x")
    with pytest.raises(InvoiceCollectionReadError, match="SHA-256"):
        load_invoice_collection(directory, stability_wait_seconds=0)


def test_bad_header_and_unknown_unit(tmp_path: Path):
    directory = (
        tmp_path
        / "filial-02/empresa-1009/centro-1106/fornecedor-50471"
        / "data-documento=2026-11-05/col-bad-header"
    )
    directory.mkdir(parents=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["wrong"] * 7)
    xlsx_path = directory / "bad.xlsx"
    workbook.save(xlsx_path)
    sha = __import__("hashlib").sha256(xlsx_path.read_bytes()).hexdigest()
    manifesto = {
        "schema_version": 1,
        "collection_id": "col-bad-header",
        "origem": "MyWEG",
        "tipo_relatorio": "notas_fiscais_emitidas",
        "unidade_delpi": "02",
        "empresa_myweg": "1009",
        "centro": "1106",
        "fornecedor": "50471",
        "data_documento": "2026-11-05",
        "executado_em": "2026-11-06T06:15:00-03:00",
        "publicado_em_preparacao_utc": "2026-11-06T09:16:00+00:00",
        "arquivo_original": "bad.xlsx",
        "sha256": sha,
        "quantidade_linhas": 0,
        "status_validacao": "VALIDADO",
        "publicacao_atomica": True,
        "contexto_obtido_dos_filtros": True,
    }
    (directory / "manifesto.json").write_text(json.dumps(manifesto), encoding="utf-8")
    with pytest.raises(InvoiceCollectionReadError, match="Cabeçalho"):
        load_invoice_collection(directory, stability_wait_seconds=0)

    # Unidade desconhecida no contrato HTTP
    bad_unit = build_sample_2026_11_05_records()[:1]
    bad_unit[0] = dict(bad_unit[0])
    bad_unit[0]["source_unit"] = "KG"
    bad_unit[0]["quantity_un"] = None
    bad_unit[0]["unit_comparability"] = "non_comparable"
    payload = _payload_from_records(bad_unit, collection_id="col-kg")
    result = validate_ingest_observation(payload)
    assert not result.ok
    assert any(issue.code == "unknown_unit" for issue in result.issues)


def test_ingest_idempotent_conflict_and_equivalent(tmp_path: Path):
    repo = InMemoryInvoiceRepo()
    service = MyWegInvoiceObservationsService(repo)
    records = build_sample_2026_11_05_records()
    payload = _payload_from_records(records, collection_id="col-idem")
    key = build_idempotency_key(
        collection_id="col-idem", payload_sha256=payload["payload_sha256"]
    )

    first = service.ingest_observation(payload, idempotency_key=key, caller_app="test")
    assert first["created"] is True
    second = service.ingest_observation(payload, idempotency_key=key, caller_app="test")
    assert second["created"] is False
    assert second["id"] == first["id"]
    assert len(repo.observations) == 1

    conflict = dict(payload)
    conflict["records"] = records[:21]
    conflict["record_count"] = 21
    conflict["payload_sha256"] = compute_payload_sha256(conflict["records"])
    conflict["semantic_sha256"] = compute_semantic_sha256(conflict["records"])
    with pytest.raises(MyWegInvoiceObservationConflict):
        service.ingest_observation(
            conflict,
            idempotency_key=build_idempotency_key(
                collection_id="col-idem",
                payload_sha256=conflict["payload_sha256"],
            ),
        )

    # Outro collection_id, mesmo conteúdo semântico
    twin = _payload_from_records(records, collection_id="col-idem-twin")
    twin_key = build_idempotency_key(
        collection_id="col-idem-twin", payload_sha256=twin["payload_sha256"]
    )
    twin_result = service.ingest_observation(
        twin, idempotency_key=twin_key, caller_app="test"
    )
    assert twin_result["created"] is True
    assert twin_result["equivalentObservationCount"] == 1
    assert twin_result["semanticSha256"] == first["semanticSha256"]
    # payload pode ser igual; source_sha256 simulado igual — semantic é a prova


def test_partial_failure_leaves_nothing():
    repo = InMemoryInvoiceRepo()
    repo.fail_after_header = True
    service = MyWegInvoiceObservationsService(repo)
    payload = _payload_from_records(
        build_sample_2026_11_05_records(), collection_id="col-partial"
    )
    key = build_idempotency_key(
        collection_id="col-partial", payload_sha256=payload["payload_sha256"]
    )
    with pytest.raises(RuntimeError, match="forced partial failure"):
        service.ingest_observation(payload, idempotency_key=key)
    assert repo.observations == {}
    assert repo.items == {}


def test_empty_observation_ingest():
    repo = InMemoryInvoiceRepo()
    service = MyWegInvoiceObservationsService(repo)
    payload = _payload_from_records(
        [],
        collection_id="col-empty",
        observation_status="empty_signaled_by_sap",
        source_sha256=None,
        document_date="2026-11-01",
        observed_at=None,
    )
    key = build_idempotency_key(
        collection_id="col-empty", payload_sha256=payload["payload_sha256"]
    )
    result = service.ingest_observation(payload, idempotency_key=key)
    assert result["created"] is True
    assert result["recordCount"] == 0
    assert result["observationStatus"] == "empty_signaled_by_sap"


def test_auth_and_rbac_routes(monkeypatch):
    assert _is_internal_integration("/integrations/myweg/invoice-observations")
    assert _is_internal_integration(
        "/apps/production-control-api/integrations/myweg/invoice-observations"
    )
    assert not _is_internal_integration("/myweg/invoice-observations")

    repo = InMemoryInvoiceRepo()
    service = MyWegInvoiceObservationsService(repo)
    app = FastAPI()
    app.include_router(integration_myweg_routes.router)
    app.include_router(myweg_invoice_observations_routes.router)
    monkeypatch.setattr(
        integration_myweg_routes,
        "build_myweg_invoice_observations_service",
        lambda: service,
    )
    monkeypatch.setattr(
        myweg_invoice_observations_routes,
        "build_myweg_invoice_observations_service",
        lambda: service,
    )
    client = TestClient(app)

    payload = _payload_from_records(
        build_sample_2026_11_05_records(), collection_id="col-http"
    )
    assert (
        client.post("/integrations/myweg/invoice-observations", json=payload).status_code
        == 401
    )

    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "invoice-e1-secret")
    from delpi_auth import service_token as service_token_mod

    monkeypatch.setattr(
        service_token_mod,
        "request_has_valid_internal_service_token",
        lambda request: request.headers.get("X-Delpi-Service-Token")
        == "invoice-e1-secret",
    )

    bad_branch = dict(payload)
    bad_branch["branch"] = "01"
    denied_branch = client.post(
        "/integrations/myweg/invoice-observations",
        json=bad_branch,
        headers={
            "X-Delpi-Service-Token": "invoice-e1-secret",
            "Idempotency-Key": build_idempotency_key(
                collection_id="col-http",
                payload_sha256=payload["payload_sha256"],
            ),
        },
    )
    assert denied_branch.status_code == 422

    key = build_idempotency_key(
        collection_id="col-http", payload_sha256=payload["payload_sha256"]
    )
    created = client.post(
        "/integrations/myweg/invoice-observations",
        json=payload,
        headers={
            "X-Delpi-Service-Token": "invoice-e1-secret",
            "Idempotency-Key": key,
            "X-Delpi-Caller-App": "test",
        },
    )
    assert created.status_code == 201
    replay = client.post(
        "/integrations/myweg/invoice-observations",
        json=payload,
        headers={
            "X-Delpi-Service-Token": "invoice-e1-secret",
            "Idempotency-Key": key,
        },
    )
    assert replay.status_code == 200

    monkeypatch.setattr(
        myweg_invoice_observations_routes,
        "resolve_user",
        lambda request: SimpleNamespace(
            is_superadmin=False,
            permissions={PC_ACCESS, PC_VIEW_FILIAL_02},
        ),
    )
    assert client.get("/myweg/invoice-observations").status_code == 403

    monkeypatch.setattr(
        myweg_invoice_observations_routes,
        "resolve_user",
        lambda request: SimpleNamespace(
            is_superadmin=False,
            permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_01},
        ),
    )
    assert client.get("/myweg/invoice-observations").status_code == 403

    monkeypatch.setattr(
        myweg_invoice_observations_routes,
        "resolve_user",
        lambda request: SimpleNamespace(
            is_superadmin=False,
            permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02},
        ),
    )
    listed = client.get("/myweg/invoice-observations?documentDate=2026-11-05")
    assert listed.status_code == 200
    obs_id = created.json()["data"]["id"]
    detail = client.get(f"/myweg/invoice-observations/{obs_id}")
    assert detail.status_code == 200
    items = client.get(f"/myweg/invoice-observations/{obs_id}/items")
    assert items.status_code == 200
    assert items.json()["data"]["total"] == SAMPLE_RECORD_COUNT


def test_openapi_operation_ids_unique():
    from production_control_app.main import app

    schema = app.openapi()
    operation_ids = [
        op.get("operationId")
        for path_item in schema["paths"].values()
        for op in path_item.values()
        if isinstance(op, dict) and op.get("operationId")
    ]
    assert "ingest_myweg_invoice_observation_batch" in operation_ids
    assert "list_myweg_invoice_observations" in operation_ids
    assert "get_myweg_invoice_observation" in operation_ids
    assert "list_myweg_invoice_observation_items" in operation_ids
    assert len(operation_ids) == len(set(operation_ids))


def test_migration_v027_present():
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "V027__myweg_invoice_observations.sql"
    )
    text = migration.read_text(encoding="utf-8")
    assert "myweg_invoice_observations" in text
    assert "myweg_invoice_observation_items" in text
    assert "semantic_sha256" in text


def test_needs_routes_untouched_by_invoice_paths():
    from production_control_app.interface.http.routes import myweg_needs_routes

    paths = [getattr(route, "path", "") for route in myweg_needs_routes.router.routes]
    assert all("invoice" not in path for path in paths)


def test_cli_dry_run(tmp_path: Path, monkeypatch, capsys):
    directory = materialize_sample_collection(tmp_path)
    monkeypatch.delenv("API_DELPI_INTERNAL_SERVICE_TOKEN", raising=False)
    code = cli_main(
        [
            "--dry-run",
            "--directory",
            str(directory),
            "--json",
        ]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["recordCount"] == SAMPLE_RECORD_COUNT
    assert out["observationStatus"] == "with_records"


def test_expected_headers_match_real_layout():
    assert EXPECTED_HEADERS[0] == "Nº nota fiscal"
    assert EXPECTED_HEADERS[6] == "Data de Saída"
