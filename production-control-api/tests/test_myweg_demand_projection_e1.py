"""Etapa 1 — projeção interna MyWEG → Demanda (sem wiring em GET /demand)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from production_control_app.application.services.myweg_demand_source_service import (
    MyWegDemandSourceService,
)
from production_control_app.core.security import (
    PC_ACCESS,
    PC_DEMAND_VIEW,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_01,
    PC_VIEW_FILIAL_02,
)
from production_control_app.domain.errors import InvalidBranch, MyWegNeedsBatchNotFound
from production_control_app.domain.myweg_demand_source_contract import (
    WEG_LINHARES_CUSTOMER_CODE,
    WEG_LINHARES_CUSTOMER_NAME,
    WEG_LINHARES_CUSTOMER_STORE,
)
from production_control_app.domain.services.myweg_demand_projection import (
    is_coverage_eligible,
    project_myweg_demand_lines,
    summarize_projection,
)
from production_control_app.domain.services.myweg_needs_comparison import aggregate_needs


def _row(
    *,
    record_id: str,
    material: str,
    remessa: str,
    qty_un: str,
    qty_mi: str | None = None,
    code: str | None = None,
    verified: str | None = None,
    status: str = "pending",
    matched_by: str | None = None,
    line_no: int = 1,
) -> dict:
    qty = Decimal(qty_un)
    mi = qty_mi if qty_mi is not None else str(qty / Decimal("1000"))
    return {
        "id": record_id,
        "line_no": line_no,
        "material_weg_tratado": material,
        "codigo_referencia_weg": code,
        "data_remessa": remessa,
        "quantidade_original_un": qty_un,
        "quantidade_mi": mi,
        "sb1_resolution": {
            "status": status,
            "protheus_product_code": verified,
            "matched_by": matched_by,
        },
    }


def _user(*perms: str) -> SimpleNamespace:
    return SimpleNamespace(is_superadmin=False, permissions=set(perms))


class _FakeRepo:
    def __init__(
        self,
        *,
        latest: dict | None = None,
        rows: list[dict] | None = None,
        by_collected: list[dict] | None = None,
    ) -> None:
        self.latest = latest
        self.rows = rows or []
        self.by_collected = by_collected
        self.compare_calls: list[str] = []

    def get_latest_batch(self) -> dict | None:
        if self.by_collected is not None:
            ordered = sorted(
                self.by_collected,
                key=lambda b: (
                    str(b.get("collected_at") or ""),
                    str(b.get("imported_at") or ""),
                    str(b.get("collection_id") or ""),
                ),
                reverse=True,
            )
            return ordered[0] if ordered else None
        return self.latest

    def list_batch_records_for_compare(self, *, batch_id: str) -> list[dict]:
        self.compare_calls.append(batch_id)
        return list(self.rows)


def test_positive_confirmed_product_multiple_remessas() -> None:
    rows = [
        _row(
            record_id="r1",
            material="M1",
            remessa="2026-11-10",
            qty_un="100",
            verified="90260001",
            status="confirmed",
            matched_by="code_and_reference",
            line_no=1,
        ),
        _row(
            record_id="r2",
            material="M1",
            remessa="2026-11-17",
            qty_un="250",
            verified="90260001",
            status="confirmed",
            matched_by="code_and_reference",
            line_no=2,
        ),
    ]
    lines = project_myweg_demand_lines(
        rows, batch_id="batch-a", collected_at="2026-11-08T08:00:25-03:00"
    )
    assert len(lines) == 2
    assert all(line.coverage_eligible for line in lines)
    assert lines[0].due_date.isoformat() == "2026-11-10"
    assert lines[1].open_quantity == Decimal("250")
    assert lines[0].customer_code == WEG_LINHARES_CUSTOMER_CODE
    assert lines[0].customer_store == WEG_LINHARES_CUSTOMER_STORE
    assert lines[0].customer_name == WEG_LINHARES_CUSTOMER_NAME
    assert lines[0].id == "myweg:batch-a:r1"
    assert lines[0].id != "MyWEG"
    assert lines[0].source == "myweg"
    assert lines[0].display_order == "MyWEG"


def test_sibling_same_product_different_quantities_not_merged_across_records() -> None:
    rows = [
        _row(
            record_id="r-old",
            material="M1",
            remessa="2026-11-10",
            qty_un="100",
            verified="90260001",
            status="confirmed",
            matched_by="code_and_reference",
        ),
        _row(
            record_id="r-new",
            material="M1",
            remessa="2026-11-10",
            qty_un="180",
            verified="90260001",
            status="confirmed",
            matched_by="code_and_reference",
            line_no=2,
        ),
    ]
    lines = project_myweg_demand_lines(rows, batch_id="b1")
    assert len(lines) == 2
    assert {line.open_quantity for line in lines} == {Decimal("100"), Decimal("180")}
    # aggregate_needs continua disponível para consolidação futura por produto+remessa
    agg = aggregate_needs(rows)
    assert len(agg) == 1
    assert next(iter(agg.values())).quantity_un == Decimal("280")


def test_negative_unconfirmed_identity_not_coverage_eligible() -> None:
    rows = [
        _row(
            record_id="r-pending",
            material="M-PEND",
            remessa="2026-11-12",
            qty_un="40",
            status="pending",
        ),
        _row(
            record_id="r-amb",
            material="M-AMB",
            remessa="2026-11-12",
            qty_un="10",
            status="ambiguous",
            code="80000001",
        ),
    ]
    lines = project_myweg_demand_lines(rows, batch_id="b1")
    assert len(lines) == 2
    assert all(not line.coverage_eligible for line in lines)
    assert all(line.open_quantity > 0 for line in lines)
    assert lines[0].product_code is None
    summary = summarize_projection(lines)
    assert summary["coverage_eligible_count"] == 0
    assert summary["line_count"] == 2


def test_provisional_sample_traceable_but_not_coverage_eligible() -> None:
    rows = [
        _row(
            record_id="r-sample",
            material="19740817",
            remessa="2026-11-20",
            qty_un="12",
            verified="80016673",
            status="confirmed",
            matched_by="provisional_highest_sample_code_no_production",
        )
    ]
    lines = project_myweg_demand_lines(rows, batch_id="b1")
    assert len(lines) == 1
    assert lines[0].coverage_eligible is False
    assert lines[0].product_code == "80016673"
    assert lines[0].resolution_status == "confirmed"
    assert is_coverage_eligible(
        identity_kind="verified_code",
        resolution_status="confirmed",
        matched_by="provisional_sample_code_no_production",
        verified_product_code="80015414",
    ) is False


def test_quantity_un_not_confused_with_mi() -> None:
    rows = [
        _row(
            record_id="r-qty",
            material="M1",
            remessa="2026-11-10",
            qty_un="1500",
            qty_mi="1.5",
            verified="90260001",
            status="confirmed",
            matched_by="reference_prefer_production",
        )
    ]
    line = project_myweg_demand_lines(rows, batch_id="b1")[0]
    assert line.open_quantity == Decimal("1500")
    assert line.quantity_mi == Decimal("1.5")
    payload = line.to_dict()
    assert payload["open_quantity"] == "1500"
    assert payload["quantity_mi"] == "1.5"


def test_myweg_only_product_projected() -> None:
    rows = [
        _row(
            record_id="r-exclusive",
            material="M-EX",
            remessa="2026-12-01",
            qty_un="5",
            verified="90269999",
            status="confirmed",
            matched_by="code_and_reference",
        )
    ]
    lines = project_myweg_demand_lines(rows, batch_id="b1")
    assert len(lines) == 1
    assert lines[0].coverage_eligible is True
    assert not hasattr(lines[0], "sales_order")
    assert "sales_order" not in lines[0].to_dict()


def test_service_uses_latest_by_collected_at_not_import_order() -> None:
    older = {
        "id": "batch-old",
        "collection_id": "old",
        "branch": "02",
        "status": "accepted",
        "collected_at": "2026-11-07T08:00:00-03:00",
        "imported_at": "2026-11-08T18:00:00-03:00",
        "collection_date": "2026-11-07",
        "record_count": 1,
    }
    newer = {
        "id": "batch-new",
        "collection_id": "new",
        "branch": "02",
        "status": "accepted",
        "collected_at": "2026-11-08T08:00:00-03:00",
        "imported_at": "2026-11-08T09:00:00-03:00",
        "collection_date": "2026-11-08",
        "record_count": 1,
    }
    repo = _FakeRepo(
        by_collected=[older, newer],
        rows=[
            _row(
                record_id="r1",
                material="M1",
                remessa="2026-11-10",
                qty_un="10",
                verified="90260001",
                status="confirmed",
                matched_by="code_and_reference",
            )
        ],
    )
    user = _user(PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02, PC_DEMAND_VIEW)
    result = MyWegDemandSourceService(repo).project_latest(user, branch="02")
    assert result["batch"]["id"] == "batch-new"
    assert repo.compare_calls == ["batch-new"]
    assert result["wired_to_demand_endpoint"] is False


def test_service_rejects_filial_01() -> None:
    repo = _FakeRepo(latest={"id": "x", "branch": "02", "record_count": 0})
    user = _user(PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_01, PC_DEMAND_VIEW)
    with pytest.raises(InvalidBranch):
        MyWegDemandSourceService(repo).project_latest(user, branch="01")


def test_service_empty_batch_raises() -> None:
    repo = _FakeRepo(latest=None)
    user = _user(PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02, PC_DEMAND_VIEW)
    with pytest.raises(MyWegNeedsBatchNotFound):
        MyWegDemandSourceService(repo).project_latest(user, branch="02")


def test_service_requires_permissions() -> None:
    repo = _FakeRepo(
        latest={
            "id": "b1",
            "branch": "02",
            "collected_at": datetime(2026, 11, 8, tzinfo=timezone.utc).isoformat(),
            "record_count": 0,
            "status": "accepted",
        },
        rows=[],
    )
    with pytest.raises(PermissionError):
        MyWegDemandSourceService(repo).project_latest(
            _user(PC_ACCESS, PC_VIEW_FILIAL_02), branch="02"
        )


def test_overlap_marker_fields_ready_for_etapa2_without_dedup() -> None:
    """Produto presente no MyWEG (e hipoteticamente no Protheus) — sem deduplicar aqui."""
    rows = [
        _row(
            record_id="r-overlap",
            material="M-OV",
            remessa="2026-11-08",
            qty_un="30",
            verified="90261111",
            status="confirmed",
            matched_by="code_and_reference",
        )
    ]
    line = project_myweg_demand_lines(rows, batch_id="b1")[0]
    assert line.coverage_eligible is True
    assert line.customer_code == "000001"
    assert line.due_date.isoformat() == "2026-11-08"
    # Etapa 1 não inventa sales_order nem subtrai NF.
    assert "sales_order" not in line.to_dict()
