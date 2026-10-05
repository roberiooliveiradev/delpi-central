"""Paridade de filtros — camadas compartilhadas (Tela/Programação) e DataModel.

Cobre:
- union schema de ``dataFilters`` inclui rotas de ``dataModels[].inputs[]``;
- ExpressionSpec em camada compartilhada (validate + scoping por rota);
- ExpressionSpec em ``playlist.dataDefaults`` (sanitize + escopo);
- digest/relayer enxergam inputs de DataModel como fontes;
- precedência do merge: programação < tela < fonte/input.
"""

from __future__ import annotations

import pytest

from tv_app.application.services.comunicado_data_params_service import (
    merge_data_params,
)
from tv_app.application.services.data.data_model_service import (
    collect_native_config_operation_ids,
    native_config_model_source_params,
)
from tv_app.application.services.data.filter_digest_service import (
    FilterDigestService,
)
from tv_app.application.services.data.filter_relayer_service import (
    apply_relayer,
    shared_keys_across_sources,
)
from tv_app.application.services.data.tv_data_binding_hydrate_service import (
    hydrate_comunicado_data_bindings,
)
from tv_app.application.services.data.tv_data_param_validation_service import (
    validate_data_filters,
)
from tv_app.application.services.data.value_expression_service import (
    MExpressionError,
    scope_layer_expressions_to_route,
    validate_shared_layer_expressions,
)
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    _sanitize_playlist_data_defaults,
)


class _FakeCatalog:
    def __init__(self, routes: dict) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


def _spec(ast, *, version=1):
    return {"expression": {"version": version, "expression": ast}}


def _lit(value):
    return {"kind": "literal", "value": value}


def _model(input_params: dict | None = None, *, operation_id="get_model_only") -> dict:
    return {
        "id": "m1",
        "label": "Carteira semanal",
        "primaryInputId": "in1",
        "inputs": [
            {
                "id": "in1",
                "operationId": operation_id,
                "params": dict(input_params or {}),
            }
        ],
    }


ROUTE_BLOCK = {
    "operationId": "get_block",
    "label": "Block",
    "paramSchema": {
        "branch": {"type": "string", "optional": True},
        "dateRangePreset": {"type": "string", "optional": True},
        "segmento": {"type": "string", "optional": True},
    },
}

ROUTE_MODEL_ONLY = {
    "operationId": "get_model_only",
    "label": "Model only",
    "paramSchema": {
        "clientes_codigos": {"type": "string", "optional": True},
        "top_clientes": {"type": "integer", "optional": True},
        "segmento": {"type": "string", "optional": True},
    },
}


# --------------------------------------------------------------------- schema union


def test_collect_operation_ids_includes_model_inputs():
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "ds1",
                "type": "data_source",
                "dataBinding": {"operationId": "get_block", "params": {}},
            }
        ],
        "dataModels": [_model()],
    }
    ids = collect_native_config_operation_ids(cfg)
    assert sorted(ids) == ["get_block", "get_model_only"]


def test_hydrate_keeps_data_filter_valid_only_on_model_input_route():
    """Bug raiz: chave declarada só na rota do input do DataModel era
    stripada de dataFilters porque o union schema ignorava inputs."""
    catalog = _FakeCatalog(
        {"get_block": ROUTE_BLOCK, "get_model_only": ROUTE_MODEL_ONLY}
    )
    cfg, _summary = hydrate_comunicado_data_bindings(
        {
            "version": 5,
            "blocks": [
                {
                    "id": "ds1",
                    "type": "data_source",
                    "dataBinding": {"operationId": "get_block", "params": {}},
                }
            ],
            "dataModels": [_model()],
            "dataFilters": {"clientes_codigos": "100,200", "top_clientes": 10},
        },
        catalog=catalog,
    )
    assert cfg["dataFilters"]["clientes_codigos"] == "100,200"
    assert cfg["dataFilters"]["top_clientes"] == 10


def test_validate_data_filters_accepts_model_only_keys():
    catalog = _FakeCatalog(
        {"get_block": ROUTE_BLOCK, "get_model_only": ROUTE_MODEL_ONLY}
    )
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "ds1",
                "type": "data_source",
                "dataBinding": {"operationId": "get_block", "params": {}},
            }
        ],
        "dataModels": [_model()],
    }
    routes = [
        catalog.get_route(op)
        for op in collect_native_config_operation_ids(cfg)
    ]
    out = validate_data_filters(
        {"segmento": "varejo", "top_clientes": 20}, routes=routes
    )
    assert out["segmento"] == "varejo"
    assert out["top_clientes"] == 20


# ------------------------------------------------------- ExpressionSpec em camada


def test_shared_layer_expression_accepted_when_declared():
    spec = _spec(_lit(5))
    routes = [ROUTE_BLOCK, ROUTE_MODEL_ONLY]
    validate_shared_layer_expressions({"top_clientes": spec}, routes=routes)


def test_shared_layer_expression_rejected_when_undeclared():
    with pytest.raises(MExpressionError):
        validate_shared_layer_expressions(
            {"chave_inexistente": _spec(_lit(1))},
            routes=[ROUTE_BLOCK, ROUTE_MODEL_ONLY],
        )


def test_shared_layer_expression_rejected_when_any_declaring_route_forbids():
    route_forbidden = {
        "operationId": "r2",
        "paramSchema": {
            "top_clientes": {"type": "integer", "expressionAllowed": False}
        },
    }
    with pytest.raises(MExpressionError):
        validate_shared_layer_expressions(
            {"top_clientes": _spec(_lit(5))},
            routes=[ROUTE_MODEL_ONLY, route_forbidden],
        )


