"""Etapa 2 — conciliação analítica NF portal × necessidades (domínio + compare/products)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.myweg_needs_compare_service import (
    MyWegNeedsCompareService,
)
from production_control_app.core.security import (
    PC_ACCESS,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_02,
)
from production_control_app.domain.services.myweg_invoice_reconciliation import (
    COVERAGE_COMPLETE,
    COVERAGE_CONFLICT,
    COVERAGE_PARTIAL,
    COVERAGE_PENDING_INGESTION,
    MANAGERIAL_INVESTIGATE,
    MANAGERIAL_INVOICED,
    MANAGERIAL_OTHER,
    MANAGERIAL_PARTIAL,
    MANAGERIAL_PENDING,
    MANAGERIAL_WITH_DIFFERENCE,
    aggregate_need_quantity_by_material,
    aggregate_posted_nf_by_material,
    apply_managerial_classification,
    build_invoice_window,
    build_reconciliations_for_materials,
    classify_managerial_status,
    enrich_products_with_portal_invoices,
    evaluate_window_coverage,
    materials_by_product_key,
    product_has_invoice_signal,
    reconcile_material,
    select_canonical_observation_for_day,
)
from production_control_app.domain.services.myweg_needs_comparison import (
    aggregate_needs,
    consolidate_by_product,
)
from production_control_app.interface.http.routes import myweg_needs_routes



def test_formulas_reference_cases():
    # Anterior 1000, atual 700, NF 200 → observado -300, ajustado -100
    r = reconcile_material(
        material_weg="M1",
        previous_need_un=Decimal("1000"),
        current_need_un=Decimal("700"),
        posted_nf_un=Decimal("200"),
        coverage_status=COVERAGE_COMPLETE,
        source_observation_ids=["a"],
    )
    assert r.observed_delta_un == Decimal("-300")
    assert r.adjusted_planning_delta_un == Decimal("-100")
    assert r.compatible_reduction_un == Decimal("200")

    r2 = reconcile_material(
        material_weg="M1",
        previous_need_un=Decimal("1000"),
        current_need_un=Decimal("700"),
        posted_nf_un=Decimal("300"),
        coverage_status=COVERAGE_COMPLETE,
        source_observation_ids=["a"],
    )
    assert r2.adjusted_planning_delta_un == Decimal("0")

    r3 = reconcile_material(
        material_weg="M1",
        previous_need_un=Decimal("1000"),
        current_need_un=Decimal("700"),
        posted_nf_un=Decimal("450"),
        coverage_status=COVERAGE_COMPLETE,
        source_observation_ids=["a"],
    )
    assert r3.adjusted_planning_delta_un == Decimal("150")

    # Sem NF com vazio comprovado
    r4 = reconcile_material(
        material_weg="M1",
        previous_need_un=Decimal("1000"),
        current_need_un=Decimal("700"),
        posted_nf_un=Decimal("0"),
        coverage_status=COVERAGE_COMPLETE,
        source_observation_ids=["empty"],
    )
    assert r4.adjusted_planning_delta_un == Decimal("-300")

    # Cobertura parcial → ajuste null
    r5 = reconcile_material(
        material_weg="M1",
        previous_need_un=Decimal("1000"),
        current_need_un=Decimal("700"),
        posted_nf_un=Decimal("200"),
        coverage_status=COVERAGE_PARTIAL,
        source_observation_ids=[],
    )
    assert r5.adjusted_planning_delta_un is None
    assert r5.compatible_reduction_un is None


def test_window_and_coverage_states():
    window = build_invoice_window(
        from_date=date(2026, 11, 1), to_date=date(2026, 11, 5)
    )
    assert window.status == "ok"
    assert window.days[0] == date(2026, 11, 1)
    assert window.days[-1] == date(2026, 11, 4)
    assert len(window.days) == 4

    same = build_invoice_window(
        from_date=date(2026, 11, 5), to_date=date(2026, 11, 5)
    )
    assert same.status == "same_day"
    assert same.days == ()

    selections = [
        select_canonical_observation_for_day([], document_date=d) for d in window.days
    ]
    coverage = evaluate_window_coverage(selections)
    assert coverage["status"] == COVERAGE_PENDING_INGESTION

    # Um dia coberto + faltantes → partial
    obs = [
        {
            "id": "1",
            "document_date": "2026-11-01",
            "semantic_sha256": "a" * 64,
            "payload_sha256": "b" * 64,
            "collection_id": "c1",
            "observation_status": "empty_signaled_by_sap",
            "source_prepared_at": "2026-11-02T09:00:00+00:00",
        }
    ]
    mixed = [
        select_canonical_observation_for_day(obs, document_date=date(2026, 11, 1)),
        select_canonical_observation_for_day([], document_date=date(2026, 11, 2)),
    ]
    assert evaluate_window_coverage(mixed)["status"] == COVERAGE_PARTIAL


def test_equivalent_reexports_single_count_and_conflict():
    day = date(2026, 11, 3)
    equivalent = [
        {
            "id": "obs-1",
            "document_date": day.isoformat(),
            "semantic_sha256": "a" * 64,
            "payload_sha256": "1111" + "a" * 60,
            "collection_id": "col-a",
            "observation_status": "with_records",
            "source_prepared_at": "2026-11-04T08:00:00+00:00",
        },
        {
            "id": "obs-2",
            "document_date": day.isoformat(),
            "semantic_sha256": "a" * 64,
            "payload_sha256": "2222" + "b" * 60,
            "collection_id": "col-b",
            "observation_status": "with_records",
            "source_prepared_at": "2026-11-04T09:00:00+00:00",
        },
    ]
    selected = select_canonical_observation_for_day(equivalent, document_date=day)
    assert selected.status == "selected"
    assert selected.observation_id == "obs-2"  # prepared_at mais recente

    conflict = equivalent + [
        {
            "id": "obs-3",
            "document_date": day.isoformat(),
            "semantic_sha256": "c" * 64,
            "payload_sha256": "3333" + "c" * 60,
            "collection_id": "col-c",
            "observation_status": "with_records",
            "source_prepared_at": "2026-11-04T10:00:00+00:00",
        }
    ]
    bad = select_canonical_observation_for_day(conflict, document_date=day)
    assert bad.status == "conflict"
    assert evaluate_window_coverage([bad])["status"] == COVERAGE_CONFLICT


def test_product_without_observed_change_but_with_nf():
    recon = build_reconciliations_for_materials(
        previous_by_material={"MAT-A": Decimal("500")},
        current_by_material={"MAT-A": Decimal("500")},
        posted_by_material={"MAT-A": Decimal("100")},
        coverage_status=COVERAGE_COMPLETE,
        source_observation_ids=["o1"],
    )
    products = [
        {
            "productKey": "ref:MAT-A",
            "identityKind": "customer_reference",
            "materialWegTratado": "MAT-A",
            "previousQuantityUn": "500",
            "currentQuantityUn": "500",
            "deltaQuantityUn": "0",
            "situation": "unchanged",
            "verifiedProductCode": None,
            "codigoReferenciaWeg": None,
            "remessas": [],
            "probableDateShifts": [],
        }
    ]
    enriched = enrich_products_with_portal_invoices(
        products,
        reconciliations=recon,
        materials_by_key={"ref:MAT-A": {"MAT-A"}},
        coverage_status=COVERAGE_COMPLETE,
    )
    assert enriched[0]["adjustedPlanningDeltaUn"] == "100"
    assert product_has_invoice_signal(enriched[0]) is True


def test_two_materials_same_delpi_no_duplication():
    prev_rows = [
        {
            "material_weg_tratado": "MAT-A",
            "codigo_referencia_weg": "9A",
            "quantidade_original_un": "100",
            "quantidade_mi": "0.1",
            "data_remessa": "2026-11-10",
            "sb1_resolution": {
                "status": "confirmed",
                "protheus_product_code": "DELPI1",
            },
        },
        {
            "material_weg_tratado": "MAT-B",
            "codigo_referencia_weg": "9B",
            "quantidade_original_un": "50",
            "quantidade_mi": "0.05",
            "data_remessa": "2026-11-10",
            "sb1_resolution": {
                "status": "confirmed",
                "protheus_product_code": "DELPI1",
            },
        },
    ]
    curr_rows = [
        {**prev_rows[0], "quantidade_original_un": "80"},
        {**prev_rows[1], "quantidade_original_un": "40"},
    ]
    previous = aggregate_needs(prev_rows)
    current = aggregate_needs(curr_rows)
    products = consolidate_by_product(previous, current, probable_date_shifts=[])
    assert len(products) == 1
    assert products[0]["productKey"] == "code:DELPI1"

    recon = build_reconciliations_for_materials(
        previous_by_material=aggregate_need_quantity_by_material(prev_rows),
        current_by_material=aggregate_need_quantity_by_material(curr_rows),
        posted_by_material={"MAT-A": Decimal("20"), "MAT-B": Decimal("10")},
        coverage_status=COVERAGE_COMPLETE,
        source_observation_ids=["o1"],
    )
    enriched = enrich_products_with_portal_invoices(
        products,
        reconciliations=recon,
        materials_by_key=materials_by_product_key(prev_rows + curr_rows),
        coverage_status=COVERAGE_COMPLETE,
    )
    assert enriched[0]["postedQuantityUn"] == "30"
    assert enriched[0]["observedDeltaUn"] == "-30"
    assert enriched[0]["adjustedPlanningDeltaUn"] == "0"
    assert enriched[0]["invoiceMatchStatus"] == "multi_material_key"


def test_same_material_different_delpi_keys_no_double_count():
    prev_rows = [
        {
            "material_weg_tratado": "MAT-X",
            "codigo_referencia_weg": None,
            "quantidade_original_un": "1000",
            "quantidade_mi": "1",
            "data_remessa": "2026-11-10",
            "sb1_resolution": {"status": "pending"},
        }
    ]
    curr_rows = [
        {
            "material_weg_tratado": "MAT-X",
            "codigo_referencia_weg": None,
            "quantidade_original_un": "700",
            "quantidade_mi": "0.7",
            "data_remessa": "2026-11-10",
            "sb1_resolution": {
                "status": "confirmed",
                "protheus_product_code": "D9",
            },
        }
    ]
    products = consolidate_by_product(
        aggregate_needs(prev_rows),
        aggregate_needs(curr_rows),
        probable_date_shifts=[],
    )
    assert len(products) == 2  # ref + code
    recon = build_reconciliations_for_materials(
        previous_by_material=aggregate_need_quantity_by_material(prev_rows),
        current_by_material=aggregate_need_quantity_by_material(curr_rows),
        posted_by_material={"MAT-X": Decimal("200")},
        coverage_status=COVERAGE_COMPLETE,
        source_observation_ids=["o1"],
    )
    enriched = enrich_products_with_portal_invoices(
        products,
        reconciliations=recon,
        materials_by_key=materials_by_product_key(prev_rows + curr_rows),
        coverage_status=COVERAGE_COMPLETE,
    )
    with_posted = [r for r in enriched if r.get("postedQuantityUn") not in (None, "0")]
    # Quantidade fiscal atribuída uma vez
    assert sum(Decimal(r["postedQuantityUn"]) for r in with_posted) == Decimal("200")
    shared = [r for r in enriched if r.get("invoiceMatchStatus") == "attributed_elsewhere"]
    assert shared  # a outra identidade marca shared


class _NeedsRepo:
    def __init__(self) -> None:
        self.batches: dict[str, dict] = {}
        self.records: dict[str, list[dict]] = {}

    def find_by_id(self, batch_id: str):
        return dict(self.batches[batch_id]) if batch_id in self.batches else None

    def list_batches(self, *, page: int, page_size: int):
        items = sorted(
            self.batches.values(),
            key=lambda b: b["collected_at"],
            reverse=True,
        )
        return {"page": page, "pageSize": page_size, "total": len(items), "items": items}

    def list_batch_records_for_compare(self, *, batch_id: str):
        return list(self.records.get(batch_id, []))

    def insert(self, *, collection_id: str, collected_at: str, rows: list[dict]):
        batch_id = collection_id
        self.batches[batch_id] = {
            "id": batch_id,
            "collection_id": collection_id,
            "branch": "02",
            "status": "accepted",
            "collected_at": collected_at,
            "exported_at": collected_at,
            "collection_date": collected_at[:10],
            "imported_at": collected_at,
            "record_count": len(rows),
            "total_quantidade_un": "0",
            "total_quantidade_mi": "0",
            "payload_sha256": "p" * 64,
            "contract_version": "myweg.needs.batch.v1",
            "myweg_company_code": "1009",
            "myweg_work_center": "1106",
        }
        self.records[batch_id] = rows
        return self.batches[batch_id]


class _InvoiceRepo:
    def __init__(self) -> None:
        self.observations: list[dict] = []
        self.items: dict[str, list[dict]] = {}

    def list_observations_for_document_date_range(self, *, date_from, date_to):
        return [
            dict(o)
            for o in self.observations
            if date_from <= date.fromisoformat(o["document_date"]) <= date_to
        ]

    def list_items_for_observation_ids(self, *, observation_ids: list[str]):
        out: list[dict] = []
        for oid in observation_ids:
            for item in self.items.get(oid, []):
                row = dict(item)
                row["observationId"] = oid
                out.append(row)
        return out


def _user():
    return SimpleNamespace(
        is_superadmin=False,
        permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02},
    )


def test_compare_products_invoice_mode_none_regression():
    needs = _NeedsRepo()
    needs.insert(
        collection_id="from",
        collected_at="2026-11-01T08:00:00-03:00",
        rows=[
            {
                "material_weg_tratado": "MAT-1",
                "codigo_referencia_weg": "9",
                "quantidade_original_un": "1000",
                "quantidade_mi": "1",
                "data_remessa": "2026-11-15",
                "sb1_resolution": {"status": "pending"},
            }
        ],
    )
    needs.insert(
        collection_id="to",
        collected_at="2026-11-05T08:00:00-03:00",
        rows=[
            {
                "material_weg_tratado": "MAT-1",
                "codigo_referencia_weg": "9",
                "quantidade_original_un": "700",
                "quantidade_mi": "0.7",
                "data_remessa": "2026-11-15",
                "sb1_resolution": {"status": "pending"},
            }
        ],
    )
    service = MyWegNeedsCompareService(needs, gateway=object(), invoice_repository=_InvoiceRepo())
    result = service.compare_products(
        _user(),
        from_batch_id="from",
        to_batch_id="to",
        changes_only=False,
        invoice_mode="none",
    )
    assert result["invoiceMode"] == "none"
    assert "portalInvoices" not in result
    assert set(result["totals"]) == {
        "previousQuantityUn",
        "currentQuantityUn",
        "deltaQuantityUn",
    }
    assert "invoiceMatchStatus" not in result["items"][0]


def test_compare_products_invoice_mode_portal_complete(monkeypatch):
    needs = _NeedsRepo()
    needs.insert(
        collection_id="from",
        collected_at="2026-11-01T08:00:00-03:00",
        rows=[
            {
                "material_weg_tratado": "MAT-1",
                "codigo_referencia_weg": "9",
                "quantidade_original_un": "1000",
                "quantidade_mi": "1",
                "data_remessa": "2026-11-15",
                "sb1_resolution": {"status": "pending"},
            }
        ],
    )
    needs.insert(
        collection_id="to",
        collected_at="2026-11-03T08:00:00-03:00",
        rows=[
            {
                "material_weg_tratado": "MAT-1",
                "codigo_referencia_weg": "9",
                "quantidade_original_un": "700",
                "quantidade_mi": "0.7",
                "data_remessa": "2026-11-15",
                "sb1_resolution": {"status": "pending"},
            }
        ],
    )
    invoices = _InvoiceRepo()
    # Janela [01, 02]
    for day, oid, qty in [
        ("2026-11-01", "o1", "0"),
        ("2026-11-02", "o2", "200"),
    ]:
        status = "empty_signaled_by_sap" if qty == "0" else "with_records"
        invoices.observations.append(
            {
                "id": oid,
                "document_date": day,
                "semantic_sha256": (oid * 8)[:64],
                "payload_sha256": (oid[::-1] * 8)[:64],
                "collection_id": f"col-{oid}",
                "observation_status": status,
                "source_prepared_at": f"{day}T12:00:00+00:00",
            }
        )
        if status == "with_records":
            invoices.items[oid] = [
                {
                    "material_weg": "MAT-1",
                    "materialWeg": "MAT-1",
                    "quantity_un": qty,
                    "quantityUn": qty,
                    "unit_comparability": "comparable",
                    "unitComparability": "comparable",
                }
            ]

    service = MyWegNeedsCompareService(
        needs, gateway=object(), invoice_repository=invoices
    )
    result = service.compare_products(
        _user(),
        from_batch_id="from",
        to_batch_id="to",
        changes_only=True,
        invoice_mode="portal",
    )
    assert result["portalInvoices"]["status"] == COVERAGE_COMPLETE
    assert result["totals"]["adjustedPlanningDeltaUn"] == "-100"
    item = result["items"][0]
    assert item["postedQuantityUn"] == "200"
    assert item["adjustedPlanningDeltaUn"] == "-100"

    app = FastAPI()
    app.include_router(myweg_needs_routes.router)
    monkeypatch.setattr(
        myweg_needs_routes, "build_myweg_needs_compare_service", lambda: service
    )
    monkeypatch.setattr(myweg_needs_routes, "resolve_user", lambda request: _user())
    client = TestClient(app)
    response = client.get(
        "/myweg/need-batches/compare/products",
        params={
            "fromBatchId": "from",
            "toBatchId": "to",
            "invoiceMode": "portal",
            "changesOnly": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["invoiceMode"] == "portal"
    assert body["portalInvoices"]["coverage"] == COVERAGE_COMPLETE


def test_missing_fiscal_day_blocks_adjustment():
    needs = _NeedsRepo()
    needs.insert(
        collection_id="from",
        collected_at="2026-11-01T08:00:00-03:00",
        rows=[
            {
                "material_weg_tratado": "MAT-1",
                "quantidade_original_un": "1000",
                "quantidade_mi": "1",
                "data_remessa": "2026-11-15",
                "sb1_resolution": {"status": "pending"},
            }
        ],
    )
    needs.insert(
        collection_id="to",
        collected_at="2026-11-04T08:00:00-03:00",
        rows=[
            {
                "material_weg_tratado": "MAT-1",
                "quantidade_original_un": "700",
                "quantidade_mi": "0.7",
                "data_remessa": "2026-11-15",
                "sb1_resolution": {"status": "pending"},
            }
        ],
    )
    invoices = _InvoiceRepo()
    invoices.observations.append(
        {
            "id": "o1",
            "document_date": "2026-11-01",
            "semantic_sha256": "a" * 64,
            "payload_sha256": "b" * 64,
            "collection_id": "c1",
            "observation_status": "with_records",
            "source_prepared_at": "2026-11-02T00:00:00+00:00",
        }
    )
    invoices.items["o1"] = [
        {
            "material_weg": "MAT-1",
            "quantity_un": "200",
            "unit_comparability": "comparable",
        }
    ]
    service = MyWegNeedsCompareService(
        needs, gateway=object(), invoice_repository=invoices
    )
    result = service.compare_products(
        _user(),
        from_batch_id="from",
        to_batch_id="to",
        changes_only=False,
        invoice_mode="portal",
    )
    assert result["portalInvoices"]["status"] == COVERAGE_PARTIAL
    assert result["totals"]["adjustedPlanningDeltaUn"] is None
    assert result["items"][0]["adjustedPlanningDeltaUn"] is None


def test_non_comparable_unit_raises_in_aggregate():
    with pytest.raises(ValueError, match="non_comparable"):
        aggregate_posted_nf_by_material(
            [
                {
                    "material_weg": "M",
                    "quantity_un": "1",
                    "unit_comparability": "non_comparable",
                }
            ]
        )


def _managerial_base(**overrides):
    row = {
        "productKey": "code:90263746",
        "identityReliable": True,
        "identityConfirmed": True,
        "deltaQuantityUn": "-2450",
        "observedDeltaUn": "-2450",
        "postedQuantityUn": "2450",
        "compatibleReductionUn": "2450",
        "adjustedPlanningDeltaUn": "0",
        "invoiceMatchStatus": "reconciled",
        "remessas": [
            {
                "remessa": "2026-11-06",
                "previousQuantityUn": "998",
                "currentQuantityUn": "0",
                "deltaQuantityUn": "-998",
                "movement": "disappeared",
            },
            {
                "remessa": "2026-11-11",
                "previousQuantityUn": "1750",
                "currentQuantityUn": "298",
                "deltaQuantityUn": "-1452",
                "movement": "decreased",
            },
            {
                "remessa": "2026-11-12",
                "previousQuantityUn": "100",
                "currentQuantityUn": "100",
                "deltaQuantityUn": "0",
                "movement": "unchanged",
            },
        ],
    }
    row.update(overrides)
    return row


def test_managerial_invoiced_case_90263746():
    classified = apply_managerial_classification(
        _managerial_base(), coverage_status=COVERAGE_COMPLETE
    )
    assert classified["managerialStatus"] == MANAGERIAL_INVOICED
    assert classified["residualUnexplainedUn"] == "0"
    assert classified["remessaInvoicingContext"] == "compatible_on_reduced_lines"
    contexts = [
        item.get("managerialRemessaContext") for item in classified["remessas"]
    ]
    assert contexts[0] == "compatible_with_invoicing"
    assert contexts[1] == "compatible_with_invoicing"
    assert contexts[2] is None


def test_managerial_reconciled_without_nf_is_not_invoiced():
    result = classify_managerial_status(
        _managerial_base(
            postedQuantityUn="0",
            compatibleReductionUn="0",
            adjustedPlanningDeltaUn="-2450",
            invoiceMatchStatus="reconciled",
        ),
        coverage_status=COVERAGE_COMPLETE,
    )
    assert result["managerialStatus"] == MANAGERIAL_INVESTIGATE


def test_managerial_partial_and_excess_nf():
    partial = classify_managerial_status(
        _managerial_base(
            postedQuantityUn="1000",
            compatibleReductionUn="1000",
            adjustedPlanningDeltaUn="-1450",
        ),
        coverage_status=COVERAGE_COMPLETE,
    )
    assert partial["managerialStatus"] == MANAGERIAL_PARTIAL
    assert partial["residualUnexplainedUn"] == "1450"

    excess = classify_managerial_status(
        _managerial_base(
            postedQuantityUn="3000",
            compatibleReductionUn="2450",
            adjustedPlanningDeltaUn="550",
        ),
        coverage_status=COVERAGE_COMPLETE,
    )
    assert excess["managerialStatus"] == MANAGERIAL_WITH_DIFFERENCE
    assert excess["fiscalExcessUn"] == "550"
    assert excess["residualUnexplainedUn"] == "0"
    assert excess["managerialStatus"] != MANAGERIAL_INVOICED


def test_managerial_invoicing_with_difference_case_90261791():
    """AC-01/AC-02: NF 1500 cobre redução 1494; excedente 6; remessas compatíveis."""
    remessas = [
        {
            "remessa": "2026-11-06",
            "previousQuantityUn": "452",
            "currentQuantityUn": "0",
            "deltaQuantityUn": "-452",
            "movement": "disappeared",
        },
        {
            "remessa": "2026-11-10",
            "previousQuantityUn": "36",
            "currentQuantityUn": "0",
            "deltaQuantityUn": "-36",
            "movement": "disappeared",
        },
        {
            "remessa": "2026-11-11",
            "previousQuantityUn": "414",
            "currentQuantityUn": "0",
            "deltaQuantityUn": "-414",
            "movement": "disappeared",
        },
        {
            "remessa": "2026-11-12",
            "previousQuantityUn": "246",
            "currentQuantityUn": "0",
            "deltaQuantityUn": "-246",
            "movement": "disappeared",
        },
        {
            "remessa": "2026-11-17",
            "previousQuantityUn": "702",
            "currentQuantityUn": "356",
            "deltaQuantityUn": "-346",
            "movement": "decreased",
        },
    ]
    classified = apply_managerial_classification(
        {
            "productKey": "code:90261791",
            "identityReliable": True,
            "identityConfirmed": True,
            "previousQuantityUn": "4094",
            "currentQuantityUn": "2600",
            "deltaQuantityUn": "-1494",
            "observedDeltaUn": "-1494",
            "postedQuantityUn": "1500",
            "compatibleReductionUn": "1494",
            "adjustedPlanningDeltaUn": "6",
            "invoiceMatchStatus": "reconciled",
            "remessas": remessas,
        },
        coverage_status=COVERAGE_COMPLETE,
    )
    assert classified["managerialStatus"] == MANAGERIAL_WITH_DIFFERENCE
    assert classified["fiscalExcessUn"] == "6"
    assert classified["residualUnexplainedUn"] == "0"
    explanation = classified["managerialExplanation"]
    assert "1500" in explanation and "1494" in explanation and "6" in explanation
    assert classified["remessaInvoicingContext"] == "compatible_on_reduced_lines"
    contexts = [
        item.get("managerialRemessaContext") for item in classified["remessas"]
    ]
    assert contexts == ["compatible_with_invoicing"] * 5


def test_managerial_nf_without_reduction_is_not_invoicing():
    """AC-06: NF positiva sem redução não explica faturamento de queda."""
    result = classify_managerial_status(
        _managerial_base(
            observedDeltaUn="0",
            deltaQuantityUn="0",
            postedQuantityUn="1500",
            compatibleReductionUn="0",
            adjustedPlanningDeltaUn="1500",
        ),
        coverage_status=COVERAGE_COMPLETE,
    )
    assert result["managerialStatus"] == MANAGERIAL_OTHER
    assert result["managerialStatus"] != MANAGERIAL_WITH_DIFFERENCE
    assert result["managerialStatus"] != MANAGERIAL_INVOICED


def test_managerial_pending_and_other_movements():
    pending = classify_managerial_status(
        _managerial_base(invoiceMatchStatus="ambiguous_identity"),
        coverage_status=COVERAGE_COMPLETE,
    )
    assert pending["managerialStatus"] == MANAGERIAL_PENDING

    coverage = classify_managerial_status(
        _managerial_base(), coverage_status=COVERAGE_PARTIAL
    )
    assert coverage["managerialStatus"] == MANAGERIAL_PENDING

    other = classify_managerial_status(
        _managerial_base(
            observedDeltaUn="10",
            deltaQuantityUn="10",
            postedQuantityUn="0",
            compatibleReductionUn="0",
            adjustedPlanningDeltaUn="10",
        ),
        coverage_status=COVERAGE_COMPLETE,
    )
    assert other["managerialStatus"] == MANAGERIAL_OTHER


def test_managerial_remessa_skipped_when_increases_present():
    classified = apply_managerial_classification(
        _managerial_base(
            remessas=[
                {
                    "remessa": "2026-11-06",
                    "previousQuantityUn": "2000",
                    "currentQuantityUn": "0",
                    "deltaQuantityUn": "-2000",
                    "movement": "decreased",
                },
                {
                    "remessa": "2026-11-11",
                    "previousQuantityUn": "450",
                    "currentQuantityUn": "0",
                    "deltaQuantityUn": "-450",
                    "movement": "decreased",
                },
                {
                    "remessa": "2026-11-20",
                    "previousQuantityUn": "0",
                    "currentQuantityUn": "100",
                    "deltaQuantityUn": "100",
                    "movement": "appeared",
                },
            ]
        ),
        coverage_status=COVERAGE_COMPLETE,
    )
    assert classified["managerialStatus"] == MANAGERIAL_INVOICED
    assert classified["remessaInvoicingContext"] == "product_only"
    assert all(
        item.get("managerialRemessaContext") is None
        for item in classified["remessas"]
    )
