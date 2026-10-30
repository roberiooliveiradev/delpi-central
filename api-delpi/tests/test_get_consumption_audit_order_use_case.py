"""Tests: consumption-audit use case composition and conservative classification.

The fixtures replicate the investigated snapshot of OP 24884201006 (branch 01,
product 50226108) from GLPI #1353/A1:

- op-01: cabo 10010030 — derived commitment equals SD3 consumption (80.75 MT);
  the RE0 transfer of 0.64 MT must NOT inflate consumption to 81.39.
- op-02: terminal 10080329 — commitment fully open, no execution evidence
  besides an SH8 allocation row (allocation != execution) → execution pending.
- MOD216 (B1_TIPO=MO, HR) is labor → excluded from material consumption.
- SH6 proves execution on op-01 (0.125 produced vs C2_QUJE=0 → warning);
  C2_QUJE is exposed as stock-receipt basis, never as appointment output.
- Mother OP 24884201002 linked via D4_OPORIG.
"""

from __future__ import annotations

import pytest

from app.application.dto.supplies.get_consumption_audit_order_request import (
    GetConsumptionAuditOrderRequest,
)
from app.application.use_cases.supplies.get_consumption_audit_order_use_case import (
    GetConsumptionAuditOrderUseCase,
)


OP = "24884201006"
BRANCH = "01"


def _order_row(**overrides):
    row = {
        "branch": BRANCH,
        "production_order": OP,
        "order_number": "248842",
        "order_item": "01",
        "order_sequence": "006",
        "product_code": "50226108",
        "product_description": "PRODUTO INTERMEDIARIO",
        "product_type": "PI",
        "unit_of_measure": "MI",
        "planned_quantity": 0.125,
        "produced_quantity": 0.0,
        "status": "N",
        "priority": "500",
        "order_type": "F",
        "warehouse": "99",
        "emission_date": "2026-10-20",
        "planned_start_date": "2026-10-29",
        "due_date": "2026-10-29",
        "finished_at": None,
    }
    row.update(overrides)
    return row


def _sibling(sequence: str, *, produced: float = 0.0):
    return _order_row(
        production_order=f"24884201{sequence}",
        order_sequence=sequence,
        produced_quantity=produced,
    )


def _commitment(operation, component, unit, original, open_, *,
                component_type="MP", origin_order=None):
    return {
        "operation": operation,
        "component_code": component,
        "component_description": None,
        "unit_of_measure": unit,
        "component_type": component_type,
        "origin_order": origin_order,
        "original_quantity": original,
        "open_quantity": open_,
        "derived_consumed_quantity": original - open_,
        "commitment_lines": 1,
    }


def _movement(doc, component, cf, tm, quantity, unit, *, reversed_flag=""):
    return {
        "document": doc,
        "component_code": component,
        "cf": cf,
        "tm": tm,
        "quantity": quantity,
        "unit_of_measure": unit,
        "warehouse": "99",
        "reversed_flag": reversed_flag,
        "issue_date": "2026-10-29",
    }


def _bom(component, desc, unit, qty_per_unit, *, component_type="MP"):
    return {
        "branch": "",
        "component_code": component,
        "component_description": desc,
        "component_type": component_type,
        "unit_of_measure": unit,
        "quantity_per_unit": qty_per_unit,
        "valid_from": "2026-10-20",
        "valid_to": "2049-12-31",
    }


