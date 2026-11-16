"""Domain tests — routing.line_balance deterministic calculations.

Reference values computed independently of the implementation
(hand arithmetic), following the official guide semantics: rows are
(product, operation, component) — operations repeated per component.
"""

from engineering_app.domain.routing.line_balance import (
    compute_balance,
    group_routing,
)


def _row(product, level, op, wc, res, minutes, setup=0.0, comp=""):
    return {
        "branch": "02",
        "route_code": "01",
        "product_code": product,
        "bom_level": level,
        "operation_code": op,
        "operation_description": f"OP {op}",
        "work_center": wc,
        "resource_code": res,
        "operation_type": "1",
        "standard_time_minutes_piece": minutes,
        "setup_hours": setup,
        "component_code": comp,
        "component_description": f"COMP {comp}" if comp else None,
    }


# Produto P com 2 componentes: op10 aplica-se aos dois (duas linhas),
# op20 a um. Nível 1: componente C1 com op própria.
ITEMS = [
    _row("P", 0, "010", "CT1", "R1", 2.0, comp="C1"),
    _row("P", 0, "010", "CT1", "R1", 2.0, comp="C2"),
    _row("P", 0, "020", "CT2", "R2", 3.0, setup=1.0, comp="C1"),
    _row("C1", 1, "010", "CT9", "R9", 5.0, comp="MP1"),
]


def test_group_routing_dedupes_operations_per_component() -> None:
    g = group_routing(ITEMS)
    assert g["rows_total"] == 4
    assert g["unique_operations"] == 3
    stage_p = [s for s in g["stages"] if s["product_code"] == "P"][0]
    assert len(stage_p["operations"]) == 2
    op10 = stage_p["operations"][0]
    assert op10["operation_code"] == "010"
    assert [c["code"] for c in op10["components"]] == ["C1", "C2"]
    # tempo da operação NÃO é multiplicado pelo nº de componentes
    assert op10["time_minutes_piece"] == 2.0


def test_stages_never_merged_across_bom_levels() -> None:
    g = group_routing(ITEMS)
    levels = {(s["product_code"], s["bom_level"]) for s in g["stages"]}
    assert levels == {("P", 0), ("C1", 1)}


def test_compute_balance_takt_work_content_and_min_stations() -> None:
    g = group_routing(ITEMS)
    stage_p = [s for s in g["stages"] if s["product_code"] == "P"][0]
    # conteúdo = 2.0 + 3.0 = 5.0 min; takt = 420/500 = 0.84 →
    # mínimo teórico = ceil(5/0.84) = 6
    r = compute_balance(
        stage_p["operations"], demand=500, available_minutes=420
    )
    assert r["takt_minutes"] == 0.84
    assert r["work_content_minutes"] == 5.0
    assert r["theoretical_min_stations"] == 6
    # ambas as operações excedem o takt → gargalo é a maior (3.0)
    assert r["bottleneck_candidate"]["operation_code"] == "020"
    assert {o["operation_code"] for o in r["over_takt_operations"]} == {
        "010",
        "020",
    }
    # sem batch_size, setup NÃO entra no tempo por peça
    assert r["setup_minutes_piece_amortized"] is None
    assert r["setup_hours_total"] == 1.0


def test_setup_amortized_only_with_batch_size() -> None:
    g = group_routing(ITEMS)
    stage_p = [s for s in g["stages"] if s["product_code"] == "P"][0]
    # batch 100 → setup 1h = 60min/100 = 0.6 min/peça na op020
    r = compute_balance(
        stage_p["operations"],
        demand=500,
        available_minutes=420,
        batch_size=100,
    )
    assert r["setup_minutes_piece_amortized"] == 0.6
    assert r["work_content_minutes"] == 5.6


