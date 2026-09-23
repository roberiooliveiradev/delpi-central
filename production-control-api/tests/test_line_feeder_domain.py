"""Domínio do alimentador de linha — corte por horário programado e rateio FIFO."""

from __future__ import annotations

from datetime import datetime

import pytest

from production_control_app.domain.services.line_feeder_requirements import (
    STATUS_AT_RISK,
    STATUS_COVERED,
    STATUS_TO_PICK,
    STATUS_UNKNOWN,
    build_requirements,
    group_by_work_center,
    normalize_commitments,
    summarize,
)
from production_control_app.domain.services.line_feeder_schedule_cutoff import (
    filter_by_cutoff,
    operation_scheduled_start,
    parse_cutoff,
    sort_by_scheduled_start,
    within_cutoff,
)
from production_control_app.domain.services.machine_load_snapshot_payload import (
    decode_snapshot_payload,
    payload_operations,
    payload_work_centers,
)


def _operation(
    *,
    work_center: str,
    order: str,
    operation: str = "01",
    date: str | None = "2026-09-22",
    time: str | None = "08:00",
) -> dict:
    return {
        "work_center": work_center,
        "production_order": order,
        "operation_code": operation,
        "scheduled_date": date,
        "scheduled_start_time": time,
    }


def _material(
    code: str,
    qty: float,
    *,
    unit: str = "PC",
    product_type: str = "MP",
) -> dict:
    return {
        "product_code": code,
        "description": f"Material {code}",
        "unit": unit,
        "product_type": product_type,
        "open_qty": qty,
    }


# --------------------------------------------------------------------------- #
# Corte por horário programado
# --------------------------------------------------------------------------- #


def test_parse_cutoff_with_and_without_time() -> None:
    assert parse_cutoff("2026-09-22", "14:30") == datetime(2026, 9, 22, 14, 30)
    # Sem hora, "dia 22" significa o dia inteiro.
    assert parse_cutoff("2026-09-22", None) == datetime(2026, 9, 22, 23, 59, 59)
    assert parse_cutoff("2026-09-22", "  ") == datetime(2026, 9, 22, 23, 59, 59)


def test_parse_cutoff_rejects_invalid_input() -> None:
    with pytest.raises(ValueError):
        parse_cutoff(None, "14:00")
    with pytest.raises(ValueError):
        parse_cutoff("22/09/2026", "14:00")
    with pytest.raises(ValueError):
        parse_cutoff("2026-09-22", "banana")
    with pytest.raises(ValueError):
        parse_cutoff("2026-09-22", "99:99")


def test_operation_scheduled_start_accepts_raw_totvs_time() -> None:
    assert operation_scheduled_start(
        _operation(work_center="B1", order="1", time="0730")
    ) == datetime(2026, 9, 22, 7, 30)
    # Sem hora, a operação começa no início do dia programado.
    assert operation_scheduled_start(
        _operation(work_center="B1", order="1", time=None)
    ) == datetime(2026, 9, 22, 0, 0)
    assert operation_scheduled_start(_operation(work_center="B1", order="1", date=None)) is None


def test_cutoff_positive_sibling_and_negative() -> None:
    cutoff = parse_cutoff("2026-09-22", "14:00")
    before = _operation(work_center="B1", order="10840401001", time="08:00")
    sibling = _operation(work_center="B2", order="10840401002", time="13:59")
    after = _operation(work_center="B1", order="10840401003", time="14:01")
    at_cutoff = _operation(work_center="B1", order="10840401004", time="14:00")

    assert within_cutoff(before, cutoff=cutoff) is True
    assert within_cutoff(sibling, cutoff=cutoff) is True
    assert within_cutoff(after, cutoff=cutoff) is False
    # O corte é inclusivo: o material precisa estar lá *às* 14h.
    assert within_cutoff(at_cutoff, cutoff=cutoff) is True

    kept = filter_by_cutoff([before, sibling, after, at_cutoff], cutoff=cutoff)
    assert [item["production_order"] for item in kept] == [
        "10840401001",
        "10840401002",
        "10840401004",
    ]


def test_cutoff_keeps_operation_without_schedule() -> None:
    cutoff = parse_cutoff("2026-09-22", "06:00")
    orphan = _operation(work_center="B1", order="1", date=None, time=None)
    # Sem data programada a operação aparece para ser corrigida, não desaparece.
    assert within_cutoff(orphan, cutoff=cutoff) is True
    assert filter_by_cutoff([orphan], cutoff=cutoff) == [orphan]