def _source(**overrides):
    data = {
        "order": _order_row(),
        "family_orders": [
            _sibling("001"),
            _sibling("002"),
            _sibling("003", produced=0.125),
            _sibling("004"),
            _sibling("005"),
        ],
        "bom_components": [
            _bom("10010030", "CABO", "MT", 646.0),
            _bom("10080329", "TERMINAL", "PC", 2000.0),
        ],
        "commitments": [
            _commitment("01", "10010030", "MT", 80.75, 0.0),
            _commitment("02", "10080329", "PC", 250.0, 250.0),
        ],
        "movements": [
            _movement("220039839", "10010030", "RE0", "999", 0.64, "MT"),
            _movement("220039840", "MOD216", "RE1", "999", 0.233, "HR"),
            _movement("220039841", "10010030", "RE2", "999", 80.75, "MT"),
        ],
        "appointments": [
            {
                "operation": "01",
                "appointment_type": "P",
                "product_code": "50226108",
                "reported_quantity": 0.125,
                "lost_quantity": 0.0,
                "appointment_id": "UDCGH1",
                "resource": "CT-23",
                "reported_at": "2026-10-29",
                "started_on": "2026-10-29",
                "ended_on": "2026-10-29",
                "start_time": "05:13",
                "end_time": "05:27",
            }
        ],
        "operation_events": [
            {
                "operation": "01",
                "status": "2",
                "transaction_type": "1",
                "appointment_ref": "0150226108       01UDCGH1",
                "resource": "",
                "sequence": "000001",
                "started_on": "2026-10-29",
                "start_time": "05:13:23",
                "ended_on": "2026-10-29",
                "end_time": "05:27:59",
            }
        ],
        "allocations": [
            {
                "operation": "02",
                "work_center": "CT-35",
                "resource": "CT-35",
                "status": "",
                "quantity": 0.125,
                "scheduled_start": "2026-10-30",
                "scheduled_end": "2026-10-30",
                "scheduled_start_time": "07:56",
                "scheduled_end_time": "08:50",
            }
        ],
        "routing": [
            {"branch": "", "operation": "01", "work_center": "CT-23", "resource": "CT-23"},
            {"branch": "", "operation": "02", "work_center": "CT-35", "resource": "CT-35"},
        ],
        "product_metadata": {
            "10010030": {"description": "CABO", "product_type": "MP", "unit_of_measure": "MT"},
            "10080329": {"description": "TERMINAL", "product_type": "MP", "unit_of_measure": "PC"},
            "MOD216": {"description": "MONTAGEM", "product_type": "MO", "unit_of_measure": "HR"},
        },
        "parent_consumers": [
            {"production_order": "24884201002", "component_code": "50226108"}
        ],
    }
    data.update(overrides)
    return data


class _Repo:
    """Port fake — devolve o snapshot investigado, registra as chamadas."""

    def __init__(self, source=None):
        self._s = source or _source()
        self.calls = []

    def fetch_order(self, *, production_order, branch):
        self.calls.append("fetch_order")
        return self._s["order"]

    def fetch_family_orders(self, *, order_number, branch, exclude_production_order):
        return [
            r for r in self._s["family_orders"]
            if r["production_order"] != exclude_production_order
        ]

    def fetch_commitments(self, *, production_order, branch):
        return self._s["commitments"]

    def fetch_movements(self, *, production_order, branch):
        return self._s["movements"]

    def fetch_appointments(self, *, production_order, branch):
        return self._s["appointments"]

    def fetch_operation_events(self, *, production_order, branch):
        return self._s["operation_events"]

    def fetch_allocations(self, *, production_order, branch):
        return self._s["allocations"]

    def fetch_routing(self, *, product_code, branch):
        return self._s["routing"]

    def fetch_bom_components(self, *, product_code, branch, reference_date):
        assert reference_date == "20261020"  # emission_date sem hífens
        return self._s["bom_components"]

    def fetch_product_metadata(self, *, codes):
        return self._s["product_metadata"]

    def fetch_parent_consumers(self, *, production_order, branch):
        return self._s["parent_consumers"]


def _run(source=None):
    repo = _Repo(source)
    use_case = GetConsumptionAuditOrderUseCase(repo)
    request = GetConsumptionAuditOrderRequest(production_order=OP, branch=BRANCH)
    return use_case.execute(request), repo


# ---------------------------------------------------------------- happy path


def test_order_projection_and_key_decomposition():
    result, repo = _run()
    assert "fetch_order" in repo.calls
    assert result["branch"] == BRANCH
    assert result["production_order"] == OP
    order = result["order"]
    assert order["order_number"] == "248842"
    assert order["order_item"] == "01"
    assert order["order_sequence"] == "006"
    assert order["product_code"] == "50226108"
    assert order["product_type"] == "PI"
    assert order["planned_quantity"] == 0.125
    assert order["produced_quantity"] == 0.0
    assert order["produced_quantity_basis"] == "stock_receipt"
    assert result["metadata"]["generated_at_source"] == "api-delpi"
    assert result["metadata"]["tolerance_policy"]["absolute"] is None
    assert result["metadata"]["tolerance_policy"]["percent"] is None


