"""Multi-source data composition runtime — generalized dependency resolution.

ROUTE A + ROUTE B + ... → combinação → fórmula → resultado, com erros tipados
quando a operação é matematicamente ou contratualmente inválida.
"""

from unittest.mock import MagicMock

import pytest

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.tv_data_transform_service import (
    apply_data_transform_steps,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)
from tv_app.domain.data_query.m_execution import MExecutionError


def _source(source_id, value, steps=None, op_id="get_commercial_rol_summary"):
    block = {
        "id": source_id,
        "type": "data_source",
        "dataBinding": {
            "operationId": op_id,
            "params": {"start_date": "2026-01-01", "end_date": "2026-09-30"},
        },
    }
    if steps:
        block["dataTransform"] = {"steps": steps}
    block["_value"] = value
    return block


def _service(payloads: dict[str, dict], fails: dict[str, Exception] | None = None):
    gateway = MagicMock()

    def _fetch(operation_id, params=None, **kw):
        source_id = (params or {}).get("_sid")
        if fails and source_id in fails:
            raise fails[source_id]
        return payloads[source_id]

    gateway.fetch_by_operation_id.side_effect = _fetch
    return ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(), gateway=gateway
    )


def _scalar(value: float) -> dict:
    return {
        "meta": {"shape": "scalar"},
        "data": {"value": value},
        "route": {"label": "X", "valueFields": ["value"]},
    }


def _blocks(*blocks):
    out = []
    for b in blocks:
        b = dict(b)
        sid = b.pop("_value")
        b["dataBinding"]["params"]["_sid"] = sid
        out.append(b)
    return out


def _resolved(enriched, block_id):
    return next(
        (b.get("resolved") or {} for b in enriched if b.get("id") == block_id),
        {},
    )


def _table_rows(enriched, block_id):
    resolved = _resolved(enriched, block_id)
    table = resolved.get("_queryTable") or {}
    return table.get("rows") or []


def _enrich(service, blocks):
    return service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")


@pytest.fixture(autouse=True)
def _clear_fetch_cache():
    # _data_block_cache é um TTL cache module-level por (operationId, params);
    # fixtures reutilizam params entre testes — isolar para não vazar payload.
    reset_comunicado_data_block_cache()
    yield
    reset_comunicado_data_block_cache()


# ---------------------------------------------------------------------------
# Dependency resolution / materialization
# ---------------------------------------------------------------------------


def test_dependency_source_is_materialized_for_merge():
    """A → B: B materializada e disponível ao merge."""
    blocks = _blocks(
        _source(
            "src_b",
            "b",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {"op": "addColumn", "name": "v_b", "expr": "value"},
            ],
        ),
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "src_b",
                    "leftKey": "jk",
                    "rightKey": "jk",
                    "columns": ["v_b"],
                },
            ],
        ),
    )
    service = _service({"a": _scalar(100), "b": _scalar(80)})
    enriched = _enrich(service, blocks)
    resolved = _resolved(enriched, "src_a")
    assert not resolved.get("error"), resolved.get("error")
    row = _table_rows(enriched, "src_a")[0]
    assert row["value"] == 100  # esquerda preservada
    assert row["v_b"] == 80  # campo do sibling materializado


def test_two_scalar_sources_variation_formula():
    """A{value:100} + B{value:80} → (A/B - 1)*100 = 25."""
    blocks = _blocks(
        _source(
            "src_b",
            "b",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {"op": "addColumn", "name": "value_prev", "expr": "value"},
            ],
        ),
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "src_b",
                    "leftKey": "jk",
                    "rightKey": "jk",
                    "columns": ["value_prev"],
                },
                {
                    "op": "addColumn",
                    "name": "var_pct",
                    "expr": "(value / value_prev - 1) * 100",
                },
            ],
        ),
    )
    service = _service({"a": _scalar(100), "b": _scalar(80)})
    enriched = _enrich(service, blocks)
    row = _table_rows(enriched, "src_a")[0]
    assert row["var_pct"] == pytest.approx(25.0)


def test_three_source_arithmetic():
    """(100 + 20) / 10 = 12 — três fontes componíveis via merges encadeados."""
    blocks = _blocks(
        _source(
            "src_b",
            "b",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {"op": "addColumn", "name": "v_b", "expr": "value"},
            ],
        ),
        _source(
            "src_c",
            "c",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {"op": "addColumn", "name": "v_c", "expr": "value"},
            ],
        ),
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "src_b",
                    "leftKey": "jk",
                    "rightKey": "jk",
                    "columns": ["v_b"],
                },
                {
                    "op": "merge",
                    "sourceId": "src_c",
                    "leftKey": "jk",
                    "rightKey": "jk",
                    "columns": ["v_c"],
                },
                {
                    "op": "addColumn",
                    "name": "result",
                    "expr": "(value + v_b) / v_c",
                },
            ],
        ),
    )
    service = _service({"a": _scalar(100), "b": _scalar(20), "c": _scalar(10)})
    enriched = _enrich(service, blocks)
    row = _table_rows(enriched, "src_a")[0]
    assert row["result"] == pytest.approx(12.0)