def test_cutoff_respects_day_boundary() -> None:
    cutoff = parse_cutoff("2026-09-22", "23:00")
    next_day = _operation(work_center="B1", order="1", date="2026-09-23", time="06:00")
    assert within_cutoff(next_day, cutoff=cutoff) is False


def test_sort_by_scheduled_start_pushes_undated_to_the_end() -> None:
    late = _operation(work_center="B1", order="3", time="16:00")
    early = _operation(work_center="B2", order="1", time="07:00")
    undated = _operation(work_center="B3", order="2", date=None, time=None)
    ordered = sort_by_scheduled_start([late, undated, early])
    assert [item["production_order"] for item in ordered] == ["1", "3", "2"]


# --------------------------------------------------------------------------- #
# Necessidade e rateio FIFO
# --------------------------------------------------------------------------- #


def test_requirement_covered_when_point_of_use_has_everything() -> None:
    operations = [_operation(work_center="B1", order="1", time="08:00")]
    requirements = build_requirements(
        operations,
        commitments_by_operation={("1", "1"): [_material("100", 10.0)]},
        point_of_use_balances={"100": 25.0},
        source_balances={"100": 500.0},
    )
    assert len(requirements) == 1
    item = requirements[0]
    assert item.required_qty == 10.0
    assert item.point_of_use_qty == 10.0
    assert item.to_deliver_qty == 0.0
    assert item.status == STATUS_COVERED


def test_requirement_to_pick_when_stockroom_covers_the_gap() -> None:
    operations = [_operation(work_center="B1", order="1", time="08:00")]
    requirements = build_requirements(
        operations,
        commitments_by_operation={("1", "1"): [_material("100", 10.0)]},
        point_of_use_balances={"100": 4.0},
        source_balances={"100": 50.0},
    )
    item = requirements[0]
    assert item.point_of_use_qty == 4.0
    assert item.to_deliver_qty == 6.0
    assert item.source_available_qty == 6.0
    assert item.status == STATUS_TO_PICK


def test_requirement_at_risk_when_stockroom_cannot_cover() -> None:
    operations = [_operation(work_center="B1", order="1", time="08:00")]
    requirements = build_requirements(
        operations,
        commitments_by_operation={("1", "1"): [_material("100", 10.0)]},
        point_of_use_balances={"100": 1.0},
        source_balances={"100": 2.0},
    )
    item = requirements[0]
    assert item.to_deliver_qty == 9.0
    assert item.source_available_qty == 2.0
    assert item.status == STATUS_AT_RISK


def test_negative_balance_counts_as_zero() -> None:
    operations = [_operation(work_center="B1", order="1", time="08:00")]
    requirements = build_requirements(
        operations,
        commitments_by_operation={("1", "1"): [_material("100", 5.0)]},
        point_of_use_balances={"100": -7.0},
        source_balances={"100": -3.0},
    )
    item = requirements[0]
    assert item.point_of_use_qty == 0.0
    assert item.to_deliver_qty == 5.0
    assert item.source_available_qty == 0.0
    assert item.status == STATUS_AT_RISK


def test_fifo_allocation_does_not_double_count_shared_stock() -> None:
    """Duas bancadas disputando o mesmo material: a mais cedo consome primeiro."""
    early = _operation(work_center="B1", order="1", time="08:00")
    late = _operation(work_center="B2", order="2", time="15:00")
    requirements = build_requirements(
        [late, early],  # ordem de entrada não importa: o rateio é por horário
        commitments_by_operation={
            ("1", "1"): [_material("100", 10.0)],
            ("2", "1"): [_material("100", 10.0)],
        },
        point_of_use_balances={"100": 10.0},
        source_balances={"100": 10.0},
    )
    by_center = {item.work_center: item for item in requirements}

    # Sem rateio, as duas bancadas veriam 10 disponíveis e diriam "coberto".
    assert by_center["B1"].point_of_use_qty == 10.0
    assert by_center["B1"].to_deliver_qty == 0.0
    assert by_center["B1"].status == STATUS_COVERED

    assert by_center["B2"].point_of_use_qty == 0.0
    assert by_center["B2"].to_deliver_qty == 10.0
    assert by_center["B2"].source_available_qty == 10.0
    assert by_center["B2"].status == STATUS_TO_PICK


