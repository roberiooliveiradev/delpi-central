"""Line balancing — cálculos determinísticos sobre o roteiro oficial.

Fonte: itens de ``GET /products/{code}/guide`` (api-delpi — SG2010 ×
SG1010 recursiva × SGF010). Cada linha do payload é a tupla
(produto, operação, componente): a MESMA operação aparece repetida
para cada componente da BOM a que se aplica — jamais somar linhas.

Semântica de tempos (owner upstream, nunca reconvertida):
- ``standard_time_minutes_piece``: tempo padrão por peça em minutos.
- ``setup_hours``: tempo de preparação por LOTE — só vira custo por
  peça quando ``batch_size`` é explicitamente informado.

Estágio produtivo = par (product_code, bom_level). Operações de
níveis/produtos distintos NÃO compõem uma mesma linha: cada estágio
é analisado isoladamente.

Toda saída é determinística (mesma entrada → mesma saída), arredondada
a ``MINUTES_PRECISION`` casas decimais. Nenhuma hipótese é assumida:
precedência, paralelismo, operadores e disponibilidade só entram se
explicitamente fornecidos.
"""

from __future__ import annotations

import math
from typing import Any

MINUTES_PRECISION = 6

# Vocabulário fechado de parâmetros do consumidor (parameters{}).
BALANCE_INPUT_FIELDS: frozenset[str] = frozenset(
    {
        "product_code",
        "branch",
        "max_depth",
        "bom_levels",
        "demand",
        "available_minutes",
        "batch_size",
        "num_stations",
    }
)