def test_operations_reflect_routing_with_distinct_evidence_channels():
    result, _ = _run()
    ops = {o["operation"]: o for o in result["operations"]}
    assert set(ops) == {"01", "02"}

    op01 = ops["01"]
    assert op01["work_center"] == "CT-23"
    ev = op01["execution_evidence"]
    assert ev["execution_state"] == "evidenced"
    assert len(ev["sh6_appointments"]) == 1
    assert len(ev["hza_records"]) == 1
    assert ev["sh8_allocation"]["row_present"] is False
    sh6 = ev["sh6_appointments"][0]
    assert sh6["appointment_id"] == "UDCGH1"
    assert sh6["linked_hza"] is True
    assert sh6["channel"] == "collector"
    assert sh6["resource"] == "CT-23"

    op02 = ops["02"]
    assert op02["work_center"] == "CT-35"
    ev2 = op02["execution_evidence"]
    assert ev2["execution_state"] == "pending"
    assert ev2["sh6_appointments"] == []
    assert ev2["hza_records"] == []
    assert ev2["sh8_allocation"]["row_present"] is True
    assert ev2["sh8_allocation"]["quantity"] == 0.125


def test_component_reconciliation_op01_cabo():
    result, _ = _run()
    op01 = next(o for o in result["operations"] if o["operation"] == "01")
    comp = op01["components"][0]
    assert comp["component_code"] == "10010030"
    assert comp["bom"]["theoretical_quantity"] == pytest.approx(80.75)
    assert comp["bom"]["structure_as_of"] == "order_emission_date"
    assert comp["bom"]["completeness"] == "complete"
    assert comp["commitment"]["original_quantity"] == 80.75
    assert comp["commitment"]["open_quantity"] == 0.0
    assert comp["commitment"]["derived_consumed_quantity"] == 80.75
    assert comp["movements"]["eligible_consumption_quantity"] == 80.75
    assert comp["discrepancy"]["value"] == 0.0
    assert comp["discrepancy"]["within_tolerance"] is None
    assert comp["classification"] == "reconciled"


def test_transfer_and_labor_excluded_from_consumption():
    result, _ = _run()
    op01 = next(o for o in result["operations"] if o["operation"] == "01")
    comp = op01["components"][0]

    excluded = comp["movements"]["excluded"]
    assert [m["document"] for m in excluded] == ["220039839"]
    assert excluded[0]["kind"] == "warehouse_transfer"
    assert excluded[0]["reason"] == "not_raw_material_consumption"
    assert excluded[0]["quantity"] == 0.64
    assert excluded[0]["cf"] == "RE0"
    assert "ambiguous_cf_semantics" in comp["quality_flags"]

    eligible = comp["movements"]["classified"]
    assert [m["document"] for m in eligible] == ["220039841"]

    # MOD216 (MO, HR) é mão de obra — movimento sem empenho correspondente.
    unmatched = result["unmatched_movements"]
    assert len(unmatched) == 1
    assert unmatched[0]["component_code"] == "MOD216"
    assert unmatched[0]["binding"] == "no_matching_commitment"
    assert unmatched[0]["reason"] == "labor_not_material"
    assert unmatched[0]["component_type"] == "MO"
    assert unmatched[0]["quantity"] == 0.233


def test_op02_pending_commitment_no_consumption_claim():
    result, _ = _run()
    op02 = next(o for o in result["operations"] if o["operation"] == "02")
    comp = op02["components"][0]
    assert comp["component_code"] == "10080329"
    assert comp["commitment"]["derived_consumed_quantity"] == 0.0
    assert comp["movements"]["eligible_consumption_quantity"] == 0.0
    assert comp["discrepancy"]["value"] == 0.0
    # Sem evidência de execução, diferença teórico↔derivado não é acusação.
    assert comp["classification"] == "requires_investigation"