def test_fifo_allocation_splits_partial_remainder() -> None:
    early = _operation(work_center="B1", order="1", time="08:00")
    late = _operation(work_center="B2", order="2", time="09:00")
    requirements = build_requirements(
        [early, late],
        commitments_by_operation={
            ("1", "1"): [_material("100", 6.0)],
            ("2", "1"): [_material("100", 6.0)],
        },
        point_of_use_balances={"100": 8.0},
        source_balances={"100": 1.0},
    )
    by_center = {item.work_center: item for item in requirements}
    assert by_center["B1"].point_of_use_qty == 6.0
    assert by_center["B1"].status == STATUS_COVERED
    # Sobraram 2 do armazém 99 para a segunda bancada.
    assert by_center["B2"].point_of_use_qty == 2.0
    assert by_center["B2"].to_deliver_qty == 4.0
    # E o almoxarifado só tem 1: a bancada tardia é a que fica em risco.
    assert by_center["B2"].source_available_qty == 1.0
    assert by_center["B2"].status == STATUS_AT_RISK


def test_fifo_allocation_is_per_operation_not_per_bench() -> None:
    """A segunda operação de uma bancada não pode furar a fila de outra bancada."""
    bench_a_early = _operation(work_center="B1", order="1", operation="01", time="08:00")
    bench_b_mid = _operation(work_center="B2", order="2", operation="01", time="09:00")
    bench_a_late = _operation(work_center="B1", order="3", operation="01", time="18:00")
    requirements = build_requirements(
        [bench_a_early, bench_b_mid, bench_a_late],
        commitments_by_operation={
            ("1", "1"): [_material("100", 5.0)],
            ("2", "1"): [_material("100", 5.0)],
            ("3", "1"): [_material("100", 5.0)],
        },
        point_of_use_balances={"100": 10.0},
        source_balances={"100": 100.0},
    )
    by_center = {item.work_center: item for item in requirements}
    # B1 pede 10 no total, mas só a operação das 08:00 entra antes de B2.
    assert by_center["B1"].required_qty == 10.0
    assert by_center["B1"].point_of_use_qty == 5.0
    assert by_center["B1"].to_deliver_qty == 5.0
    # B2 às 09:00 é atendida antes da operação das 18:00 de B1.
    assert by_center["B2"].point_of_use_qty == 5.0
    assert by_center["B2"].status == STATUS_COVERED


def test_distinct_products_do_not_share_allocation() -> None:
    a = _operation(work_center="B1", order="1", time="08:00")
    b = _operation(work_center="B2", order="2", time="09:00")
    requirements = build_requirements(
        [a, b],
        commitments_by_operation={
            ("1", "1"): [_material("100", 5.0)],
            ("2", "1"): [_material("200", 5.0)],
        },
        point_of_use_balances={"100": 5.0, "200": 5.0},
        source_balances={},
    )
    assert all(item.status == STATUS_COVERED for item in requirements)


def test_operation_without_commitments_is_skipped() -> None:
    requirements = build_requirements(
        [_operation(work_center="B1", order="1", time="08:00")],
        commitments_by_operation={},
        point_of_use_balances={"100": 5.0},
        source_balances={"100": 5.0},
    )
    assert requirements == []


def test_zero_open_qty_commitment_is_not_a_requirement() -> None:
    requirements = build_requirements(
        [_operation(work_center="B1", order="1", time="08:00")],
        commitments_by_operation={("1", "1"): [_material("100", 0.0)]},
        point_of_use_balances={},
        source_balances={},
    )
    assert requirements == []


def test_balances_unavailable_reports_unknown_instead_of_at_risk() -> None:
    requirements = build_requirements(
        [_operation(work_center="B1", order="1", time="08:00")],
        commitments_by_operation={("1", "1"): [_material("100", 10.0)]},
        point_of_use_balances=None,
        source_balances=None,
        balances_available=False,
    )
    item = requirements[0]
    assert item.required_qty == 10.0
    # Saldo não medido não vira "falta tudo": isso mandaria o alimentador buscar
    # material que já pode estar na bancada.
    assert item.point_of_use_qty is None
    assert item.to_deliver_qty is None
    assert item.source_available_qty is None
    assert item.status == STATUS_UNKNOWN


def test_same_product_in_two_operations_of_same_bench_aggregates() -> None:
    requirements = build_requirements(
        [
            _operation(work_center="B1", order="1", operation="01", time="08:00"),
            _operation(work_center="B1", order="2", operation="02", time="10:00"),
        ],
        commitments_by_operation={
            ("1", "1"): [_material("100", 3.0)],
            ("2", "2"): [_material("100", 4.0)],
        },
        point_of_use_balances={"100": 0.0},
        source_balances={"100": 100.0},
    )
    assert len(requirements) == 1
    item = requirements[0]
    assert item.required_qty == 7.0
    assert item.operation_count == 2
    assert item.production_orders == ("1", "2")
    assert item.first_scheduled_at == "2026-09-22T08:00:00"


