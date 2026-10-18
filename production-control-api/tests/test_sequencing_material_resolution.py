"""Resolução de material de sequenciamento — Regras de Sequenciamento E2.

Domínio puro + serviço de aplicação em lote. O resolvedor NUNCA escolhe entre
candidatos, nunca reordena e nunca toca fila/snapshot.
"""

from __future__ import annotations

from typing import Any

import pytest

from production_control_app.application.services.sequencing_material_resolver_service import (
    SequencingMaterialResolverService,
)
from production_control_app.domain.services.sequencing_material_resolution import (
    IDENTITY_DIRECT,
    IDENTITY_FALLBACK_OP,
    RESOLUTION_AMBIGUOUS,
    RESOLUTION_INCOMPLETE,
    RESOLUTION_MISSING,
    RESOLUTION_RESOLVED,
    RESOLUTION_SOURCE_UNAVAILABLE,
    is_fully_zeroed,
    material_criterion_params,
    resolve_operation_material,
    resolve_operations_materials,
)
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.sequencing_profile import validate_criteria

PILOT_GROUPS = [
    "1037", "1038", "1053", "1007", "1042", "1047", "1040", "1041",
    "1055", "1049", "1002", "1001", "1005", "1051", "1044", "1036",
]


def _params(**overrides: Any) -> dict[str, Any]:
    params = {
        "material_type": "MP",
        "eligible_product_groups": list(PILOT_GROUPS),
        "identity_source": "operation_then_order",
        "ignore_zeroed_allocations": True,
        "on_missing": "flag",
        "on_ambiguous": "flag",
    }
    params.update(overrides)
    return params


def _criteria(**overrides: Any) -> list[dict[str, Any]]:
    return validate_criteria(
        [
            {"type": "pa_due_date"},
            {"type": "material_code", "params": _params(**overrides)},
        ]
    )


def _operation(
    order: str = "123456001",
    operation: str = "01",
    work_center: str = "CT-02B",
    branch: str = "02",
) -> dict[str, str]:
    return {
        "branch": branch,
        "work_center": work_center,
        "production_order": order,
        "operation_code": operation,
    }


def _material(
    code: str,
    *,
    order: str = "123456001",
    operation: str = "01",
    product_type: str = "MP",
    product_group: str = "1007",
    original_qty: float = 10.0,
    open_qty: float = 4.0,
    zeroed: int = 0,
    count: int = 1,
) -> dict[str, Any]:
    return {
        "production_order": order,
        "operation": operation,
        "product_code": code,
        "product_type": product_type,
        "product_group": product_group,
        "original_qty": original_qty,
        "open_qty": open_qty,
        "consumed_qty": max(original_qty - open_qty, 0.0),
        "zeroed_commitment_count": zeroed,
        "commitment_count": count,
    }


# ---------------------------------------------------------------------------
# Domínio puro
# ---------------------------------------------------------------------------


def test_resolves_single_material_directly_at_operation() -> None:
    result = resolve_operation_material(
        operation=_operation(),
        order_items=[_material("10070371")],
        params=_params(),
    )
    assert result["status"] == RESOLUTION_RESOLVED
    assert result["product_code"] == "10070371"
    assert result["product_group"] == "1007"
    assert result["source"] == IDENTITY_DIRECT
    assert result["work_center"] == "CT-02B"
    assert result["branch"] == "02"


def test_falls_back_to_order_when_operation_has_no_material() -> None:
    items = [_material("10070371", operation="02")]
    result = resolve_operation_material(
        operation=_operation(operation="01"),
        order_items=items,
        params=_params(),
    )
    assert result["status"] == RESOLUTION_RESOLVED
    assert result["product_code"] == "10070371"
    assert result["source"] == IDENTITY_FALLBACK_OP


def test_two_records_same_code_resolve_to_one_material() -> None:
    items = [
        _material("10070371", count=1),
        _material("10070371", count=1, open_qty=2.0),
    ]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_RESOLVED
    assert result["product_code"] == "10070371"


def test_two_distinct_codes_at_operation_flag_ambiguous() -> None:
    items = [_material("10070371"), _material("10070372")]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_AMBIGUOUS
    assert result["product_code"] is None
    assert result["candidate_codes"] == ["10070371", "10070372"]