def test_four_source_composition_no_structural_limit():
    """Sem limite estrutural de duas fontes: (a+b+c)/d."""
    steps = [{"op": "addColumn", "name": "jk", "expr": "1"}]
    for sid in ("s2", "s3", "s4"):
        steps.append(
            {
                "op": "merge",
                "sourceId": sid,
                "leftKey": "jk",
                "rightKey": "jk",
                "columns": [f"v_{sid}"],
            }
        )
    steps.append(
        {
            "op": "addColumn",
            "name": "result",
            "expr": "(value + v_s2 + v_s3) / v_s4",
        }
    )
    blocks = _blocks(
        *[
            _source(
                sid,
                sid,
                steps=[
                    {"op": "addColumn", "name": "jk", "expr": "1"},
                    {"op": "addColumn", "name": f"v_{sid}", "expr": "value"},
                ],
            )
            for sid in ("s2", "s3", "s4")
        ],
        _source("s1", "s1", steps=steps),
    )
    service = _service(
        {"s1": _scalar(10), "s2": _scalar(10), "s3": _scalar(10), "s4": _scalar(5)}
    )
    enriched = _enrich(service, blocks)
    row = _table_rows(enriched, "s1")[0]
    assert row["result"] == pytest.approx(6.0)


def test_chained_dependencies_ordering():
    """A → B → C: C materializado antes de B, B antes de A."""
    blocks = _blocks(
        # Ordem de documento invertida de propósito — o DAG deve ordenar.
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "src_b",
                    "leftKey": "jk",
                    "rightKey": "jk",
                    "columns": ["sum_bc"],
                },
            ],
        ),
        _source(
            "src_b",
            "b",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "src_c",
                    "leftKey": "jk",
                    "rightKey": "jk",
                    "columns": ["v_c"],
                },
                {"op": "addColumn", "name": "sum_bc", "expr": "value + v_c"},
            ],
        ),
        _source(
            "src_c",
            "c",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {"op": "addColumn", "name": "v_c", "expr": "value"},
            ],
        ),
    )
    service = _service({"a": _scalar(1), "b": _scalar(2), "c": _scalar(3)})
    enriched = _enrich(service, blocks)
    resolved_b = _resolved(enriched, "src_b")
    assert not resolved_b.get("error"), resolved_b.get("error")
    row = _table_rows(enriched, "src_a")[0]
    assert row["sum_bc"] == pytest.approx(5.0)


def test_dependency_cycle_typed_error():
    """A → B → A: ciclo detectado no DAG (m.query_cycle)."""
    merge_a = [
        {"op": "addColumn", "name": "jk", "expr": "1"},
        {"op": "merge", "sourceId": "src_b", "leftKey": "jk", "rightKey": "jk"},
    ]
    merge_b = [
        {"op": "addColumn", "name": "jk", "expr": "1"},
        {"op": "merge", "sourceId": "src_a", "leftKey": "jk", "rightKey": "jk"},
    ]
    blocks = _blocks(
        _source("src_a", "a", steps=merge_a),
        _source("src_b", "b", steps=merge_b),
    )
    service = _service({"a": _scalar(1), "b": _scalar(2)})
    with pytest.raises(ValueError) as exc:
        _enrich(service, blocks)
    assert "m.query_cycle" in str(exc.value)
    assert "ciclo" in str(exc.value).lower()


def test_missing_dependency_typed_error():
    """A → B inexistente: erro tipado, não sucesso vazio."""
    blocks = _blocks(
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "ghost_source",
                    "leftKey": "jk",
                    "rightKey": "jk",
                },
            ],
        ),
    )
    service = _service({"a": _scalar(1)})
    enriched = _enrich(service, blocks)
    resolved = _resolved(enriched, "src_a")
    assert resolved.get("error")
    assert resolved["transformError"]["code"] == "m.merge_source_unavailable"


def test_failed_dependency_distinct_typed_error():
    """B existe mas o fetch falhou → m.merge_source_failed (≠ unavailable)."""
    blocks = _blocks(
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "src_b",
                    "leftKey": "jk",
                    "rightKey": "jk",
                },
            ],
        ),
        _source("src_b", "b"),
    )
    service = _service(
        {"a": _scalar(1)},
        fails={"b": RuntimeError("upstream exploded")},
    )
    enriched = _enrich(service, blocks)
    resolved = _resolved(enriched, "src_a")
    assert resolved["transformError"]["code"] == "m.merge_source_failed"
    assert "src_b" in resolved["transformError"]["message"]