def test_normalize_commitments_indexes_by_op_and_operation_ignoring_leading_zero() -> None:
    indexed = normalize_commitments(
        [
            {
                "production_order": "10840401001",
                "operation": "01",
                "product_code": "100",
                "open_qty": 1.0,
            },
            {
                "production_order": "10840401001",
                "operation": "1",
                "product_code": "200",
                "open_qty": 2.0,
            },
            {"production_order": "", "operation": "01", "product_code": "300"},
        ]
    )
    assert list(indexed) == [("10840401001", "1")]
    assert len(indexed[("10840401001", "1")]) == 2


def test_requirements_match_operation_code_across_leading_zero_forms() -> None:
    requirements = build_requirements(
        [_operation(work_center="B1", order="1", operation="010", time="08:00")],
        commitments_by_operation=normalize_commitments(
            [
                {
                    "production_order": "1",
                    "operation": "10",
                    "product_code": "100",
                    "description": "Cabo",
                    "unit": "MT",
                    "product_type": "MP",
                    "open_qty": 4.0,
                }
            ]
        ),
        point_of_use_balances={"100": 4.0},
        source_balances={},
    )
    assert len(requirements) == 1
    assert requirements[0].status == STATUS_COVERED


def test_demand_keeps_raw_material_and_drops_intermediate() -> None:
    """Positive + negative: só MP entra; PI (mesmo com código '5…') fica de fora."""
    requirements = build_requirements(
        [
            _operation(work_center="B1", order="1", time="08:00"),
            _operation(work_center="B1", order="2", time="09:00"),
        ],
        commitments_by_operation={
            ("1", "1"): [_material("30190001", 5.0, product_type="MP")],
            ("2", "1"): [_material("50215375", 8.0, product_type="PI")],
        },
        point_of_use_balances={"30190001": 0.0, "50215375": 0.0},
        source_balances={"30190001": 10.0, "50215375": 10.0},
    )
    assert [item.product_code for item in requirements] == ["30190001"]
    assert requirements[0].required_qty == 5.0


def test_demand_excludes_missing_product_type_fail_closed() -> None:
    requirements = build_requirements(
        [_operation(work_center="B1", order="1", time="08:00")],
        commitments_by_operation={
            ("1", "1"): [
                {
                    "product_code": "30190001",
                    "description": "Sem tipo",
                    "unit": "PC",
                    "open_qty": 5.0,
                }
            ]
        },
        point_of_use_balances={},
        source_balances={},
    )
    assert requirements == []


def test_demand_code_looking_like_mp_but_typed_pi_is_excluded() -> None:
    """Prova que o filtro é B1_TIPO, não heurística de prefixo do código."""
    requirements = build_requirements(
        [_operation(work_center="B1", order="1", time="08:00")],
        commitments_by_operation={
            ("1", "1"): [_material("30199999", 5.0, product_type="PI")],
        },
        point_of_use_balances={"30199999": 0.0},
        source_balances={"30199999": 10.0},
    )
    assert requirements == []


def test_shared_mp_still_aggregates_across_benches() -> None:
    """Sibling: duas bancadas com a mesma MP continuam somando."""
    from production_control_app.domain.services.line_feeder_requirements import (
        pick_list_by_product,
        pick_list_candidates,
    )

    requirements = build_requirements(
        [
            _operation(work_center="B1", order="1", time="08:00"),
            _operation(work_center="B2", order="2", time="09:00"),
        ],
        commitments_by_operation={
            ("1", "1"): [_material("30190001", 3.0)],
            ("2", "1"): [
                _material("30190001", 2.0),
                _material("50215375", 9.0, product_type="PI"),
            ],
        },
        point_of_use_balances={"30190001": 0.0, "50215375": 0.0},
        source_balances={"30190001": 10.0, "50215375": 10.0},
    )
    assert len(requirements) == 2
    lines = pick_list_by_product(pick_list_candidates(requirements))
    assert [line.product_code for line in lines] == ["30190001"]
    assert lines[0].to_deliver_qty == 5.0
    assert lines[0].work_centers == ("B1", "B2")