def test_two_distinct_codes_only_at_order_flag_ambiguous() -> None:
    items = [
        _material("10070371", operation="02"),
        _material("10070372", operation="03"),
    ]
    result = resolve_operation_material(
        operation=_operation(operation="01"), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_AMBIGUOUS
    assert result["candidate_codes"] == ["10070371", "10070372"]


def test_operation_without_eligible_material_is_missing() -> None:
    result = resolve_operation_material(
        operation=_operation(),
        order_items=[_material("20000001", operation="05")],
        params=_params(),
    )
    # OP inteira tem só um código elegível → fallback resolve.
    assert result["status"] == RESOLUTION_RESOLVED
    assert result["source"] == IDENTITY_FALLBACK_OP

    result = resolve_operation_material(
        operation=_operation(), order_items=[], params=_params()
    )
    assert result["status"] == RESOLUTION_MISSING


def test_non_mp_materials_are_excluded() -> None:
    items = [
        _material("30000001", product_type="PA"),
        _material("40000001", product_type="PI"),
    ]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_MISSING


def test_mp_outside_configured_groups_is_excluded() -> None:
    items = [_material("10070371", product_group="9999")]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_MISSING


def test_different_group_configuration_changes_eligibility() -> None:
    items = [_material("10070371", product_group="9999")]
    result = resolve_operation_material(
        operation=_operation(),
        order_items=items,
        params=_params(eligible_product_groups=["9999"]),
    )
    assert result["status"] == RESOLUTION_RESOLVED


def test_open_qty_zero_with_positive_original_stays_eligible() -> None:
    """open_qty=0 não é empenho zerado: o material existiu e foi empenhado."""
    items = [_material("10070371", original_qty=10.0, open_qty=0.0, zeroed=0, count=1)]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_RESOLVED


def test_fully_zeroed_record_is_ignored_when_policy_says_so() -> None:
    items = [_material("10071279", original_qty=0.0, open_qty=0.0, zeroed=1, count=1)]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_MISSING

    result = resolve_operation_material(
        operation=_operation(),
        order_items=items,
        params=_params(ignore_zeroed_allocations=False),
    )
    assert result["status"] == RESOLUTION_RESOLVED


def test_netting_zero_aggregate_is_not_fully_zeroed() -> None:
    """Soma zero por positivo+negativo não prova registros zerados."""
    item = _material(
        "10070371", original_qty=0.0, open_qty=0.0, zeroed=0, count=2
    )
    assert is_fully_zeroed(item) is False

    zeroed = _material(
        "10070371", original_qty=0.0, open_qty=0.0, zeroed=2, count=2
    )
    assert is_fully_zeroed(zeroed) is True

    # Sem o campo novo (producer antigo): conservador, mantém elegível.
    legacy = dict(zeroed)
    del legacy["zeroed_commitment_count"]
    assert is_fully_zeroed(legacy) is False


def test_op_11173301001_reference_case() -> None:
    """Caso real do piloto: cabo zerado na operação + cabo válido na OP."""
    items = [
        _material(
            "10071279", order="11173301001", operation="01",
            original_qty=0.0, open_qty=0.0, zeroed=1, count=1,
        ),
        _material(
            "10070371", order="11173301001", operation="02",
            original_qty=50.0, open_qty=50.0,
        ),
    ]
    result = resolve_operation_material(
        operation=_operation(order="11173301001", operation="01"),
        order_items=items,
        params=_params(),
    )
    assert result["status"] == RESOLUTION_RESOLVED
    assert result["product_code"] == "10070371"
    assert result["source"] == IDENTITY_FALLBACK_OP


def test_product_code_preserves_leading_zeros() -> None:
    items = [_material("0010070371")]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["product_code"] == "0010070371"


def test_same_order_two_operations_with_distinct_cables() -> None:
    items = [
        _material("10070371", operation="01"),
        _material("10070372", operation="02"),
    ]
    first = resolve_operation_material(
        operation=_operation(operation="01"), order_items=items, params=_params()
    )
    second = resolve_operation_material(
        operation=_operation(operation="02"), order_items=items, params=_params()
    )
    assert first["product_code"] == "10070371"
    assert first["source"] == IDENTITY_DIRECT
    assert second["product_code"] == "10070372"
    assert second["source"] == IDENTITY_DIRECT


def test_mixed_filled_and_empty_operations_in_same_order() -> None:
    items = [_material("10070371", operation="01")]
    filled = resolve_operation_material(
        operation=_operation(operation="01"), order_items=items, params=_params()
    )
    empty = resolve_operation_material(
        operation=_operation(operation="02"), order_items=items, params=_params()
    )
    assert filled["source"] == IDENTITY_DIRECT
    assert empty["source"] == IDENTITY_FALLBACK_OP
    assert empty["product_code"] == "10070371"


def test_transferred_operation_keeps_current_work_center_identity() -> None:
    result = resolve_operation_material(
        operation=_operation(work_center="CT-05A"),
        order_items=[_material("10070371")],
        params=_params(),
    )
    assert result["work_center"] == "CT-05A"
    assert result["status"] == RESOLUTION_RESOLVED


def test_operation_then_order_is_the_only_fallback_source() -> None:
    params = _params(identity_source="operation_then_order")
    assert resolve_operation_material(
        operation=_operation(), order_items=[], params=params
    )["status"] == RESOLUTION_MISSING

    # Fonte desconhecida não cai para a OP: nada de fallback implícito.
    params = _params(identity_source="order_only")
    assert resolve_operation_material(
        operation=_operation(),
        order_items=[_material("10070371", operation="02")],
        params=params,
    )["status"] == RESOLUTION_MISSING


def test_material_criterion_params_extraction() -> None:
    params = material_criterion_params(_criteria())
    assert params is not None
    assert params["material_type"] == "MP"
    assert material_criterion_params([{"type": "pa_due_date", "params": {}}]) is None
    assert material_criterion_params(None) is None
    assert material_criterion_params("x") is None


def test_resolve_batch_keeps_operation_order_and_identity() -> None:
    operations = [
        _operation(order="111111001", operation="01"),
        _operation(order="222222001", operation="01"),
        _operation(order="111111001", operation="02", work_center="CT-05A"),
    ]
    items_by_order = {
        "111111001": [
            _material("10070371", order="111111001", operation="01"),
            _material("10070372", order="111111001", operation="02"),
        ],
        "222222001": [_material("10070373", order="222222001", operation="01")],
    }
    results = resolve_operations_materials(
        operations=operations, items_by_order=items_by_order, params=_params()
    )
    assert [r["product_code"] for r in results] == [
        "10070371", "10070373", "10070372",
    ]
    assert results[2]["work_center"] == "CT-05A"


def test_unavailable_and_incomplete_never_become_missing() -> None:
    operations = [
        _operation(order="111111001"),
        _operation(order="222222001"),
        _operation(order="333333001"),
    ]
    results = resolve_operations_materials(
        operations=operations,
        items_by_order={},
        params=_params(),
        unavailable_orders={"111111001"},
        incomplete_orders={"222222001"},
    )
    assert results[0]["status"] == RESOLUTION_SOURCE_UNAVAILABLE
    assert results[1]["status"] == RESOLUTION_INCOMPLETE
    assert results[2]["status"] == RESOLUTION_MISSING


# ---------------------------------------------------------------------------
# Serviço de aplicação (lote, chunking, falhas)
# ---------------------------------------------------------------------------


class _FakeGateway:
    def __init__(self, payloads: dict[str, Any] | None = None, fail_on: set[str] = ()):  # noqa: E501
        self.payloads = payloads or {}
        self.fail_on = set(fail_on)
        self.calls: list[list[str]] = []

    def fetch_operation_materials_batch(
        self, *, branch: str, production_orders: Any
    ) -> dict[str, Any]:
        chunk = list(production_orders)
        self.calls.append(chunk)
        items: list[dict[str, Any]] = []
        for order in chunk:
            if order in self.fail_on:
                raise DelpiGatewayError("indisponível")
            entry = self.payloads.get(order)
            if entry == "malformed":
                return {"data": {}}
            items.extend(entry or [])
        return {
            "data": {
                "branch": branch,
                "production_orders": chunk,
                "items": items,
            }
        }


def test_service_resolves_batch_and_dedupes_orders() -> None:
    gateway = _FakeGateway(
        payloads={
            "111111001": [_material("10070371", order="111111001")],
            "222222001": [_material("10070372", order="222222001")],
        }
    )
    service = SequencingMaterialResolverService(gateway)
    operations = [
        _operation(order="111111001", operation="01"),
        _operation(order="111111001", operation="02"),  # mesma OP repetida
        _operation(order="222222001", operation="01"),
    ]
    result = service.resolve_materials(
        branch="02",
        work_center="CT-02B",
        operations=operations,
        criteria=_criteria(),
    )
    assert result["material_criterion"] is True
    assert gateway.calls == [["111111001", "222222001"]]
    assert result["summary"]["resolved"] == 3
    assert result["items"][1]["source"] == IDENTITY_FALLBACK_OP
    # Entrada não é mutada.
    assert operations[0] == _operation(order="111111001", operation="01")


def test_service_profile_without_material_criterion_is_explicit() -> None:
    service = SequencingMaterialResolverService(_FakeGateway())
    result = service.resolve_materials(
        branch="02",
        work_center="CT-02B",
        operations=[_operation()],
        criteria=validate_criteria([{"type": "pa_due_date"}]),
    )
    assert result["material_criterion"] is False
    assert result["items"] == []
    assert result["summary"]["total"] == 1


def test_service_chunks_over_batch_limit() -> None:
    gateway = _FakeGateway()
    service = SequencingMaterialResolverService(gateway)
    operations = [
        _operation(order=f"{index:09d}") for index in range(350)
    ]
    result = service.resolve_materials(
        branch="02",
        work_center="CT-02B",
        operations=operations,
        criteria=_criteria(),
    )
    # 350 OPs distintas, fatiadas em lotes de 100 (commitmentBatchSize).
    assert sum(len(chunk) for chunk in gateway.calls) == 350
    assert max(len(chunk) for chunk in gateway.calls) <= 100
    assert len(gateway.calls) == 4
    assert result["summary"]["total"] == 350
    assert result["summary"]["missing"] == 350


def test_service_partial_chunk_failure_is_source_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Lote de 1 OP para cada ordem ser um chunk isolado — a falha de um lote
    # marca apenas as OPs dele, nunca as vizinhas.
    monkeypatch.setattr(
        "production_control_app.application.services"
        ".sequencing_material_resolver_service.commitment_batch_size",
        lambda: 1,
    )
    gateway = _FakeGateway(
        payloads={"111111001": [_material("10070371", order="111111001")]},
        fail_on={"222222001"},
    )
    service = SequencingMaterialResolverService(gateway)
    operations = [
        _operation(order="111111001"),
        _operation(order="222222001"),
    ]
    result = service.resolve_materials(
        branch="02", work_center="CT-02B",
        operations=operations, criteria=_criteria(),
    )
    assert result["items"][0]["status"] == RESOLUTION_RESOLVED
    assert result["items"][1]["status"] == RESOLUTION_SOURCE_UNAVAILABLE
    assert result["summary"]["source_unavailable"] == 1


def test_service_total_unavailability_marks_all_ops_not_missing() -> None:
    gateway = _FakeGateway(fail_on={"111111001", "222222001"})
    service = SequencingMaterialResolverService(gateway)
    result = service.resolve_materials(
        branch="02", work_center="CT-02B",
        operations=[_operation(order="111111001"), _operation(order="222222001")],
        criteria=_criteria(),
    )
    assert result["summary"]["source_unavailable"] == 2
    assert result["summary"]["missing"] == 0


def test_service_malformed_response_is_incomplete() -> None:
    gateway = _FakeGateway(payloads={"111111001": "malformed"})
    service = SequencingMaterialResolverService(gateway)
    result = service.resolve_materials(
        branch="02", work_center="CT-02B",
        operations=[_operation(order="111111001")], criteria=_criteria(),
    )
    assert result["items"][0]["status"] == RESOLUTION_INCOMPLETE


def test_service_keeps_same_order_text_in_different_branches_isolated() -> None:
    """A resolução é por filial: a mesma OP textual em outra filial é outra leitura."""
    gateway = _FakeGateway(
        payloads={
            "111111001": [
                _material("10070371", order="111111001", product_group="1036")
            ]
        }
    )
    service = SequencingMaterialResolverService(gateway)
    result = service.resolve_materials(
        branch="01", work_center="CT-01A",
        operations=[
            _operation(order="111111001", branch="01", work_center="CT-01A")
        ],
        criteria=_criteria(),
    )
    assert result["branch"] == "01"
    assert result["items"][0]["product_code"] == "10070371"


def test_service_deterministic_regardless_of_chunk_order() -> None:
    gateway = _FakeGateway(
        payloads={
            "111111001": [_material("10070371", order="111111001")],
            "222222001": [_material("10070372", order="222222001")],
        }
    )
    service = SequencingMaterialResolverService(gateway)
    operations = [
        _operation(order="111111001"),
        _operation(order="222222001"),
    ]
    first = service.resolve_materials(
        branch="02", work_center="CT-02B",
        operations=operations, criteria=_criteria(),
    )
    gateway.calls.clear()
    second = service.resolve_materials(
        branch="02", work_center="CT-02B",
        operations=list(reversed(operations)), criteria=_criteria(),
    )
    assert [i["product_code"] for i in first["items"]] == ["10070371", "10070372"]
    assert [i["product_code"] for i in second["items"]] == ["10070372", "10070371"]


def test_service_orders_beyond_window_ceiling_are_incomplete() -> None:
    """Acima do teto de janela não há truncamento silencioso: INCOMPLETE."""
    gateway = _FakeGateway()
    service = SequencingMaterialResolverService(gateway)
    ceiling = 3000  # commitmentBatchSize(100) * maxCommitmentBatches(30)
    operations = [
        _operation(order=f"{index:09d}") for index in range(ceiling + 5)
    ]
    result = service.resolve_materials(
        branch="02", work_center="CT-02B",
        operations=operations, criteria=_criteria(),
    )
    fetched = sum(len(chunk) for chunk in gateway.calls)
    assert fetched == ceiling
    overflow = [i for i in result["items"] if i["status"] == RESOLUTION_INCOMPLETE]
    assert len(overflow) == 5
    assert result["summary"]["total"] == ceiling + 5


# ---------------------------------------------------------------------------
# Hardening E2 — dados indispensáveis, integridade de lote, escopo
# ---------------------------------------------------------------------------


def test_mp_material_without_product_group_is_incomplete_not_missing() -> None:
    item = _material("10070371", product_group="")
    result = resolve_operation_material(
        operation=_operation(), order_items=[item], params=_params()
    )
    assert result["status"] == RESOLUTION_INCOMPLETE
    assert result["detail"] == "insufficient_material_data"


def test_material_without_product_type_is_incomplete() -> None:
    item = _material("10070371", product_type="")
    result = resolve_operation_material(
        operation=_operation(), order_items=[item], params=_params()
    )
    assert result["status"] == RESOLUTION_INCOMPLETE


def test_proven_ineligible_material_still_ignored() -> None:
    """Tipo conhecido ≠ MP ou grupo conhecido fora da config: descarte seguro."""
    items = [
        _material("30000001", product_type="PA"),
        _material("10070371", product_group="9999"),
    ]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_MISSING


def test_absent_zeroed_count_with_zero_aggregate_is_incomplete() -> None:
    """Convivência de versões: sem zeroed_commitment_count e agregado 0/0,
    não dá para provar nem zerado nem ativo → nunca resolved/missing."""
    item = _material("10070371", original_qty=0.0, open_qty=0.0)
    del item["zeroed_commitment_count"]
    result = resolve_operation_material(
        operation=_operation(), order_items=[item], params=_params()
    )
    assert result["status"] == RESOLUTION_INCOMPLETE


def test_absent_zeroed_count_with_positive_aggregate_stays_eligible() -> None:
    """Producer antigo + saldo claramente positivo: not-zeroed provado."""
    item = _material("10070371", original_qty=10.0, open_qty=4.0)
    del item["zeroed_commitment_count"]
    result = resolve_operation_material(
        operation=_operation(), order_items=[item], params=_params()
    )
    assert result["status"] == RESOLUTION_RESOLVED


def test_absent_zeroed_count_irrelevant_when_policy_keeps_zeroed() -> None:
    item = _material("10070371", original_qty=0.0, open_qty=0.0)
    del item["zeroed_commitment_count"]
    result = resolve_operation_material(
        operation=_operation(),
        order_items=[item],
        params=_params(ignore_zeroed_allocations=False),
    )
    assert result["status"] == RESOLUTION_RESOLVED


@pytest.mark.parametrize("zeroed,total", [(-1, 2), (3, 2), (0, 0), ("x", 1)])
def test_invalid_zeroed_or_commitment_count_is_incomplete(
    zeroed: Any, total: Any
) -> None:
    item = _material("10070371", zeroed=zeroed, count=total)
    result = resolve_operation_material(
        operation=_operation(), order_items=[item], params=_params()
    )
    assert result["status"] == RESOLUTION_INCOMPLETE


def test_eligible_row_without_product_code_is_incomplete() -> None:
    item = _material("")
    result = resolve_operation_material(
        operation=_operation(), order_items=[item], params=_params()
    )
    assert result["status"] == RESOLUTION_INCOMPLETE


def test_valid_material_plus_indeterminate_companion_is_incomplete() -> None:
    items = [
        _material("10070371"),
        _material("10071279", product_group=""),  # pode ser outro cabo
    ]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_INCOMPLETE
    assert result["candidate_codes"] == ["10070371"]


def test_two_proven_codes_stay_ambiguous_even_with_indeterminate() -> None:
    items = [
        _material("10070371"),
        _material("10070372"),
        _material("10071279", product_group=""),
    ]
    result = resolve_operation_material(
        operation=_operation(), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_AMBIGUOUS
    assert result["candidate_codes"] == ["10070371", "10070372"]


def test_indeterminate_at_operation_does_not_fall_back() -> None:
    """Item indeterminado na operação também está no escopo da OP: incompleto."""
    items = [
        _material("10071279", operation="01", product_group=""),
        _material("10070371", operation="02"),
    ]
    result = resolve_operation_material(
        operation=_operation(operation="01"), order_items=items, params=_params()
    )
    assert result["status"] == RESOLUTION_INCOMPLETE


def _service_with(payload: Any) -> tuple[SequencingMaterialResolverService, _FakeGateway]:
    gateway = _FakeGateway()
    gateway.static_payload = payload
    return SequencingMaterialResolverService(gateway), gateway


class _RawGateway:
    """Devolve payload arbitrário, para testar validação integral."""

    def __init__(self, payload: Any):
        self.payload = payload
        self.calls: list[list[str]] = []

    def fetch_operation_materials_batch(self, *, branch: str, production_orders: Any):
        self.calls.append(list(production_orders))
        return self.payload


def _resolve(payload: Any, ops: list[dict[str, str]] | None = None, **kw):
    gateway = _RawGateway(payload)
    service = SequencingMaterialResolverService(gateway)
    result = service.resolve_materials(
        branch=kw.get("branch", "02"),
        work_center=kw.get("work_center", "CT-02B"),
        operations=ops or [_operation(order="111111001")],
        criteria=_criteria(),
    )
    return result, gateway


def _envelope(items: Any, **extra: Any) -> dict[str, Any]:
    data = {"branch": "02", "production_orders": ["111111001"], "items": items}
    data.update(extra)
    return {"success": True, "data": data}


def test_malformed_row_in_items_invalidates_chunk() -> None:
    result, _ = _resolve(
        _envelope([_material("10070371", order="111111001"), "lixo"])
    )
    assert result["items"][0]["status"] == RESOLUTION_INCOMPLETE


def test_row_without_order_invalidates_chunk() -> None:
    row = _material("10070371")
    del row["production_order"]
    result, _ = _resolve(_envelope([row]))
    assert result["items"][0]["status"] == RESOLUTION_INCOMPLETE


def test_row_of_unsolicited_order_invalidates_chunk() -> None:
    result, _ = _resolve(
        _envelope([_material("10070371", order="999999999")])
    )
    assert result["items"][0]["status"] == RESOLUTION_INCOMPLETE


def test_envelope_of_other_branch_is_rejected() -> None:
    result, _ = _resolve(
        _envelope([_material("10070371", order="111111001")], branch="01")
    )
    assert result["items"][0]["status"] == RESOLUTION_INCOMPLETE


def test_row_of_other_branch_is_rejected() -> None:
    row = _material("10070371", order="111111001")
    row["branch"] = "01"
    result, _ = _resolve(_envelope([row]))
    assert result["items"][0]["status"] == RESOLUTION_INCOMPLETE


def test_error_shaped_envelope_is_not_success() -> None:
    result, _ = _resolve({"success": False, "data": {"items": "n/a"}})
    assert result["items"][0]["status"] == RESOLUTION_INCOMPLETE


def test_truly_empty_items_is_missing_not_incomplete() -> None:
    result, _ = _resolve(_envelope([]))
    assert result["items"][0]["status"] == RESOLUTION_MISSING


def test_envelope_missing_a_requested_order_is_incomplete() -> None:
    gateway = _RawGateway(
        _envelope([], production_orders=["111111001"])  # cobre só 1 das 2
    )
    service = SequencingMaterialResolverService(gateway)
    result = service.resolve_materials(
        branch="02", work_center="CT-02B",
        operations=[
            _operation(order="111111001"),
            _operation(order="111111002"),
        ],
        criteria=_criteria(),
    )
    # o envelope ecoa só uma das OPs pedidas → lote incompleto
    assert result["items"][0]["status"] == RESOLUTION_INCOMPLETE
    assert result["items"][1]["status"] == RESOLUTION_INCOMPLETE


def test_scope_rejects_foreign_branch_operation() -> None:
    gateway = _FakeGateway()
    service = SequencingMaterialResolverService(gateway)
    with pytest.raises(ValueError):
        service.resolve_materials(
            branch="02", work_center="CT-02B",
            operations=[_operation(branch="01")],
            criteria=_criteria(),
        )
    assert gateway.calls == []


def test_scope_rejects_operation_of_other_work_center() -> None:
    gateway = _FakeGateway()
    service = SequencingMaterialResolverService(gateway)
    with pytest.raises(ValueError):
        service.resolve_materials(
            branch="02", work_center="CT-02B",
            operations=[_operation(work_center="CT-01A")],
            criteria=_criteria(),
        )
    assert gateway.calls == []


def test_scope_rejects_missing_order_or_operation() -> None:
    service = SequencingMaterialResolverService(_FakeGateway())
    for bad in (
        {"work_center": "CT-02B", "production_order": "", "operation_code": "01"},
        {"work_center": "CT-02B", "production_order": "111111001", "operation_code": ""},
        {"work_center": "CT-02B", "production_order": "111111001"},
        "not-a-dict",
    ):
        with pytest.raises(ValueError):
            service.resolve_materials(
                branch="02", work_center="CT-02B",
                operations=[bad], criteria=_criteria(),
            )


def test_scope_rejects_empty_branch_or_center() -> None:
    service = SequencingMaterialResolverService(_FakeGateway())
    with pytest.raises(ValueError):
        service.resolve_materials(
            branch="", work_center="CT-02B",
            operations=[_operation()], criteria=_criteria(),
        )
    with pytest.raises(ValueError):
        service.resolve_materials(
            branch="02", work_center="",
            operations=[_operation()], criteria=_criteria(),
        )


def test_operation_without_branch_field_inherits_context() -> None:
    """O snapshot canônico pode não carregar filial por item: a filial vem do
    contexto confiável (fila WORKING carregada pelo backend)."""
    op = {"work_center": "CT-02B", "production_order": "111111001",
          "operation_code": "01"}
    gateway = _FakeGateway(
        payloads={"111111001": [_material("10070371", order="111111001")]}
    )
    service = SequencingMaterialResolverService(gateway)
    result = service.resolve_materials(
        branch="02", work_center="CT-02B", operations=[op], criteria=_criteria()
    )
    assert result["items"][0]["branch"] == "02"
    assert result["items"][0]["status"] == RESOLUTION_RESOLVED
    assert op == {"work_center": "CT-02B", "production_order": "111111001",
                  "operation_code": "01"}
