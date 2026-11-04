"""E4 — resolução SB1 MyWEG: classificação, dry-run, persistência idempotente."""

from __future__ import annotations

import threading
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.myweg_needs_service import MyWegNeedsService
from production_control_app.application.services.myweg_sb1_resolve_service import (
    MyWegSb1ResolveService,
)
from production_control_app.domain.errors import DelpiGatewayError, MyWegNeedsValidationFailed
from production_control_app.domain.myweg_needs_contract import (
    CONTRACT_VERSION,
    compute_payload_sha256,
    decimal_to_canonical_str,
)
from production_control_app.domain.services.myweg_needs_normalization import (
    normalize_source_records,
)
from production_control_app.domain.services.myweg_sb1_semantics import (
    evaluate_field_semantics,
)
from production_control_app.interface.http.routes import integration_myweg_routes
from production_control_app.middleware.auth_middleware import _is_internal_integration
from tests.fixtures.myweg.sanitized_real_format import (
    SAMPLE_TOTAL_MI,
    SAMPLE_TOTAL_UN,
    build_sanitized_real_format_records,
)
from tests.test_myweg_needs_e2 import InMemoryMyWegNeedsRepository, _build_payload

_TOKEN = "myweg-e4-internal-secret"


class InMemorySb1Repo(InMemoryMyWegNeedsRepository):
    def __init__(self) -> None:
        super().__init__()
        self.runs: dict[str, dict] = {}
        self.resolutions: dict[str, dict] = {}

    def list_all_batch_records(self, *, batch_id: str) -> list[dict]:
        with self._lock:
            rows = list(self.records.get(batch_id, []))
        return [
            {
                "id": row["id"],
                "batch_id": row["batch_id"],
                "line_no": row["line_no"],
                "material_weg_tratado": row["material_weg_tratado"],
                "codigo_referencia_weg": row.get("codigo_referencia_weg"),
                "line_fingerprint": row["line_fingerprint"],
            }
            for row in rows
        ]

    def insert_sb1_resolution_run(self, **kwargs) -> None:
        with self._lock:
            self.runs[kwargs["run_id"]] = dict(kwargs)

    def upsert_sb1_resolutions(self, *, resolution_run_id: str, rows: list[dict]) -> None:
        with self._lock:
            for row in rows:
                key = row["record_id"]
                self.resolutions[key] = {**row, "resolution_run_id": resolution_run_id}


class FakeSb1Gateway:
    def __init__(self, results_by_key: dict[str, dict] | None = None, *, fail: bool = False):
        self.results_by_key = results_by_key or {}
        self.fail = fail
        self.calls = 0

    def lookup_products_sb1_identity(self, *, branch: str, items: list[dict]):
        self.calls += 1
        if self.fail:
            raise DelpiGatewayError("api-delpi down", status_code=503)
        results = []
        for item in items:
            key = item["client_key"]
            seeded = self.results_by_key.get(key)
            if seeded is not None:
                results.append({"client_key": key, **seeded})
                continue
            code = (item.get("product_code") or "").strip() or None
            ref = (item.get("customer_reference") or "").strip() or None
            if code and ref:
                results.append(
                    {
                        "client_key": key,
                        "match_status": "confirmed",
                        "product_code": code,
                        "customer_reference": ref,
                        "verified_product_code": code,
                        "verified_description": f"Desc {code}",
                        "matched_by": "code_and_reference",
                        "reason": None,
                        "candidates": [],
                    }
                )
            elif ref and not code:
                results.append(
                    {
                        "client_key": key,
                        "match_status": "confirmed",
                        "product_code": None,
                        "customer_reference": ref,
                        "verified_product_code": "REFONLY01",
                        "verified_description": "Por referência",
                        "matched_by": "reference_only",
                        "reason": None,
                        "candidates": [],
                    }
                )
            else:
                results.append(
                    {
                        "client_key": key,
                        "match_status": "pending",
                        "product_code": code,
                        "customer_reference": ref,
                        "verified_product_code": None,
                        "verified_description": None,
                        "matched_by": None,
                        "reason": "missing_code_and_reference",
                        "candidates": [],
                    }
                )
        return {
            "data": {
                "branch": branch,
                "summary": {},
                "results": results,
            }
        }


def _mini_records(count: int = 5) -> list[dict]:
    rows = []
    for index in range(count):
        rows.append(
            {
                "material_weg_tratado": f"MAT-E4-{index:04d}",
                "codigo_referencia_weg": f"9{index:07d}",
                "origem_material_weg": "MYWEG-ORIGEM",
                "quantidade": "1000",
                "unidade": "UN",
                "data_remessa": "15/11/2026",
                "documento": f"DOC-{index:04d}",
                "linha_fonte": index + 2,
                "assinatura_registro": f"sig-e4-{index}",
            }
        )
    # Uma linha sem código DELPI informado
    rows.append(
        {
            "material_weg_tratado": "MAT-E4-NOCODE",
            "codigo_referencia_weg": "",
            "origem_material_weg": "MYWEG-ORIGEM",
            "quantidade": "1000",
            "unidade": "UN",
            "data_remessa": "15/11/2026",
            "documento": None,
            "linha_fonte": 99,
            "assinatura_registro": "sig-e4-nocode",
        }
    )
    return rows


