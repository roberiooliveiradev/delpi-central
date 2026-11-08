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
        self.fail_after_run_insert = False

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

    def persist_sb1_resolution_batch(self, **kwargs) -> None:
        """Simula transação única: falha após run → nada permanece."""
        run_id = kwargs["run_id"]
        rows = list(kwargs.get("rows") or [])
        with self._lock:
            staged_run = {
                "run_id": run_id,
                "batch_id": kwargs["batch_id"],
                "dry_run": kwargs["dry_run"],
                "caller_app": kwargs.get("caller_app"),
                "status": kwargs["status"],
                "counts": dict(kwargs.get("counts") or {}),
                "semantics_proven": kwargs.get("semantics_proven"),
                "semantics_notes": kwargs.get("semantics_notes"),
            }
            if self.fail_after_run_insert:
                raise RuntimeError("forced upsert failure after run insert")
            self.runs[run_id] = staged_run
            for row in rows:
                key = row["record_id"]
                self.resolutions[key] = {**row, "resolution_run_id": run_id}

    def list_batch_items(
        self,
        *,
        batch_id: str,
        search: str,
        remessa_from,
        remessa_to,
        page: int,
        page_size: int,
    ) -> dict:
        """Espelha filtros JWT incluindo código DELPI verificado na projeção."""
        with self._lock:
            rows = [dict(row) for row in self.records.get(batch_id, [])]
            resolutions = dict(self.resolutions)
        for row in rows:
            res = resolutions.get(row["id"])
            if res:
                row["sb1_resolution"] = {
                    "status": res.get("status"),
                    "protheus_product_code": res.get("verified_product_code"),
                    "matched_by": res.get("matched_by"),
                    "resolved_at": res.get("verified_at"),
                    "verified_description": res.get("verified_description"),
                    "reason": res.get("reason"),
                    "informed_product_code": res.get("informed_product_code"),
                    "candidates": res.get("candidates") or [],
                }
        needle = (search or "").strip().lower()
        if needle:
            filtered = []
            for row in rows:
                res = row.get("sb1_resolution") or {}
                hay = " ".join(
                    [
                        str(row.get("material_weg_tratado") or ""),
                        str(row.get("codigo_referencia_weg") or ""),
                        str(row.get("origem_material_weg") or ""),
                        str(row.get("documento") or ""),
                        str(res.get("protheus_product_code") or ""),
                    ]
                ).lower()
                if needle in hay:
                    filtered.append(row)
            rows = filtered
        if remessa_from is not None:
            rows = [
                row
                for row in rows
                if date.fromisoformat(str(row["data_remessa"])[:10]) >= remessa_from
            ]
        if remessa_to is not None:
            rows = [
                row
                for row in rows
                if date.fromisoformat(str(row["data_remessa"])[:10]) <= remessa_to
            ]
        offset = (page - 1) * page_size
        return {
            "page": page,
            "pageSize": page_size,
            "total": len(rows),
            "items": rows[offset : offset + page_size],
        }


class FakeSb1Gateway:
    def __init__(self, results_by_key: dict[str, dict] | None = None, *, fail: bool = False):
        self.results_by_key = results_by_key or {}
        self.fail = fail
        self.calls = 0

    def lookup_products_sb1_identity(
        self,
        *,
        branch: str,
        items: list[dict],
        disambiguation_policy: str | None = None,
    ):
        self.calls += 1
        self.last_policy = disambiguation_policy
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