def test_quality_partial_and_warnings():
    result, _ = _run()
    quality = result["quality"]
    assert quality["status"] == "partial"
    warnings = set(quality["warnings"])
    assert "sh6_vs_sc2_quantity_mismatch" in warnings
    assert "re0_tm999_ambiguity" in warnings
    assert "movements_without_commitment" in warnings
    assert set(quality["unresolved_semantics"]) == {
        "automatic_issue_causality",
        "re0_tm999_transfer_meaning",
        "sh8_row_removal_semantics",
    }


def test_related_orders_family_and_d4_oporig_parent():
    result, _ = _run()
    by_rel = {}
    for r in result["related_orders"]:
        by_rel.setdefault(r["production_order"], set()).add(r["relationship"])
    assert "same_order_number" in by_rel["24884201002"]
    assert "parent_commitment_via_d4_oporig" in by_rel["24884201002"]
    assert "same_order_number" in by_rel["24884201001"]
    parent = next(
        r for r in result["related_orders"]
        if r["relationship"] == "parent_commitment_via_d4_oporig"
    )
    assert parent["component_code"] == "50226108"
    assert parent["confidence"] == "proven"


def test_origin_order_commitment_exposes_producing_op():
    source = _source(
        commitments=[
            _commitment("01", "10010030", "MT", 80.75, 0.0),
            _commitment("02", "50226108", "MI", 0.125, 0.125,
                        component_type="PI", origin_order="24884201005"),
        ]
    )
    result, _ = _run(source)
    rels = [
        r for r in result["related_orders"]
        if r["relationship"] == "producing_order_for_component"
    ]
    assert rels[0]["production_order"] == "24884201005"
    assert rels[0]["component_code"] == "50226108"


# ------------------------------------------------------------- siblings


def test_sibling_op03_produced_quantity_is_stock_receipt_not_appointment():
    """OP irmã 003 com C2_QUJE=0.125: QUJE é recebimento de estoque
    (sibling_correlation), nunca saída de operação intermediária."""
    source = _source(order=_order_row(
        production_order="24884201003",
        order_sequence="003",
        produced_quantity=0.125,
    ))
    result, _ = _run(source)
    assert result["order"]["produced_quantity"] == 0.125
    assert result["order"]["produced_quantity_basis"] == "stock_receipt"


def test_sh6_without_hza_keeps_execution_evidenced():
    """OP-04 provou SH6 sem HZA: evidência válida, canal marcado unknown."""
    source = _source(
        operation_events=[],
        appointments=[{
            "operation": "01", "appointment_type": "P",
            "product_code": "50226108", "reported_quantity": 0.05,
            "lost_quantity": 0.0, "appointment_id": "UDCAWQ",
            "resource": "CT-23", "reported_at": "2026-10-28",
            "started_on": "2026-10-28", "ended_on": "2026-10-28",
            "start_time": "10:00", "end_time": "10:30",
        }],
    )
    result, _ = _run(source)
    op01 = result["operations"][0]
    ev = op01["execution_evidence"]
    assert ev["execution_state"] == "evidenced"
    assert ev["hza_records"] == []
    assert ev["sh6_appointments"][0]["channel"] == "unknown"
    assert ev["sh6_appointments"][0]["linked_hza"] is False


# ------------------------------------------------------------- classification


def test_estorno_pairs_netted_out():
    """Linhas espelhadas marcadas D3_ESTORNO='S' são excluídas como reversed."""
    source = _source(movements=[
        _movement("220039841", "10010030", "RE2", "999", 80.75, "MT"),
        _movement("220039841", "10010030", "DE2", "999", 80.75, "MT", reversed_flag="S"),
        _movement("220039841", "10010030", "RE2", "999", 80.75, "MT", reversed_flag="S"),
    ])
    result, _ = _run(source)
    comp = result["operations"][0]["components"][0]
    eligible = [(m["document"], m["cf"]) for m in comp["movements"]["classified"]]
    excluded = comp["movements"]["excluded"]
    assert eligible == [("220039841", "RE2")]
    assert [m["reason"] for m in excluded] == ["reversed", "reversed"]
    assert all(m["reversed"] for m in excluded)
    assert comp["movements"]["eligible_consumption_quantity"] == 80.75
    assert comp["classification"] == "reconciled"