def test_non_source_block_dependency_typed_error():
    """Merge apontando para bloco visual → not_composable, não unavailable."""
    blocks = _blocks(
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "view_1",
                    "leftKey": "jk",
                    "rightKey": "jk",
                },
            ],
        ),
    )
    blocks.append({"id": "view_1", "type": "kpi_view", "dataSourceId": "src_a"})
    service = _service({"a": _scalar(1)})
    enriched = _enrich(service, blocks)
    resolved = _resolved(enriched, "src_a")
    assert resolved["transformError"]["code"] == "m.merge_source_not_composable"


def test_transform_failed_dependency_distinct_typed_error():
    """B existe mas seu transform falha → m.merge_source_failed com causa de B."""
    blocks = _blocks(
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "src_b",
                    "leftKey": "jk",
                    "rightKey": "jk",
                },
            ],
        ),
        _source(
            "src_b",
            "b",
            steps=[{"op": "select", "columns": ["coluna_inexistente"]}],
        ),
    )
    service = _service({"a": _scalar(1), "b": _scalar(2)})
    enriched = _enrich(service, blocks)
    resolved = _resolved(enriched, "src_a")
    assert resolved["transformError"]["code"] == "m.merge_source_failed"


# ---------------------------------------------------------------------------
# Arithmetic / expression errors (executor level)
# ---------------------------------------------------------------------------


def _exec(rows, steps, siblings=None, status=None):
    return apply_data_transform_steps(
        {"columns": list(rows[0]) if rows else [], "rows": rows},
        steps,
        sibling_tables=siblings,
        sibling_status=status,
    )


def test_division_by_zero_typed_error():
    with pytest.raises(MExecutionError) as exc:
        _exec(
            [{"a": 100, "b": 0}],
            [{"op": "addColumn", "name": "r", "expr": "a / b"}],
        )
    assert exc.value.code == "m.calc_division_by_zero"


def test_non_numeric_operand_typed_error():
    with pytest.raises(MExecutionError) as exc:
        _exec(
            [{"a": "abc", "b": 10}],
            [{"op": "addColumn", "name": "r", "expr": "a / b"}],
        )
    assert exc.value.code == "m.calc_invalid_operand"


def test_null_operand_typed_error():
    with pytest.raises(MExecutionError) as exc:
        _exec(
            [{"a": None, "b": 10}],
            [{"op": "addColumn", "name": "r", "expr": "a / b"}],
        )
    assert exc.value.code == "m.calc_null_operand"


def test_missing_field_in_expression_typed_error():
    with pytest.raises(MExecutionError) as exc:
        _exec(
            [{"a": 1}],
            [{"op": "addColumn", "name": "r", "expr": "missing / a"}],
        )
    assert exc.value.code == "m.unknown_column"


def test_iff_guards_division_by_zero():
    """iff lazy: branch não escolhido não deve disparar div/0."""
    table = _exec(
        [{"a": 100, "b": 0}],
        [{"op": "addColumn", "name": "r", "expr": "if(b != 0, a / b, -1)"}],
    )
    assert table["rows"][0]["r"] == -1.0


def test_generic_arithmetic_supported():
    table = _exec(
        [{"a": 10, "b": 5}],
        [
            {"op": "addColumn", "name": "s", "expr": "a + b"},
            {"op": "addColumn", "name": "d", "expr": "a - b"},
            {"op": "addColumn", "name": "m", "expr": "a * b"},
            {"op": "addColumn", "name": "q", "expr": "a / b"},
            {"op": "addColumn", "name": "v", "expr": "(a / b - 1) * 100"},
        ],
    )
    row = table["rows"][0]
    assert row["s"] == 15.0
    assert row["d"] == 5.0
    assert row["m"] == 50.0
    assert row["q"] == 2.0
    assert row["v"] == pytest.approx(100.0)


def test_authoritative_field_usable_in_formula():
    """Ler campo autoritativo numa fórmula é permitido."""
    table = _exec(
        [{"rol": 100, "meta": 50}],
        [{"op": "addColumn", "name": "pct", "expr": "rol / meta * 100"}],
    )
    assert table["rows"][0]["pct"] == pytest.approx(200.0)