def test_informed_production_9_propagates_confirmed_despite_shared_reference() -> None:
    """Regressão MyWEG: código 9 informado válido permanece confirmed na resolução PC."""
    repo = InMemorySb1Repo()
    cases = (
        ("11403512", "90261614", "Produto 90261614"),
        ("12322556", "90262016", "Produto 90262016"),
    )
    seed_rows = [
        {
            "material_weg_tratado": material,
            "codigo_referencia_weg": code,
            "origem_material_weg": "MYWEG-ORIGEM",
            "quantidade": "1000",
            "unidade": "UN",
            "data_remessa": "15/11/2026",
            "documento": f"DOC-{code}",
            "linha_fonte": index + 2,
            "assinatura_registro": f"sig-informed-9-{code}",
        }
        for index, (material, code, _desc) in enumerate(cases)
    ]
    created = _seed_batch(
        repo, records=seed_rows, collection_id="col-informed-9-priority"
    )
    records = repo.list_all_batch_records(batch_id=created["id"])
    by_material = {row["material_weg_tratado"]: row for row in records}
    seeded: dict[str, dict] = {}
    for material, code, description in cases:
        record = by_material[material]
        seeded[record["id"]] = {
            "match_status": "confirmed",
            "product_code": code,
            "customer_reference": material,
            "verified_product_code": code,
            "verified_description": description,
            "matched_by": "code_and_reference",
            "reason": None,
            "candidates": [
                {
                    "product_code": code,
                    "customer_reference": material,
                    "description": description,
                },
                {
                    "product_code": "90269999",
                    "customer_reference": material,
                    "description": "Contrapeca",
                },
            ],
        }

    service = MyWegSb1ResolveService(repo, gateway=FakeSb1Gateway(seeded))
    result = service.resolve_batch(batch_id=created["id"], dry_run=True)
    assert result["persisted"] is False
    assert result["counts"]["confirmed"] == 2
    by_key = {item["customer_reference"]: item for item in result["items"]}
    for material, code, description in cases:
        item = by_key[material]
        assert item["status"] == "confirmed"
        assert item["verified_product_code"] == code
        assert item["verified_description"] == description
        assert item["matched_by"] == "code_and_reference"
        assert item["informed_product_code"] == code


def test_skip_if_complete_avoids_second_lookup() -> None:
    repo = InMemorySb1Repo()
    proof_records = []
    for i in range(25):
        proof_records.append(
            {
                "material_weg_tratado": f"MAT-SKIP-{i:04d}",
                "codigo_referencia_weg": f"9{i:07d}",
                "origem_material_weg": "MYWEG-ORIGEM",
                "quantidade": "1000",
                "unidade": "UN",
                "data_remessa": "15/11/2026",
                "documento": None,
                "linha_fonte": i + 2,
                "assinatura_registro": f"sig-skip-{i}",
            }
        )
    created = _seed_batch(repo, records=proof_records, collection_id="col-skip-001")
    gateway = FakeSb1Gateway()
    service = MyWegSb1ResolveService(repo, gateway=gateway)
    first = service.resolve_batch(batch_id=created["id"], dry_run=False)
    assert first["persisted"] is True
    calls_after_first = gateway.calls
    second = service.resolve_batch(
        batch_id=created["id"], dry_run=False, skip_if_complete=True
    )
    assert second["skipped"] is True
    assert second["persisted"] is False
    assert second["status"] == "already_resolved"
    assert gateway.calls == calls_after_first
    assert gateway.last_policy == "prefer_production_over_sample"


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