def _num(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _r(value: float | None) -> float | None:
    return None if value is None else round(float(value), MINUTES_PRECISION)


def group_routing(items: list[dict]) -> dict:
    """Consolida linhas oficiais em operações únicas por estágio.

    Uma operação é identificada por
    (product_code, operation_code, work_center, resource_code,
    bom_level). Linhas adicionais da mesma operação (uma por
    componente) são fundidas em ``components``.
    """
    stages: dict[tuple[str, int], dict] = {}
    ops: dict[tuple, dict] = {}
    rows = 0
    for item in items or []:
        rows += 1
        product = str(item.get("product_code") or "").strip()
        level = int(_num(item.get("bom_level")) or 0)
        op_code = str(item.get("operation_code") or "").strip()
        wc = str(item.get("work_center") or "").strip()
        res = str(item.get("resource_code") or "").strip()
        stage_key = (product, level)
        stage = stages.setdefault(
            stage_key,
            {
                "product_code": product,
                "bom_level": level,
                "branch": item.get("branch"),
                "route_code": item.get("route_code"),
                "operations": [],
            },
        )
        key = stage_key + (op_code, wc, res)
        op = ops.get(key)
        if op is None:
            op = {
                "operation_code": op_code,
                "operation_description": item.get("operation_description"),
                "work_center": wc or None,
                "resource_code": res or None,
                "operation_type": item.get("operation_type"),
                "mandatory_operation": item.get("mandatory_operation"),
                "mandatory_sequence": item.get("mandatory_sequence"),
                "mandatory_report": item.get("mandatory_report"),
                "time_minutes_piece": _num(
                    item.get("standard_time_minutes_piece")
                ),
                "setup_hours": _num(item.get("setup_hours")),
                "components": [],
            }
            ops[key] = op
            stage["operations"].append(op)
        component = str(item.get("component_code") or "").strip()
        if component and component not in {
            c["code"] for c in op["components"]
        }:
            op["components"].append(
                {
                    "code": component,
                    "description": item.get("component_description"),
                    "sequence": item.get("component_sequence"),
                }
            )
    ordered = sorted(
        stages.values(),
        key=lambda s: (s["bom_level"], s["product_code"]),
    )
    return {
        "rows_total": rows,
        "unique_operations": sum(len(s["operations"]) for s in ordered),
        "stages": ordered,
    }


def _positive_int(value: Any) -> int | None:
    n = _num(value)
    if n is None:
        return None
    i = int(n)
    return i if i > 0 else None


def compute_balance(
    operations: list[dict],
    *,
    demand: Any = None,
    available_minutes: Any = None,
    batch_size: Any = None,
    num_stations: Any = None,
) -> dict:
    """Balanço determinístico de UM estágio (uma linha candidata).

    ``demand`` (peças no período) e ``available_minutes`` (tempo
    produtivo do período) produzem o takt; sem ambos completos o
    resultado é parcial (``missing_parameters``). ``batch_size``
    amortiza ``setup_hours`` por peça; sem ele o setup NÃO entra no
    tempo por peça — é reportado à parte. ``num_stations`` informado
    gera verificação de viabilidade e eficiência do arranjo.
    """
    demand_n = _positive_int(demand)
    avail = _num(available_minutes)
    batch = _positive_int(batch_size)
    stations = _positive_int(num_stations)

    limitations: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []

    def _classify(name: str, raw: Any, parsed: Any, required: bool) -> None:
        if raw in (None, ""):
            if required:
                missing.append(name)
        elif parsed is None:
            invalid.append(name)

    _classify("demand", demand, demand_n, required=True)
    _classify(
        "available_minutes",
        available_minutes,
        avail if avail and avail > 0 else None,
        required=True,
    )
    _classify("batch_size", batch_size, batch, required=False)
    _classify("num_stations", num_stations, stations, required=False)
    if invalid:
        limitations.append(
            "Parâmetros fornecidos com valor inválido (ignorados): "
            + ", ".join(invalid)
            + "."
        )

    ops = [dict(o) for o in operations or []]
    missing_time = [
        o["operation_code"]
        for o in ops
        if o.get("time_minutes_piece") is None
    ]
    timed = [o for o in ops if o.get("time_minutes_piece") is not None]
    if missing_time:
        limitations.append(
            "Operações sem tempo padrão oficial excluídas do conteúdo "
            "de trabalho: " + ", ".join(missing_time) + "."
        )

    setup_total_hours = _r(
        sum(o.get("setup_hours") or 0.0 for o in ops)
    )
    amortized_piece = None
    if batch:
        amortized_piece = _r(
            sum(
                ((o.get("setup_hours") or 0.0) * 60.0) / batch
                for o in timed
            )
        )
        for o in timed:
            o["effective_minutes_piece"] = _r(
                o["time_minutes_piece"]
                + ((o.get("setup_hours") or 0.0) * 60.0) / batch
            )
    else:
        if setup_total_hours:
            limitations.append(
                "setup_hours não amortizado: batch_size não informado — "
                "setup reportado à parte, nunca somado ao tempo peça."
            )
        for o in timed:
            o["effective_minutes_piece"] = _r(o["time_minutes_piece"])

    work_content = _r(
        sum(o["effective_minutes_piece"] or 0.0 for o in timed)
    )

    bottleneck = None
    if timed:
        worst = max(timed, key=lambda o: o["effective_minutes_piece"])
        bottleneck = {
            "operation_code": worst["operation_code"],
            "operation_description": worst.get("operation_description"),
            "work_center": worst.get("work_center"),
            "minutes_piece": worst["effective_minutes_piece"],
        }

    takt = None
    theoretical_min = None
    over_takt: list[dict] = []
    if demand_n and avail and avail > 0:
        takt = _r(avail / demand_n) or None
        if work_content is not None and takt:
            theoretical_min = math.ceil(work_content / takt)
        over_takt = [
            {
                "operation_code": o["operation_code"],
                "work_center": o.get("work_center"),
                "minutes_piece": o["effective_minutes_piece"],
            }
            for o in timed
            if o["effective_minutes_piece"] > takt
        ]
        if not timed:
            limitations.append(
                "Sem operações com tempo — takt computável mas "
                "conteúdo de trabalho indisponível."
            )
    else:
        limitations.append(
            "Takt indisponível: informe demand (peças/período) e "
            "available_minutes (tempo produtivo do período)."
        )

    station_check = None
    if stations is not None:
        check = {
            "num_stations": stations,
            "theoretical_min_stations": theoretical_min,
        }
        if work_content is not None:
            check["required_cycle_minutes"] = _r(work_content / stations)
            if takt:
                check["feasible"] = work_content / stations <= takt
                check["theoretical_efficiency"] = _r(
                    work_content / (stations * takt)
                )
        station_check = check
        if theoretical_min is not None and stations < theoretical_min:
            limitations.append(
                f"num_stations={stations} abaixo do mínimo teórico "
                f"{theoretical_min} — configuração inviável para o takt."
            )

    scenario = None
    if takt and timed:
        scenario = _ffd_scenario(timed, takt)

    return {
        "operations_count": len(ops),
        "operations_missing_time": missing_time,
        "setup_hours_total": setup_total_hours,
        "setup_minutes_piece_amortized": amortized_piece,
        "work_content_minutes": work_content,
        "takt_minutes": takt,
        "theoretical_min_stations": theoretical_min,
        "bottleneck_candidate": bottleneck,
        "over_takt_operations": over_takt,
        "station_check": station_check,
        "balance_scenario": scenario,
        "missing_parameters": missing,
        "invalid_parameters": invalid,
        "limitations": limitations,
    }


def _ffd_scenario(operations: list[dict], takt: float) -> dict:
    """Cenário SIMULATION — first-fit decreasing em postos de capacidade
    = takt. Sem precedência informada a alocação ignora restrições de
    sequência (limitação declarada no payload)."""
    ranked = sorted(
        operations,
        key=lambda o: o["effective_minutes_piece"],
        reverse=True,
    )
    stations: list[dict] = []
    for op in ranked:
        t = op["effective_minutes_piece"]
        placed = False
        for st in stations:
            if st["load_minutes"] + t <= takt:
                st["operations"].append(op["operation_code"])
                st["load_minutes"] += t
                placed = True
                break
        if not placed:
            stations.append(
                {"operations": [op["operation_code"]], "load_minutes": t}
            )
    content = sum(o["effective_minutes_piece"] for o in operations)
    used = len(stations)
    for st in stations:
        st["load_minutes"] = _r(st["load_minutes"])
        st["idle_minutes"] = _r(takt - st["load_minutes"])
    return {
        "type": "first_fit_decreasing",
        "data_class": "SIMULATION",
        "stations_used": used,
        "stations": stations,
        "balance_efficiency": _r(content / (used * takt)),
        "idle_minutes_total": _r(used * takt - content),
        "caveats": [
            "Alocação hipotética por capacidade de takt — precedência "
            "entre operações não informada e não verificada.",
            "Não considera operadores, ferramentas, layout ou restrições "
            "de equipamento — simulação até revisão da Engenharia.",
        ],
    }