def _seed_batch(
    repo: InMemorySb1Repo,
    *,
    records: list[dict] | None = None,
    collection_id: str = "col-e4-001",
) -> dict:
    service = MyWegNeedsService(repo)
    payload = _build_payload(records or _mini_records(), collection_id=collection_id)
    return service.ingest_batch(payload, idempotency_key=None, caller_app="test")


def test_semantics_proof_requires_aligned_pairs() -> None:
    weak = evaluate_field_semantics(
        [
            {
                "product_code": "A",
                "customer_reference": "R",
                "match_status": "divergent",
                "reason": "informed_code_reference_mismatch",
            }
        ]
        * 25
    )
    assert weak["proven"] is False
    assert weak["architecture_decision_required"] is True

    strong = evaluate_field_semantics(
        [
            {
                "product_code": f"C{i}",
                "customer_reference": f"R{i}",
                "match_status": "confirmed",
                "matched_by": "code_and_reference",
                "verified_product_code": f"C{i}",
            }
            for i in range(25)
        ]
    )
    assert strong["proven"] is True


def test_dry_run_does_not_persist() -> None:
    repo = InMemorySb1Repo()
    created = _seed_batch(repo)
    batch_id = created["id"]
    records = repo.list_all_batch_records(batch_id=batch_id)
    gateway = FakeSb1Gateway()
    service = MyWegSb1ResolveService(repo, gateway=gateway)
    result = service.resolve_batch(batch_id=batch_id, dry_run=True)
    assert result["dryRun"] is True
    assert result["persisted"] is False
    assert result["counts"]["confirmed"] >= 1
    assert repo.resolutions == {}
    assert len(result["items"]) == len(records)


def test_persist_blocked_without_semantics() -> None:
    repo = InMemorySb1Repo()
    created = _seed_batch(repo)
    # Forçar resultados sem alinhamento code+reference
    records = repo.list_all_batch_records(batch_id=created["id"])
    results = {
        row["id"]: {
            "match_status": "not_found",
            "product_code": row.get("codigo_referencia_weg"),
            "customer_reference": row.get("material_weg_tratado"),
            "verified_product_code": None,
            "verified_description": None,
            "matched_by": None,
            "reason": "product_code_and_reference_not_found",
            "candidates": [],
        }
        for row in records
    }
    service = MyWegSb1ResolveService(repo, gateway=FakeSb1Gateway(results))
    with pytest.raises(MyWegNeedsValidationFailed):
        service.resolve_batch(batch_id=created["id"], dry_run=False)


def test_persist_idempotent_when_semantics_proven() -> None:
    repo = InMemorySb1Repo()
    proof_records = []
    for i in range(25):
        proof_records.append(
            {
                "material_weg_tratado": f"MAT-PROOF-{i:04d}",
                "codigo_referencia_weg": f"9{i:07d}",
                "origem_material_weg": "MYWEG-ORIGEM",
                "quantidade": "1000",
                "unidade": "UN",
                "data_remessa": "15/11/2026",
                "documento": None,
                "linha_fonte": i + 2,
                "assinatura_registro": f"sig-proof-{i}",
            }
        )
    created = _seed_batch(
        repo,
        records=proof_records,
        collection_id="col-e4-proof",
    )

    service = MyWegSb1ResolveService(repo, gateway=FakeSb1Gateway())
    first = service.resolve_batch(batch_id=created["id"], dry_run=False)
    assert first["persisted"] is True
    assert first["semantics"]["proven"] is True
    count_after_first = len(repo.resolutions)
    second = service.resolve_batch(batch_id=created["id"], dry_run=False)
    assert second["persisted"] is True
    assert len(repo.resolutions) == count_after_first


def test_gateway_failure_marks_unavailable_not_not_found() -> None:
    repo = InMemorySb1Repo()
    created = _seed_batch(repo)
    service = MyWegSb1ResolveService(repo, gateway=FakeSb1Gateway(fail=True))
    result = service.resolve_batch(batch_id=created["id"], dry_run=True)
    assert result["counts"]["unavailable"] == result["recordCount"]
    assert result["counts"].get("not_found", 0) == 0
    assert result["error"] == "protheus_lookup_unavailable"


def test_s2s_resolve_requires_service_token(monkeypatch) -> None:
    repo = InMemorySb1Repo()
    created = _seed_batch(repo, collection_id="col-e4-http")
    service = MyWegSb1ResolveService(repo, gateway=FakeSb1Gateway())

    app = FastAPI()
    app.include_router(integration_myweg_routes.router)

    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", _TOKEN)
    monkeypatch.setattr(
        integration_myweg_routes,
        "build_myweg_sb1_resolve_service",
        lambda: service,
    )

    client = TestClient(app)
    denied = client.post("/integrations/myweg/need-batches/sb1-resolve", json={"dry_run": True})
    assert denied.status_code == 401

    monkeypatch.setattr(
        integration_myweg_routes,
        "request_has_valid_internal_service_token",
        lambda request: True,
    )
    ok = client.post(
        "/integrations/myweg/need-batches/sb1-resolve",
        json={"collection_id": created["collectionId"], "dry_run": True},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["data"]["dryRun"] is True


def test_auth_bypass_includes_sb1_resolve_path() -> None:
    assert _is_internal_integration("/integrations/myweg/need-batches/sb1-resolve")
