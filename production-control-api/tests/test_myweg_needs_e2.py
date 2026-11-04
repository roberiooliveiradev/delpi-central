"""E2 — ingestão S2S, persistência e consultas MyWEG Necessidades."""

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

from production_control_app.application.services.myweg_needs_service import MyWegNeedsService
from production_control_app.core.security import (
    PC_ACCESS,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_01,
    PC_VIEW_FILIAL_02,
)
from production_control_app.domain.errors import MyWegNeedsBatchConflict
from production_control_app.domain.myweg_needs_contract import (
    CONTRACT_VERSION,
    build_idempotency_key,
    compute_payload_sha256,
    decimal_to_canonical_str,
)
from production_control_app.domain.services.myweg_needs_normalization import (
    normalize_source_records,
)
from production_control_app.infrastructure.persistence.postgres_myweg_needs_repository import (
    MyWegNeedsCollectionConflict,
)
from production_control_app.interface.http.routes import (
    integration_myweg_routes,
    myweg_needs_routes,
)
from production_control_app.middleware.auth_middleware import _is_internal_integration
from tests.fixtures.myweg.sanitized_real_format import (
    SAMPLE_TOTAL_MI,
    SAMPLE_TOTAL_UN,
    build_sanitized_real_format_records,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "myweg"
_TOKEN = "myweg-e2-internal-secret"


class InMemoryMyWegNeedsRepository:
    """Fake thread-safe com UNIQUE(collection_id) realista."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.batches: dict[str, dict] = {}
        self.records: dict[str, list[dict]] = {}
        self.fail_after_batch_insert = False

    def find_by_collection_id(self, collection_id: str) -> dict | None:
        with self._lock:
            for batch in self.batches.values():
                if batch["collection_id"] == collection_id:
                    return dict(batch)
        return None

    def find_by_id(self, batch_id: str) -> dict | None:
        with self._lock:
            batch = self.batches.get(batch_id)
            return dict(batch) if batch else None

    def insert_accepted_batch(self, **kwargs):
        with self._lock:
            for batch in self.batches.values():
                if batch["collection_id"] == kwargs["collection_id"]:
                    raise MyWegNeedsCollectionConflict("duplicate collection_id")
            batch_id = str(uuid.uuid4())
            batch = {
                "id": batch_id,
                "collection_id": kwargs["collection_id"],
                "branch": kwargs["branch"],
                "myweg_company_code": kwargs["myweg_company_code"],
                "myweg_work_center": kwargs["myweg_work_center"],
                "contract_version": kwargs["contract_version"],
                "collected_at": kwargs["collected_at"].isoformat(),
                "exported_at": kwargs["exported_at"].isoformat(),
                "collection_date": kwargs["collection_date"].isoformat(),
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "payload_sha256": kwargs["payload_sha256"],
                "source_files": dict(kwargs["source_files"]),
                "record_count": kwargs["record_count"],
                "total_quantidade_un": decimal_to_canonical_str(
                    kwargs["total_quantidade_un"]
                ),
                "total_quantidade_mi": decimal_to_canonical_str(
                    kwargs["total_quantidade_mi"]
                ),
                "status": "accepted",
                "idempotency_key": kwargs["idempotency_key"],
                "caller_app": kwargs["caller_app"],
            }
            if self.fail_after_batch_insert:
                # Simula falha após header e antes do commit → sem persistência.
                raise RuntimeError("forced partial failure")
            self.batches[batch_id] = batch
            self.records[batch_id] = [
                {
                    **record,
                    "id": str(uuid.uuid4()),
                    "batch_id": batch_id,
                    "line_no": index,
                }
                for index, record in enumerate(kwargs["records"], start=1)
            ]
            return dict(batch)

    def list_batches(self, *, page: int, page_size: int) -> dict:
        items = sorted(
            self.batches.values(),
            key=lambda row: (
                row["collected_at"],
                row["imported_at"],
                row["collection_id"],
            ),
            reverse=True,
        )
        offset = (page - 1) * page_size
        return {
            "page": page,
            "pageSize": page_size,
            "total": len(items),
            "items": [dict(item) for item in items[offset : offset + page_size]],
        }

    def get_latest_batch(self) -> dict | None:
        data = self.list_batches(page=1, page_size=1)
        return data["items"][0] if data["items"] else None

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
        rows = list(self.records.get(batch_id, []))
        needle = (search or "").strip().lower()
        if needle:
            rows = [
                row
                for row in rows
                if needle in str(row.get("material_weg_tratado") or "").lower()
                or needle in str(row.get("codigo_referencia_weg") or "").lower()
                or needle in str(row.get("origem_material_weg") or "").lower()
                or needle in str(row.get("documento") or "").lower()
            ]
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


def _source_files() -> dict[str, str]:
    return {
        "necessidades_tratadas_csv_sha256": "a" * 64,
        "necessidades_tratadas_xlsx_sha256": "b" * 64,
        "para_conferencia_pcp_csv_sha256": "c" * 64,
        "resumo_json_sha256": "d" * 64,
    }


def _build_payload(records: list[dict], *, collection_id: str = "col-e2-001") -> dict:
    source = normalize_source_records(records)
    assert source.ok, source.issues
    totals_un = sum(
        (Decimal(str(row["quantidade_original_un"])) for row in source.records),
        Decimal("0"),
    )
    totals_mi = sum(
        (Decimal(str(row["quantidade_mi"])) for row in source.records),
        Decimal("0"),
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "collection_id": collection_id,
        "branch": "02",
        "myweg_company_code": "1009",
        "myweg_work_center": "1106",
        "collected_at": "2026-11-04T08:00:00-03:00",
        "exported_at": "2026-11-04T08:10:00-03:00",
        "source_files": _source_files(),
        "record_count": len(source.records),
        "totals": {
            "quantidade_original_un": decimal_to_canonical_str(totals_un),
            "quantidade_mi": decimal_to_canonical_str(totals_mi),
        },
        "payload_sha256": compute_payload_sha256(source.records),
        "records": records,
    }


def _service(repo: InMemoryMyWegNeedsRepository | None = None) -> tuple[MyWegNeedsService, InMemoryMyWegNeedsRepository]:
    repository = repo or InMemoryMyWegNeedsRepository()
    return MyWegNeedsService(repository), repository


def test_auth_bypass_includes_myweg_paths():
    assert _is_internal_integration("/integrations/myweg/need-batches")
    assert _is_internal_integration("/apps/production-control-api/integrations/myweg/need-batches")
    assert not _is_internal_integration("/myweg/need-batches")


def test_ac01_ac02_ingest_reference_batch_preserves_empty_refs():
    service, repo = _service()
    records = json.loads(
        (_FIXTURES / "planilha_real_sanitizada.json").read_text(encoding="utf-8")
    )["records"]
    payload = _build_payload(records, collection_id="col-ref-532")
    key = build_idempotency_key(
        collection_id=payload["collection_id"],
        payload_sha256=payload["payload_sha256"],
    )
    result = service.ingest_batch(payload, idempotency_key=key, caller_app="myweg-linux-connector")
    assert result["created"] is True
    assert result["recordCount"] == 532
    assert result["totals"]["quantidade_original_un"] == decimal_to_canonical_str(SAMPLE_TOTAL_UN)
    assert result["totals"]["quantidade_mi"] == decimal_to_canonical_str(SAMPLE_TOTAL_MI)
    stored_records = repo.records[result["id"]]
    empty = [row for row in stored_records if row.get("codigo_referencia_weg") is None]
    assert len(empty) == 2
    assert len(stored_records) == 532


def test_ac03_two_collections_different_dates_remain_available():
    service, repo = _service()
    rows = build_sanitized_real_format_records()[:3]
    first = service.ingest_batch(
        _build_payload(rows, collection_id="col-day-1"),
        idempotency_key=None,
    )
    second_payload = _build_payload(rows, collection_id="col-day-2")
    second_payload["collected_at"] = "2026-11-05T08:00:00-03:00"
    second_payload["exported_at"] = "2026-11-05T08:10:00-03:00"
    # recalcular sha porque records iguais — ok; collection_id diferente
    second = service.ingest_batch(second_payload, idempotency_key=None)
    assert first["id"] != second["id"]
    assert len(repo.batches) == 2
    listed = service.list_batches(
        SimpleNamespace(is_superadmin=True, permissions=set()),
        page=1,
        page_size=10,
    )
    assert listed["total"] == 2


def test_ac04_identical_resubmit_does_not_duplicate():
    service, repo = _service()
    rows = build_sanitized_real_format_records()[:4]
    payload = _build_payload(rows, collection_id="col-idem")
    key = build_idempotency_key(
        collection_id=payload["collection_id"],
        payload_sha256=payload["payload_sha256"],
    )
    first = service.ingest_batch(payload, idempotency_key=key)
    second = service.ingest_batch(payload, idempotency_key=key)
    assert first["created"] is True
    assert second["created"] is False
    assert first["id"] == second["id"]
    assert len(repo.batches) == 1
    assert len(repo.records[first["id"]]) == 4


def test_ac05_same_collection_different_hash_conflicts():
    service, _repo = _service()
    rows = build_sanitized_real_format_records()[:3]
    payload = _build_payload(rows, collection_id="col-conflict")
    service.ingest_batch(payload, idempotency_key=None)
    altered = build_sanitized_real_format_records()[3:6]
    other = _build_payload(altered, collection_id="col-conflict")
    with pytest.raises(MyWegNeedsBatchConflict):
        service.ingest_batch(other, idempotency_key=None)


def test_ac06_different_collections_identical_payload_both_kept():
    service, repo = _service()
    rows = build_sanitized_real_format_records()[:5]
    a = service.ingest_batch(_build_payload(rows, collection_id="col-a"), idempotency_key=None)
    b = service.ingest_batch(_build_payload(rows, collection_id="col-b"), idempotency_key=None)
    assert a["payloadSha256"] == b["payloadSha256"]
    assert a["id"] != b["id"]
    assert len(repo.batches) == 2


def test_ac07_partial_failure_rolls_back_and_keeps_previous():
    service, repo = _service()
    rows = build_sanitized_real_format_records()[:2]
    previous = service.ingest_batch(
        _build_payload(rows, collection_id="col-prev"),
        idempotency_key=None,
    )
    repo.fail_after_batch_insert = True
    with pytest.raises(RuntimeError):
        service.ingest_batch(
            _build_payload(rows, collection_id="col-fail"),
            idempotency_key=None,
        )
    assert len(repo.batches) == 1
    assert previous["id"] in repo.batches
    latest = service.get_latest_batch(SimpleNamespace(is_superadmin=True, permissions=set()))
    assert latest["id"] == previous["id"]


def test_ac08_s2s_and_jwt_authz_rejects():
    repo = InMemoryMyWegNeedsRepository()
    service = MyWegNeedsService(repo)

    app = FastAPI()
    app.include_router(integration_myweg_routes.router)
    app.include_router(myweg_needs_routes.router)

    def _build():
        return service

    integration_myweg_routes.build_myweg_needs_service = _build  # type: ignore[attr-defined]
    myweg_needs_routes.build_myweg_needs_service = _build  # type: ignore[attr-defined]

    client = TestClient(app)
    rows = build_sanitized_real_format_records()[:2]
    payload = _build_payload(rows, collection_id="col-auth")

    # Sem token S2S
    assert client.post("/integrations/myweg/need-batches", json=payload).status_code == 401

    # Filial 01 no payload
    monkey_payload = dict(payload)
    monkey_payload["branch"] = "01"
    # precisa do token — set via env no handler
    import os

    os.environ["API_DELPI_INTERNAL_SERVICE_TOKEN"] = _TOKEN
    bad_branch = client.post(
        "/integrations/myweg/need-batches",
        json=monkey_payload,
        headers={"X-Delpi-Service-Token": _TOKEN},
    )
    assert bad_branch.status_code == 422

    # JWT sem permissão MyWEG
    def _user_no_perm(request):
        return SimpleNamespace(
            is_superadmin=False,
            permissions={PC_ACCESS, PC_VIEW_FILIAL_02},
        )

    myweg_needs_routes.resolve_user = _user_no_perm  # type: ignore[attr-defined]
    denied = client.get("/myweg/need-batches")
    assert denied.status_code == 403

    # JWT só filial 01
    def _user_filial_01(request):
        return SimpleNamespace(
            is_superadmin=False,
            permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_01},
        )

    myweg_needs_routes.resolve_user = _user_filial_01  # type: ignore[attr-defined]
    assert client.get("/myweg/need-batches").status_code == 403


def test_ac09_ac10_queries_pagination_filters_and_latest():
    service, repo = _service()
    rows = build_sanitized_real_format_records()[:10]
    first = service.ingest_batch(_build_payload(rows, collection_id="col-q1"), idempotency_key=None)
    second = service.ingest_batch(_build_payload(rows, collection_id="col-q2"), idempotency_key=None)
    user = SimpleNamespace(is_superadmin=True, permissions=set())

    # "reinício": nova instância de serviço no mesmo repositório (estado preservado)
    revived = MyWegNeedsService(repo)
    latest = revived.get_latest_batch(user)
    assert latest["id"] in {first["id"], second["id"]}

    page1 = revived.list_batches(user, page=1, page_size=1)
    assert page1["total"] == 2
    assert len(page1["items"]) == 1

    items = revived.list_batch_items(
        user,
        batch_id=first["id"],
        search="MAT-WEG-SANIT-0001",
        remessa_from=date(2026, 11, 15),
        remessa_to=date(2026, 11, 15),
        page=1,
        page_size=5,
    )
    assert items["total"] >= 1
    assert all("MAT-WEG-SANIT-0001" in row["material_weg_tratado"] for row in items["items"])


def test_ac11_migration_file_is_additive_v025():
    migration = Path(__file__).resolve().parents[1] / "migrations" / "V025__myweg_need_batches.sql"
    text = migration.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS production_control.myweg_need_batches" in text
    assert "CREATE TABLE IF NOT EXISTS production_control.myweg_need_records" in text
    assert "DROP TABLE" not in text.upper()
    assert "TRUNCATE" not in text.upper()
    assert "UNIQUE (collection_id)" in text
    assert "payload_sha256" in text
    assert "UNIQUE (payload_sha256)" not in text


def test_ac12_demand_route_module_untouched_by_myweg_paths():
    from production_control_app.interface.http.routes import demand_routes

    paths = [getattr(route, "path", "") for route in demand_routes.router.routes]
    assert "/demand" in paths
    assert all("myweg" not in path for path in paths)


def test_s2s_ingest_happy_path_http():
    import os

    os.environ["API_DELPI_INTERNAL_SERVICE_TOKEN"] = _TOKEN
    service, _repo = _service()
    app = FastAPI()
    app.include_router(integration_myweg_routes.router)
    integration_myweg_routes.build_myweg_needs_service = lambda: service  # type: ignore[attr-defined]
    client = TestClient(app)
    payload = _build_payload(build_sanitized_real_format_records()[:3], collection_id="col-http")
    key = build_idempotency_key(
        collection_id=payload["collection_id"],
        payload_sha256=payload["payload_sha256"],
    )
    response = client.post(
        "/integrations/myweg/need-batches",
        json=payload,
        headers={
            "X-Delpi-Service-Token": _TOKEN,
            "X-Delpi-Caller-App": "myweg-linux-connector",
            "Idempotency-Key": key,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["recordCount"] == 3

    again = client.post(
        "/integrations/myweg/need-batches",
        json=payload,
        headers={
            "X-Delpi-Service-Token": _TOKEN,
            "Idempotency-Key": key,
        },
    )
    assert again.status_code == 200
    assert again.json()["data"]["created"] is False