def test_ac_list_search_material_and_verified_code_totals() -> None:
    """AC-01..AC-06 — filtros/paginação alinhados à projeção SB1."""
    from production_control_app.core.security import (
        PC_ACCESS,
        PC_MYWEG_NEEDS_VIEW,
        PC_VIEW_FILIAL_02,
    )

    repo = InMemorySb1Repo()
    created = _seed_batch(repo, collection_id="col-e4-search")
    records = repo.list_all_batch_records(batch_id=created["id"])
    now = datetime.now(timezone.utc)
    # Injeta projeção sem passar pelo gate de semântica (foco: filtros JWT).
    repo.persist_sb1_resolution_batch(
        run_id=str(uuid.uuid4()),
        batch_id=created["id"],
        dry_run=False,
        caller_app="test",
        status="completed",
        counts={"confirmed": len(records)},
        semantics_proven=True,
        semantics_notes="fixture",
        rows=[
            {
                "record_id": row["id"],
                "batch_id": created["id"],
                "line_fingerprint": row["line_fingerprint"],
                "status": "confirmed",
                "informed_product_code": row.get("codigo_referencia_weg"),
                "customer_reference": row.get("material_weg_tratado"),
                "verified_product_code": f"VER-{row['line_no']:04d}",
                "verified_description": f"Desc {row['line_no']}",
                "matched_by": "code_and_reference",
                "reason": None,
                "candidates": [],
                "verified_at": now,
            }
            for row in records
            if (row.get("codigo_referencia_weg") or "").strip()
        ],
    )

    user = SimpleNamespace(
        permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02},
        is_superadmin=False,
    )
    needs = MyWegNeedsService(repo)

    by_material = needs.list_batch_items(
        user, batch_id=created["id"], search="MAT-E4-0001", page=1, page_size=50
    )
    assert by_material["total"] == 1
    assert by_material["items"][0]["material_weg_tratado"] == "MAT-E4-0001"

    line_no = int(by_material["items"][0]["line_no"])
    verified = by_material["items"][0]["sb1_resolution"]["protheus_product_code"]
    assert verified == f"VER-{line_no:04d}"
    by_verified = needs.list_batch_items(
        user, batch_id=created["id"], search=verified, page=1, page_size=50
    )
    assert by_verified["total"] == 1
    assert by_verified["total"] == len(by_verified["items"])

    unfiltered = needs.list_batch_items(
        user, batch_id=created["id"], search="", page=1, page_size=50
    )
    assert unfiltered["total"] == created["recordCount"]

    zero = needs.list_batch_items(
        user, batch_id=created["id"], search="ZZZ-NO-MATCH-999", page=1, page_size=50
    )
    assert zero["total"] == 0
    assert zero["items"] == []

    # Sem resolução persistida ainda funciona (lote novo).
    repo2 = InMemorySb1Repo()
    created2 = _seed_batch(repo2, collection_id="col-e4-no-res")
    needs2 = MyWegNeedsService(repo2)
    pending = needs2.list_batch_items(
        user, batch_id=created2["id"], search="MAT-E4", page=1, page_size=50
    )
    assert pending["total"] >= 1
    assert pending["items"][0]["sb1_resolution"]["status"] == "pending"


def test_ac_persist_rollback_leaves_no_completed_run() -> None:
    """AC-08/AC-09/AC-11 — falha no upsert não marca execução completed."""
    repo = InMemorySb1Repo()
    proof_records = [
        {
            "material_weg_tratado": f"MAT-TX-{i:04d}",
            "codigo_referencia_weg": f"9{i:07d}",
            "origem_material_weg": "MYWEG-ORIGEM",
            "quantidade": "1000",
            "unidade": "UN",
            "data_remessa": "15/11/2026",
            "documento": None,
            "linha_fonte": i + 2,
            "assinatura_registro": f"sig-tx-{i}",
        }
        for i in range(25)
    ]
    created = _seed_batch(repo, records=proof_records, collection_id="col-e4-tx")
    repo.fail_after_run_insert = True
    service = MyWegSb1ResolveService(repo, gateway=FakeSb1Gateway())
    with pytest.raises(RuntimeError, match="forced upsert failure"):
        service.resolve_batch(batch_id=created["id"], dry_run=False)
    assert repo.runs == {}
    assert repo.resolutions == {}


def test_ac_count_sql_shares_left_join_with_list() -> None:
    """AC estrutural — count_sql referencia res via o mesmo LEFT JOIN do list."""
    from pathlib import Path

    source = Path(
        "production_control_app/infrastructure/persistence/postgres_myweg_needs_repository.py"
    ).read_text(encoding="utf-8")
    # Método list_batch_items deve construir from_join compartilhado.
    assert "from_join" in source
    assert "LEFT JOIN" in source
    assert "COUNT(*) AS total {from_join}" in source or 'COUNT(*) AS total {from_join}' in source
    assert "COALESCE(res.verified_product_code" in source
    # Não pode haver count só sobre records sem join quando o filtro usa res.
    assert "SELECT COUNT(*) AS total FROM {_RECORDS} r WHERE {where}" not in source