def test_unclassified_movement_excluded_with_reason():
    source = _source(movements=[
        _movement("1", "10010030", "RE9", "101", 5.0, "MT"),
    ])
    result, _ = _run(source)
    comp = result["operations"][0]["components"][0]
    assert comp["movements"]["classified"] == []
    excluded = comp["movements"]["excluded"][0]
    assert excluded["kind"] == "unclassified"
    assert excluded["reason"] == "not_raw_material_consumption"


def test_same_document_multiple_lines_bound_by_line_semantics():
    """Documento nunca é chave: cada linha do mesmo doc casa por
    (operação, componente) — nada é duplicado nem misturado."""
    source = _source(movements=[
        _movement("220039841", "10010030", "RE2", "999", 80.75, "MT"),
        _movement("220039841", "MOD216", "RE1", "999", 0.5, "HR"),
    ])
    result, _ = _run(source)
    comp = result["operations"][0]["components"][0]
    assert [m["document"] for m in comp["movements"]["classified"]] == ["220039841"]
    assert comp["movements"]["eligible_consumption_quantity"] == 80.75
    # Linha MOD216 do mesmo documento vai para unmatched, não para o cabo.
    assert result["unmatched_movements"][0]["document"] == "220039841"
    assert result["unmatched_movements"][0]["component_code"] == "MOD216"


def test_non_comparable_units_make_difference_null():
    """UM divergente não gera diferença aritmética espúria."""
    source = _source(movements=[
        _movement("X1", "10010030", "RE2", "999", 10.0, "KG"),
    ])
    result, _ = _run(source)
    comp = result["operations"][0]["components"][0]
    assert comp["discrepancy"]["value"] is None
    assert "uom_mismatch" in comp["quality_flags"]
    assert comp["classification"] == "requires_investigation"
    assert "movement_uom_differs_from_commitment" in result["quality"]["warnings"]


# ------------------------------------------------------------- incomplete data


def test_missing_structure_returns_partial_not_zero():
    source = _source(bom_components=[])
    result, _ = _run(source)
    op01 = next(o for o in result["operations"] if o["operation"] == "01")
    comp = op01["components"][0]
    assert comp["component_code"] == "10010030"
    assert comp["bom"]["theoretical_quantity"] is None
    assert comp["bom"]["completeness"] == "missing"
    assert result["quality"]["status"] == "partial"
    assert "commitment_without_bom" in result["quality"]["warnings"]


def test_no_evidence_at_all_is_unknown_execution():
    source = _source(appointments=[], operation_events=[], allocations=[], routing=[])
    result, _ = _run(source)
    ops = {o["operation"]: o for o in result["operations"]}
    assert ops["01"]["execution_evidence"]["execution_state"] == "unknown"
    assert ops["01"]["work_center"] is None
    assert ops["01"]["components"][0]["classification"] == "requires_investigation"


def test_no_operations_at_all_is_inconclusive():
    source = _source(
        appointments=[], operation_events=[], allocations=[],
        routing=[], commitments=[], movements=[],
    )
    result, _ = _run(source)
    assert result["operations"] == []
    assert result["quality"]["status"] == "inconclusive"
    assert "no_operations_found" in result["quality"]["warnings"]


# ------------------------------------------------------------- validation


def test_production_order_must_be_11_position_key():
    repo = _Repo()
    use_case = GetConsumptionAuditOrderUseCase(repo)
    for bad in ("2488420100", "248842010061", "24884201*06", ""):
        with pytest.raises(ValueError):
            use_case.execute(
                GetConsumptionAuditOrderRequest(production_order=bad, branch=BRANCH)
            )
    assert repo.calls == []


def test_branch_validation_in_request_dto():
    for bad in ("00", "99", "", None):
        with pytest.raises(ValueError):
            GetConsumptionAuditOrderRequest(production_order=OP, branch=bad)
    dto = GetConsumptionAuditOrderRequest(production_order=OP, branch=" 02 ")
    assert dto.branch == "02"


def test_production_order_normalized_uppercase():
    dto = GetConsumptionAuditOrderRequest(production_order=" 24884201006 ", branch=BRANCH)
    assert dto.production_order == OP


def test_order_not_found_returns_none():
    source = _source(order=None)
    result, _ = _run(source)
    assert result is None