def test_shared_layer_expression_rejected_when_path_param():
    route_path = {
        "operationId": "r3",
        "paramSchema": {"ref": {"type": "string", "in": "path"}},
    }
    with pytest.raises(MExpressionError):
        validate_shared_layer_expressions(
            {"ref": _spec(_lit("x"))}, routes=[route_path]
        )


def test_scope_layer_expressions_drops_spec_where_route_disallows():
    spec = _spec(_lit(5))
    params = {"top_clientes": spec, "segmento": "varejo"}
    # Rota que declara e permite → spec mantida.
    allowed = scope_layer_expressions_to_route(params, route=ROUTE_MODEL_ONLY)
    assert allowed["top_clientes"] is spec
    assert allowed["segmento"] == "varejo"
    # Rota que não declara a chave → spec descartada; literal permanece.
    scoped = scope_layer_expressions_to_route(params, route=ROUTE_BLOCK)
    assert "top_clientes" not in scoped
    assert scoped["segmento"] == "varejo"


def test_scope_layer_expressions_drops_fixed_query_param():
    route = {
        "paramSchema": {"granularity": {"type": "string"}},
        "fixedQueryParams": {"granularity": "day"},
    }
    out = scope_layer_expressions_to_route(
        {"granularity": _spec(_lit("week"))}, route=route
    )
    assert "granularity" not in out


def test_validate_data_filters_accepts_expression_spec():
    out = validate_data_filters(
        {"top_clientes": _spec(_lit(7)), "segmento": "varejo"},
        routes=[ROUTE_BLOCK, ROUTE_MODEL_ONLY],
    )
    assert out["top_clientes"]["expression"]["version"] == 1
    assert out["segmento"] == "varejo"


def test_validate_data_filters_rejects_expression_for_unknown_key():
    with pytest.raises(MExpressionError):
        validate_data_filters(
            {"nao_existe": _spec(_lit(1))},
            routes=[ROUTE_BLOCK, ROUTE_MODEL_ONLY],
        )


# ------------------------------------------------------------ playlist dataDefaults


def test_sanitize_playlist_data_defaults_accepts_expression_spec():
    spec = _spec(_lit("2026-01-01"))
    out = _sanitize_playlist_data_defaults({"start_date": spec, "branch": "01"})
    assert out["start_date"] is spec
    assert out["branch"] == "01"


def test_sanitize_playlist_data_defaults_still_rejects_plain_object():
    with pytest.raises(PresentationWriteError):
        _sanitize_playlist_data_defaults({"branch": {"nested": "no"}})


# ------------------------------------------------------------- digest / relayer


def test_digest_counts_model_inputs_as_sources():
    native = {
        "version": 5,
        "blocks": [
            {
                "id": "ds1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_block",
                    "params": {"branch": "01"},
                },
            }
        ],
        "dataModels": [_model({"branch": "01"})],
    }
    digest = FilterDigestService.digest_slide(native, slide_id="s1")
    assert len(digest.get("sources") or []) == 2


def test_shared_keys_across_sources_includes_model_inputs():
    native = {
        "version": 5,
        "blocks": [
            {
                "id": "ds1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_block",
                    "params": {"branch": "01"},
                },
            }
        ],
        "dataModels": [_model({"branch": "01"})],
    }
    shared = shared_keys_across_sources(native)
    assert shared.get("branch") == "01"


def test_relayer_promotion_cleans_model_input_params():
    native = {
        "version": 5,
        "blocks": [
            {
                "id": "ds1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_block",
                    "params": {"branch": "01", "segmento": "a"},
                },
            }
        ],
        "dataModels": [_model({"branch": "01", "clientes_codigos": "x"})],
    }
    cfg, _defaults, promoted = apply_relayer(
        native, scope="slide", keys=None, playlist_defaults={}
    )
    assert promoted.get("branch") == "01"
    assert cfg["dataFilters"]["branch"] == "01"
    # Chave promovida sai do bloco e do input do modelo.
    assert "branch" not in cfg["blocks"][0]["dataBinding"]["params"]
    assert "branch" not in cfg["dataModels"][0]["inputs"][0]["params"]
    # Params não promovidos permanecem.
    assert cfg["dataModels"][0]["inputs"][0]["params"]["clientes_codigos"] == "x"


# --------------------------------------------------------------- merge precedence


def test_merge_precedence_programacao_tela_model_input():
    spec = _spec(_lit("x"))
    merged = merge_data_params(
        playlist_defaults={"segmento": "A"},
        slide_filters={"segmento": "B"},
        block_params={"segmento": "C"},
        input_overrides=None,
    )
    assert merged["segmento"] == "C"
    merged = merge_data_params(
        playlist_defaults={"segmento": "A"},
        slide_filters={"segmento": "B"},
        block_params={},
        input_overrides=None,
    )
    assert merged["segmento"] == "B"
    merged = merge_data_params(
        playlist_defaults={"segmento": "A", "top_clientes": spec},
        slide_filters={},
        block_params={},
        input_overrides=None,
    )
    assert merged["segmento"] == "A"
    assert merged["top_clientes"] is spec


# ----------------------------------------------------------- projeção de sources


def test_native_config_model_source_params_projects_inputs():
    cfg = {
        "version": 5,
        "dataModels": [_model({"branch": "01"})],
    }
    sources = native_config_model_source_params(cfg)
    assert len(sources) == 1
    assert sources[0]["operationId"] == "get_model_only"
    assert sources[0]["params"] == {"branch": "01"}
    assert sources[0]["modelId"] == "m1"