def test_summary_counts_and_grouping_put_risk_first() -> None:
    requirements = build_requirements(
        [
            _operation(work_center="B1", order="1", time="08:00"),
            _operation(work_center="B2", order="2", time="09:00"),
        ],
        commitments_by_operation={
            ("1", "1"): [_material("100", 5.0)],
            ("2", "1"): [_material("200", 5.0)],
        },
        point_of_use_balances={"100": 5.0, "200": 0.0},
        source_balances={"200": 1.0},
    )
    summary = summarize(requirements)
    assert summary["material_count"] == 2
    assert summary["work_center_count"] == 2
    assert summary["covered_count"] == 1
    assert summary["at_risk_count"] == 1
    assert summary["to_deliver_qty"] == 5.0

    groups = group_by_work_center(requirements)
    # A bancada com risco aparece primeiro.
    assert [group["work_center"] for group in groups] == ["B2", "B1"]
    assert groups[0]["summary"]["at_risk_count"] == 1
    assert groups[0]["items"][0]["status"] == STATUS_AT_RISK


def test_pick_list_by_product_sums_benches_and_sorts_by_code() -> None:
    from production_control_app.domain.services.line_feeder_requirements import (
        pick_list_by_product,
        pick_list_candidates,
    )

    requirements = build_requirements(
        [
            _operation(work_center="B1", order="1", time="08:00"),
            _operation(work_center="B2", order="2", time="09:00"),
            _operation(work_center="B1", order="3", time="10:00"),
        ],
        commitments_by_operation={
            ("1", "1"): [_material("200", 5.0)],
            ("2", "1"): [_material("100", 3.0)],
            ("3", "1"): [_material("200", 2.0)],
        },
        point_of_use_balances={"100": 0.0, "200": 0.0},
        source_balances={"100": 10.0, "200": 10.0},
    )
    lines = pick_list_by_product(pick_list_candidates(requirements))
    assert [line.product_code for line in lines] == ["100", "200"]
    by_code = {line.product_code: line for line in lines}
    assert by_code["100"].to_deliver_qty == 3.0
    assert by_code["200"].to_deliver_qty == 7.0
    assert by_code["200"].work_centers == ("B1",)
    assert by_code["100"].work_centers == ("B2",)


def test_pick_list_by_product_skips_covered_and_keeps_empty_location() -> None:
    from production_control_app.domain.services.line_feeder_requirements import (
        MaterialRequirement,
        pick_list_by_product,
        pick_list_candidates,
    )

    requirements = build_requirements(
        [_operation(work_center="B1", order="1", time="08:00")],
        commitments_by_operation={("1", "1"): [_material("100", 5.0)]},
        point_of_use_balances={"100": 5.0},
        source_balances={"100": 0.0},
    )
    assert pick_list_by_product(pick_list_candidates(requirements)) == []

    line = pick_list_by_product(
        [
            MaterialRequirement(
                work_center="B1",
                product_code="100",
                description="Parafuso",
                unit="UN",
                required_qty=5.0,
                point_of_use_qty=0.0,
                to_deliver_qty=5.0,
                source_available_qty=5.0,
                status=STATUS_TO_PICK,
                first_scheduled_at="2026-09-22T08:00:00",
                first_production_order="1",
                first_operation_code="1",
                production_orders=("1",),
                operation_count=1,
            )
        ]
    )[0]
    assert line.with_pickup_location("A-01").pickup_location == "A-01"
    assert line.pickup_location == ""


# --------------------------------------------------------------------------- #
# Decodificação do snapshot (owner único)
# --------------------------------------------------------------------------- #


def test_decode_snapshot_payload_accepts_text_dict_and_garbage() -> None:
    assert decode_snapshot_payload({"payload_json": '{"a": 1}'}) == {"a": 1}
    assert decode_snapshot_payload({"payload_json": {"a": 1}}) == {"a": 1}
    assert decode_snapshot_payload({"payload_json": None}) == {}
    assert decode_snapshot_payload({}) == {}


def test_decode_snapshot_payload_returns_mutable_copy() -> None:
    row = {"payload_json": {"operations": []}}
    payload = decode_snapshot_payload(row)
    payload["operations"] = [{"work_center": "B1"}]
    assert row["payload_json"]["operations"] == []


def test_payload_operations_reads_list_and_envelope_forms() -> None:
    assert payload_operations({"operations": [{"work_center": "B1"}]}) == [
        {"work_center": "B1"}
    ]
    assert payload_operations({"operations": {"items": [{"work_center": "B2"}]}}) == [
        {"work_center": "B2"}
    ]
    assert payload_operations({"operations": None}) == []
    assert payload_operations({}) == []
    assert payload_operations({"operations": [1, "x", {"work_center": "B3"}]}) == [
        {"work_center": "B3"}
    ]
    assert payload_work_centers({"work_centers": [{"work_center": "B1"}]}) == [
        {"work_center": "B1"}
    ]