def test_authoritative_field_overwrite_rejected():
    """addColumn com nome de coluna existente → colisão tipada."""
    with pytest.raises(MExecutionError) as exc:
        _exec(
            [{"rol": 100}],
            [{"op": "addColumn", "name": "rol", "expr": "rol * 2"}],
        )
    assert exc.value.code == "m.column_collision"


def test_field_collision_still_protected():
    with pytest.raises(MExecutionError) as exc:
        _exec(
            [{"k": 1, "rol": 100}],
            [
                {
                    "op": "merge",
                    "sourceId": "b",
                    "leftKey": "k",
                    "rightKey": "k",
                }
            ],
            siblings={"b": {"columns": ["k", "rol"], "rows": [{"k": 1, "rol": 80}]}},
        )
    assert exc.value.code == "m.merge_field_collision"


def test_real_case_commercial_rol_variation():
    """Caso real: current=4516461.10, previous=4399153.22 → ~+2.67%."""
    payloads = {
        "cur": {
            "meta": {"shape": "scalar"},
            "data": {"rol": 4516461.10, "rol_target_pct": 88.0},
            "route": {"valueFields": ["rol", "rol_target_pct"]},
        },
        "prev": {
            "meta": {"shape": "scalar"},
            "data": {"rol": 4399153.22, "rol_target_pct": 91.0},
            "route": {"valueFields": ["rol", "rol_target_pct"]},
        },
    }
    blocks = _blocks(
        _source(
            "prev",
            "prev",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {"op": "addColumn", "name": "rol_prev", "expr": "rol"},
            ],
        ),
        _source(
            "cur",
            "cur",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "prev",
                    "leftKey": "jk",
                    "rightKey": "jk",
                    "columns": ["rol_prev"],
                },
                {
                    "op": "addColumn",
                    "name": "value",
                    "expr": "(rol / rol_prev - 1) * 100",
                },
            ],
        ),
    )
    service = _service(payloads)
    enriched = _enrich(service, blocks)
    resolved = _resolved(enriched, "cur")
    assert not resolved.get("error"), resolved.get("error")
    row = _table_rows(enriched, "cur")[0]
    # Campo derivado próprio — rol_target_pct da rota intocado.
    assert row["value"] == pytest.approx(2.67, abs=0.01)
    assert row["rol_target_pct"] == 88.0


def test_preview_and_runtime_share_resolution_path():
    """Preview resolve o mesmo grafo de dependências do runtime."""
    from tv_app.application.services.data.tv_data_preview_service import (
        TvDataPreviewService,
    )

    src_b = _source(
        "src_b",
        "b",
        steps=[
            {"op": "addColumn", "name": "jk", "expr": "1"},
            {"op": "addColumn", "name": "v_b", "expr": "value"},
        ],
    )
    src_a = _source(
        "src_a",
        "a",
        steps=[
            {"op": "addColumn", "name": "jk", "expr": "1"},
            {
                "op": "merge",
                "sourceId": "src_b",
                "leftKey": "jk",
                "rightKey": "jk",
                "columns": ["v_b"],
            },
        ],
    )
    blocks = _blocks(src_b, src_a)
    native_config = {"version": 1, "blocks": blocks}
    gateway = MagicMock()
    gateway.fetch_by_operation_id.side_effect = lambda operation_id, **kw: _scalar(
        100 if (kw.get("params") or {}).get("_sid") == "a" else 80
    )
    service = TvDataPreviewService(
        catalog=TvDataRouteCatalogService(),
        enrichment=ComunicadoDataEnrichmentService(
            catalog=TvDataRouteCatalogService(), gateway=gateway
        ),
    )
    previewed = service.preview_block(
        blocks[1], native_config=native_config, authorization="Bearer x"
    )
    resolved = previewed.get("resolved") or {}
    assert not resolved.get("error"), resolved.get("error")
    rows = (resolved.get("_queryTable") or {}).get("rows") or []
    assert rows and rows[0]["v_b"] == 80


def test_empty_dependency_source_is_valid_empty():
    """Fonte com dados vazios é política explícita: merge casa zero linhas
    sem erro genérico (direita vazia → linhas esquerdas com colunas None)."""
    blocks = _blocks(
        _source(
            "src_b",
            "b",
            steps=[{"op": "addColumn", "name": "jk", "expr": "1"}],
        ),
        _source(
            "src_a",
            "a",
            steps=[
                {"op": "addColumn", "name": "jk", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "src_b",
                    "leftKey": "jk",
                    "rightKey": "jk",
                },
            ],
        ),
    )
    service = _service(
        {"a": _scalar(1), "b": {"meta": {}, "data": [], "route": {}}}
    )
    enriched = _enrich(service, blocks)
    resolved = _resolved(enriched, "src_a")
    assert not resolved.get("error"), resolved.get("error")