def test_missing_inputs_yield_partial_with_missing_parameters() -> None:
    g = group_routing(ITEMS)
    stage_p = [s for s in g["stages"] if s["product_code"] == "P"][0]
    r = compute_balance(stage_p["operations"])
    assert r["takt_minutes"] is None
    assert r["theoretical_min_stations"] is None
    assert r["balance_scenario"] is None
    assert set(r["missing_parameters"]) == {
        "demand",
        "available_minutes",
    }
    assert any("Takt" in m for m in r["limitations"])


def test_operations_without_time_excluded_and_flagged() -> None:
    items = ITEMS + [_row("P", 0, "030", "CT3", "R3", None, comp="C1")]
    g = group_routing(items)
    stage_p = [s for s in g["stages"] if s["product_code"] == "P"][0]
    r = compute_balance(
        stage_p["operations"], demand=500, available_minutes=420
    )
    assert r["operations_missing_time"] == ["030"]
    assert r["work_content_minutes"] == 5.0  # op030 excluída


def test_station_check_feasibility_and_efficiency() -> None:
    g = group_routing(ITEMS)
    stage_p = [s for s in g["stages"] if s["product_code"] == "P"][0]
    # 8 postos: required cycle = 5/8 = 0.625 < takt 0.84 → viável;
    # eficiência teórica = 5/(8*0.84) = 0.744048
    ok = compute_balance(
        stage_p["operations"],
        demand=500,
        available_minutes=420,
        num_stations=8,
    )
    assert ok["station_check"]["feasible"] is True
    assert ok["station_check"]["required_cycle_minutes"] == 0.625
    assert ok["station_check"]["theoretical_efficiency"] == 0.744048
    # 4 postos < mínimo teórico 6 → inviável
    bad = compute_balance(
        stage_p["operations"],
        demand=500,
        available_minutes=420,
        num_stations=4,
    )
    assert bad["station_check"]["feasible"] is False
    assert any("inviável" in m for m in bad["limitations"])


def test_ffd_scenario_labeled_simulation_with_idle() -> None:
    # ops de 4, 3, 2, 1 min em takt 5 → FFD: [4+1]=5, [3+2]=5 →
    # 2 postos, eficiência = 10/10 = 1.0, ociosidade 0
    ops = [
        {
            "operation_code": code,
            "operation_description": code,
            "work_center": "CT",
            "resource_code": "R",
            "time_minutes_piece": t,
            "setup_hours": 0.0,
            "components": [],
        }
        for code, t in (("A", 4.0), ("B", 3.0), ("C", 2.0), ("D", 1.0))
    ]
    r = compute_balance(ops, demand=100, available_minutes=500)
    assert r["takt_minutes"] == 5.0
    s = r["balance_scenario"]
    assert s["data_class"] == "SIMULATION"
    assert s["stations_used"] == 2
    assert s["balance_efficiency"] == 1.0
    assert s["idle_minutes_total"] == 0.0
    assert s["stations"][0]["operations"] == ["A", "D"]
    assert s["stations"][1]["operations"] == ["B", "C"]
    assert s["caveats"]  # precedência não verificada — declarado


def test_operation_over_takt_gets_own_station() -> None:
    ops = [
        {
            "operation_code": "BIG",
            "operation_description": "BIG",
            "work_center": "CT",
            "resource_code": "R",
            "time_minutes_piece": 7.0,
            "setup_hours": 0.0,
            "components": [],
        },
        {
            "operation_code": "S",
            "operation_description": "S",
            "work_center": "CT",
            "resource_code": "R",
            "time_minutes_piece": 1.0,
            "setup_hours": 0.0,
            "components": [],
        },
    ]
    r = compute_balance(ops, demand=100, available_minutes=500)
    s = r["balance_scenario"]
    assert s["stations_used"] == 2
    assert [o["operation_code"] for o in r["over_takt_operations"]] == [
        "BIG"
    ]


def test_empty_operations() -> None:
    r = compute_balance([], demand=500, available_minutes=420)
    assert r["operations_count"] == 0
    assert r["work_content_minutes"] == 0.0
    assert r["bottleneck_candidate"] is None
