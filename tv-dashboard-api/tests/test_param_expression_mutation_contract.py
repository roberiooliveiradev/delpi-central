"""ParamExpression no contrato de mutação — patch/upsert alinhados ao runtime.

O mesmo ``ExpressionSpec`` aceito pelo preview/runtime deve passar pelo schema
das ops de mutação (PREPARE), com validação semântica fail-closed
(paramSchema/expressionAllowed/fase/tipo de saída) e AST persistida intacta.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi
from tv_app.application.gpt_actions.proposal_store import (
    reset_proposal_store_for_tests,
)
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_mutation_telemetry import (
    reset_presentation_mutation_telemetry,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.value_expression_service import (
    _PARAMETER_KINDS,
)
from tv_app.domain.data_query.transform_plan import CompiledExpression
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    InMemoryIdempotencyRepository,
)


SLIDE_ID = "11111111-1111-1111-1111-111111111111"
PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"
SOURCE_ID = "rx_weg_sc_m25"

ROL_ROUTE = {
    "operationId": "get_commercial_rol_summary",
    "label": "ROL comercial — resumo",
    "paramStrategy": "date_range",
    "dateRangeKeys": ["start_date", "end_date"],
    "openEndedDateRange": False,
    "paramSchema": {
        "branch": {"type": "string", "optional": True},
        "customer_segment": {"type": "string", "optional": True},
        "start_date": {"type": "string", "format": "date", "optional": True},
        "end_date": {"type": "string", "format": "date", "optional": True},
        "path_id": {"type": "string", "in": "path"},
        "locked": {"type": "string", "expressionAllowed": False, "optional": True},
    },
    "fixedQueryParams": {"channel": "web"},
}

_SOURCE_BLOCK = {
    "id": SOURCE_ID,
    "type": "data_source",
    "frame": {"x": 10, "y": 20, "w": 30, "h": 40},
    "dataBinding": {
        "operationId": "get_commercial_rol_summary",
        "params": {
            "dateRangePreset": "this_month",
            "branch": "01",
            "customer_segment": "weg",
        },
        "displayMode": "table",
        "label": "Realizado 2025 x 2026",
    },
}

PREV_YEAR_MONTH_START_AST = {
    "kind": "call",
    "value": "Date.StartOfMonth",
    "children": [
        {
            "kind": "call",
            "value": "Date.AddMonths",
            "children": [
                {"kind": "identifier", "value": "today"},
                {"kind": "literal", "value": -12},
            ],
        }
    ],
}

PREV_YEAR_SAME_DAY_AST = {
    "kind": "call",
    "value": "Date.AddMonths",
    "children": [
        {"kind": "identifier", "value": "today"},
        {"kind": "literal", "value": -12},
    ],
}


def _expr(ast: dict[str, Any]) -> dict[str, Any]:
    return {"expression": {"version": 1, "expression": ast}}


class _FakeCatalog:
    def __init__(self, routes: dict[str, dict]) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


class _FakeRepo:
    def __init__(self) -> None:
        self.slides: dict[str, dict[str, Any]] = {
            SLIDE_ID: {
                "id": SLIDE_ID,
                "title": "Realizado 2025 x 2026",
                "durationSec": 30,
                "isActive": True,
                "nativeConfig": {
                    "version": 5,
                    "blocks": [copy.deepcopy(_SOURCE_BLOCK)],
                },
            }
        }
        self.updated: list[dict[str, Any]] = []

    def get_slide(self, slide_id, *, playlist_id=None):
        from tv_app.infrastructure.persistence.repositories.playlist_repository import (
            SlideNotFoundError,
        )

        key = str(slide_id)
        if key not in self.slides:
            raise SlideNotFoundError(key)
        return copy.deepcopy(self.slides[key])

    def get_by_id(self, playlist_id):
        return {"id": str(playlist_id), "dataDefaults": {}, "revision": 7}

    def get_revision(self, playlist_id):
        return 7


@pytest.fixture(autouse=True)
def _reset():
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()
    reset_proposal_store_for_tests()
    yield
    reset_presentation_mutation_telemetry()
    reset_proposal_store_for_tests()
    clear_presentation_ops_content_cache()


class _FakeResolution:
    def resolve_blocks(self, blocks, **kwargs):
        out = []
        for block in blocks:
            item = dict(block)
            item["resolved"] = {}
            out.append(item)
        return out

    def enrich_data_models(self, models, **kwargs):
        return {}


def _service(repo: _FakeRepo | None = None) -> PresentationPatchService:
    return PresentationPatchService(
        catalog=_FakeCatalog({"get_commercial_rol_summary": ROL_ROUTE}),
        repo=repo or _FakeRepo(),
        resolution=_FakeResolution(),
    )


def _preview(svc: PresentationPatchService, op: dict[str, Any]) -> dict[str, Any]:
    return svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [op],
        },
        user={"sub": "u1"},
        authorization="Bearer x",
    )


def _source_block(result: dict[str, Any], block_id: str = SOURCE_ID) -> dict[str, Any]:
    return next(
        block
        for block in result["nativeConfig"]["blocks"]
        if block["id"] == block_id
    )


def _patch_op() -> dict[str, Any]:
    """Mesmo shape que a VISTA tentou: unset preset + datas em expressão."""
    return {
        "op": "patch_data_source_params",
        "blockId": SOURCE_ID,
        "unset": ["dateRangePreset"],
        "set": {
            "start_date": _expr(PREV_YEAR_MONTH_START_AST),
            "end_date": _expr(PREV_YEAR_SAME_DAY_AST),
        },
    }


# ---------------------------------------------------------------------------
# Aceitação — o ParamExpression canônico passa pelo contrato de mutação
# ---------------------------------------------------------------------------


def test_patch_accepts_param_expression_and_preserves_ast():
    result = _preview(_service(), _patch_op())
    assert result["ok"] is True
    params = _source_block(result)["dataBinding"]["params"]
    assert params["start_date"] == _expr(PREV_YEAR_MONTH_START_AST)
    assert params["end_date"] == _expr(PREV_YEAR_SAME_DAY_AST)
    # AST permanece dinâmico — nunca é resolvida para literal persistido.
    assert params["start_date"] != "2025-09-01"
    assert "dateRangePreset" not in params
    assert params["branch"] == "01"
    assert params["customer_segment"] == "weg"


def test_patch_expression_minimal_diff_preserves_bindings_and_transform():
    result = _preview(_service(), _patch_op())
    block = _source_block(result)
    binding = block["dataBinding"]
    assert binding["operationId"] == "get_commercial_rol_summary"
    assert binding["label"] == "Realizado 2025 x 2026"
    assert binding["displayMode"] == "table"
    assert block["frame"] == _SOURCE_BLOCK["frame"]
    assert "resolved" not in block
    patch_report = result["sideEffects"]["dataSourceParamPatches"][0]
    assert patch_report["blockId"] == SOURCE_ID
    assert set(patch_report["changed"]["set"]) == {"start_date", "end_date"}
    assert patch_report["changed"]["unset"] == ["dateRangePreset"]


def test_patch_prepare_is_side_effect_free():
    repo = _FakeRepo()
    _preview(_service(repo), _patch_op())
    assert repo.updated == []


def test_upsert_data_source_accepts_param_expression():
    op = {
        "op": "upsert_data_source",
        "blockId": "rx_prev_year",
        "operationId": "get_commercial_rol_summary",
        "params": {
            "branch": "01",
            "start_date": _expr(PREV_YEAR_MONTH_START_AST),
            "end_date": _expr(PREV_YEAR_SAME_DAY_AST),
        },
    }
    result = _preview(_service(), op)
    assert result["ok"] is True
    params = _source_block(result, "rx_prev_year")["dataBinding"]["params"]
    assert params["start_date"] == _expr(PREV_YEAR_MONTH_START_AST)
    assert params["end_date"] == _expr(PREV_YEAR_SAME_DAY_AST)
    assert params["branch"] == "01"


def test_upsert_data_model_input_accepts_param_expression():
    op = {
        "op": "upsert_data_model",
        "model": {
            "id": "mdl_realizado_yy",
            "primaryInputId": "current",
            "inputs": [
                {
                    "id": "previous",
                    "operationId": "get_commercial_rol_summary",
                    "params": {
                        "start_date": _expr(PREV_YEAR_MONTH_START_AST),
                        "end_date": _expr(PREV_YEAR_SAME_DAY_AST),
                    },
                },
                {
                    "id": "current",
                    "operationId": "get_commercial_rol_summary",
                    "params": {"dateRangePreset": "this_month"},
                },
            ],
        },
    }
    result = _preview(_service(), op)
    assert result["ok"] is True
    models = result["nativeConfig"].get("dataModels") or []
    model = next(m for m in models if m["id"] == "mdl_realizado_yy")
    prev = next(i for i in model["inputs"] if i["id"] == "previous")
    assert prev["params"]["start_date"] == _expr(PREV_YEAR_MONTH_START_AST)
    assert prev["params"]["end_date"] == _expr(PREV_YEAR_SAME_DAY_AST)


def test_literal_scalars_still_accepted_alongside_expressions():
    op = {
        "op": "patch_data_source_params",
        "blockId": SOURCE_ID,
        "set": {
            "branch": "02",
            "customer_segment": "weg",
            "start_date": _expr(PREV_YEAR_MONTH_START_AST),
            "end_date": _expr(PREV_YEAR_SAME_DAY_AST),
        },
    }
    result = _preview(_service(), op)
    params = _source_block(result)["dataBinding"]["params"]
    assert params["branch"] == "02"
    assert params["customer_segment"] == "weg"
    assert params["start_date"] == _expr(PREV_YEAR_MONTH_START_AST)


def test_expression_ast_round_trips_through_loader():
    """O wire persistido é o mesmo AST que CompiledExpression.from_dict aceita."""
    for ast in (PREV_YEAR_MONTH_START_AST, PREV_YEAR_SAME_DAY_AST):
        node = CompiledExpression.from_dict(ast)
        assert node.to_dict() == ast


# ---------------------------------------------------------------------------
# Fail-closed — inválidos rejeitam durante PREPARE
# ---------------------------------------------------------------------------


def _expect_invalid(op: dict[str, Any]) -> None:
    with pytest.raises(PresentationPatchError):
        _preview(_service(), op)


def test_rejects_invalid_expression_version():
    op = _patch_op()
    op["set"]["start_date"] = {
        "expression": {"version": 2, "expression": PREV_YEAR_MONTH_START_AST}
    }
    _expect_invalid(op)


def test_rejects_unknown_function():
    op = _patch_op()
    op["set"]["start_date"] = _expr(
        {
            "kind": "call",
            "value": "Evil.Hack",
            "children": [{"kind": "literal", "value": 1}],
        }
    )
    _expect_invalid(op)


def test_rejects_derived_only_field_node():
    op = _patch_op()
    op["set"]["start_date"] = _expr({"kind": "field", "value": "payload.total"})
    _expect_invalid(op)


def test_rejects_wrong_output_type_for_date_param():
    op = _patch_op()
    op["set"]["start_date"] = _expr({"kind": "literal", "value": "não é data"})
    _expect_invalid(op)


def test_rejects_expression_on_expression_disabled_param():
    op = _patch_op()
    op["set"] = {"locked": _expr({"kind": "identifier", "value": "today"})}
    _expect_invalid(op)


def test_rejects_arbitrary_dict_param_value():
    op = _patch_op()
    op["set"]["start_date"] = {"foo": 1}
    _expect_invalid(op)


def test_rejects_expression_spec_with_extra_fields():
    op = _patch_op()
    op["set"]["start_date"] = {
        "expression": {"version": 1, "expression": PREV_YEAR_SAME_DAY_AST},
        "injected": True,
    }
    _expect_invalid(op)


def test_rejects_expression_on_path_param():
    op = _patch_op()
    op["set"] = {"path_id": _expr({"kind": "literal", "value": "abc"})}
    _expect_invalid(op)


def test_rejects_expression_on_virtual_param_key():
    """dateRangePreset está na allowlist de patch mas fora do paramSchema."""
    op = _patch_op()
    op["set"] = {"dateRangePreset": _expr({"kind": "identifier", "value": "today"})}
    _expect_invalid(op)


def test_upsert_data_source_rejects_invalid_expression():
    op = {
        "op": "upsert_data_source",
        "blockId": "rx_bad",
        "operationId": "get_commercial_rol_summary",
        "params": {
            "start_date": _expr({"kind": "identifier", "value": "payload.x"}),
            "end_date": _expr(PREV_YEAR_SAME_DAY_AST),
        },
    }
    _expect_invalid(op)


# ---------------------------------------------------------------------------
# Paridade de contrato — schema da ops file, OpenAPI e loader canônico
# ---------------------------------------------------------------------------


def _expression_variants() -> dict[str, dict[str, Any]]:
    ops = PresentationOpsContentService.operations()
    patch = ops["patch_data_source_params"]["inputSchema"]["properties"]["set"]
    upsert = ops["upsert_data_source"]["inputSchema"]["properties"]["params"]
    model_items = ops["upsert_data_model"]["inputSchema"]["properties"]["model"][
        "properties"
    ]["inputs"]["items"]["properties"]["params"]
    def _variant(node: dict[str, Any]) -> dict[str, Any]:
        for branch in node["additionalProperties"]["oneOf"]:
            if isinstance(branch, dict) and branch.get("type") == "object":
                return branch
        raise AssertionError("expression variant ausente")

    return {
        "patch": _variant(patch),
        "upsert": _variant(upsert),
        "model_inputs": _variant(model_items),
    }


def test_expression_variants_identical_across_ops():
    variants = _expression_variants()
    assert variants["patch"] == variants["upsert"] == variants["model_inputs"]


def test_expression_variant_kind_enum_matches_parameter_phase():
    variant = _expression_variants()["patch"]
    kinds = set(
        variant["properties"]["expression"]["properties"]["expression"][
            "properties"
        ]["kind"]["enum"]
    )
    assert kinds == set(_PARAMETER_KINDS)


def test_catalog_expressions_metadata_matches_writable_ops():
    from tv_app.application.services.data.value_expression_service import (
        expression_capability,
    )

    cap = expression_capability(transport="mcp")
    assert set(cap["writableVia"]) == {
        "patch_data_source_params.set.<param>",
        "upsert_data_source.params.<param>",
        "upsert_data_model.model.inputs[].params.<param>",
    }
    # Cada caminho anunciado tem a variante ExpressionSpec no schema da op.
    assert set(_expression_variants()) == {"patch", "upsert", "model_inputs"}


def test_openapi_projects_expression_variant_for_mutation_ops():
    doc = build_gpt_actions_openapi()
    ops_schema = doc["paths"]["/gpt-actions/v1/changes/preview"]["post"][
        "requestBody"
    ]["content"]["application/json"]["schema"]["properties"]["ops"]["items"][
        "oneOf"
    ]
    by_title = {b.get("title"): b for b in ops_schema}
    for title, prop in (
        ("patch_data_source_params", "set"),
        ("upsert_data_source", "params"),
    ):
        branches = by_title[title]["properties"][prop]["additionalProperties"][
            "oneOf"
        ]
        assert any(
            isinstance(b, dict) and b.get("type") == "object" for b in branches
        ), title


def test_runtime_validator_accepts_same_wire_shape():
    """O payload que passa no OpenAPI também passa no validador runtime."""
    from tv_app.application.services.data.presentation_nested_contract import (
        validate_operation_payload,
    )

    validate_operation_payload("patch_data_source_params", _patch_op())


# ---------------------------------------------------------------------------
# Proposal — PREPARE cria proposta sem side effects
# ---------------------------------------------------------------------------


def test_prepare_creates_proposal_with_ast_and_no_side_effects():
    repo = _FakeRepo()
    svc = _service(repo)
    writes = MagicMock()
    writes.get_revision.return_value = 7
    commit = TvGptCommitService(
        writes=writes, idempotency=InMemoryIdempotencyRepository()
    )
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True, can_read=True)
    access.actor_id.return_value = "actor-1"
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=commit, access=access, patch=svc
    )
    result = dispatch.preview_change(
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1"),
        target={"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
        ops=[_patch_op()],
        catalog_version=PresentationOpsContentService.catalog_version(),
        authorization=None,
        idempotency_key=f"expr-prepare-{uuid4()}",
    )
    assert result.get("proposal_handle")
    proposal = result.get("proposal") or {}
    assert proposal.get("base_revision") == 7
    assert result.get("canCommit") is True
    assert result.get("persisted") is False
    # Candidato preserva AST (não resolve para data literal).
    from tv_app.application.gpt_actions.proposal_store import (
        get_proposal_store,
        parse_proposal_handle,
    )

    stored = get_proposal_store().get(
        parse_proposal_handle(result["proposal_handle"])
    )
    assert stored is not None
    cfg = (stored.meta or {}).get("nativeConfig") or {}
    params = next(
        b["dataBinding"]["params"]
        for b in cfg.get("blocks", [])
        if b.get("id") == SOURCE_ID
    )
    assert params["start_date"] == _expr(PREV_YEAR_MONTH_START_AST)
    assert params["end_date"] == _expr(PREV_YEAR_SAME_DAY_AST)
    assert repo.updated == []


# ---------------------------------------------------------------------------
# Integridade de proposta — AST sobrevive o round-trip da projeção pública
# ---------------------------------------------------------------------------


def _dispatch_with_service(
    svc: PresentationPatchService,
) -> GptActionsDispatchService:
    writes = MagicMock()
    writes.get_revision.return_value = 7
    commit = TvGptCommitService(
        writes=writes, idempotency=InMemoryIdempotencyRepository()
    )
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True, can_read=True)
    access.actor_id.return_value = "actor-1"
    return GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=commit, access=access, patch=svc
    )


def _prepare(
    svc: PresentationPatchService, op: dict[str, Any]
) -> dict[str, Any]:
    return _dispatch_with_service(svc).preview_change(
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1"),
        target={"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
        ops=[op],
        catalog_version=PresentationOpsContentService.catalog_version(),
        authorization=None,
        idempotency_key=f"expr-prepare-{uuid4()}",
    )


def _stored_proposal(handle: str):
    from tv_app.application.gpt_actions.proposal_store import (
        get_proposal_store,
        parse_proposal_handle,
    )

    return get_proposal_store().get(parse_proposal_handle(handle))


ROUND_TRIP_ASTS = {
    "identifier_today": {"kind": "identifier", "value": "today"},
    "identifier_now": {"kind": "identifier", "value": "now"},
    "identifier_param": {"kind": "identifier", "value": "param.branch"},
    "literal_int": {"kind": "literal", "value": -12},
    "literal_str": {"kind": "literal", "value": "abc"},
    "literal_bool": {"kind": "literal", "value": True},
    "literal_null": {"kind": "literal", "value": None},
    "nested_call": PREV_YEAR_MONTH_START_AST,
    "binary": {
        "kind": "binary",
        "value": "*",
        "children": [
            {
                "kind": "binary",
                "value": "-",
                "children": [
                    {
                        "kind": "binary",
                        "value": "/",
                        "children": [
                            {"kind": "literal", "value": 120},
                            {"kind": "literal", "value": 100},
                        ],
                    },
                    {"kind": "literal", "value": 1},
                ],
            },
            {"kind": "literal", "value": 100},
        ],
    },
    "unary": {
        "kind": "unary",
        "value": "-",
        "children": [{"kind": "literal", "value": 12}],
    },
    "if": {
        "kind": "if",
        "children": [
            {"kind": "literal", "value": True},
            {"kind": "literal", "value": 1},
            {"kind": "literal", "value": 2},
        ],
    },
    "list": {
        "kind": "list",
        "children": [
            {"kind": "literal", "value": 1},
            {"kind": "literal", "value": 2},
        ],
    },
}


# Casos avaliáveis de ponta a ponta (coerção ao tipo do param é válida).
ROUND_TRIP_EVALUABLE = {
    "identifier_today": ("start_date", {"kind": "identifier", "value": "today"}),
    "identifier_now": ("start_date", {"kind": "identifier", "value": "now"}),
    "identifier_param": (
        "customer_segment",
        {"kind": "identifier", "value": "param.branch"},
    ),
    "literal_int": ("customer_segment", {"kind": "literal", "value": -12}),
    "literal_str": ("customer_segment", {"kind": "literal", "value": "abc"}),
    "literal_bool": ("customer_segment", {"kind": "literal", "value": True}),
    "nested_call": ("start_date", PREV_YEAR_MONTH_START_AST),
    "binary": ("customer_segment", ROUND_TRIP_ASTS["binary"]),
    "unary": ("customer_segment", ROUND_TRIP_ASTS["unary"]),
    "if": ("customer_segment", ROUND_TRIP_ASTS["if"]),
}


@pytest.mark.parametrize("kind", sorted(ROUND_TRIP_EVALUABLE))
def test_proposal_exact_change_preserves_ast_nodes(kind: str):
    """input == orderedOps == proposal.exact_change == stored proposal."""
    param, ast = ROUND_TRIP_EVALUABLE[kind]
    op = {
        "op": "patch_data_source_params",
        "blockId": SOURCE_ID,
        "set": {param: _expr(ast)},
    }
    result = _prepare(_service(), op)

    public_ops = result["proposal"]["exact_change"]["ops"]
    assert public_ops[0]["set"][param] == _expr(ast)
    ordered = result["orderedOps"][0]["set"][param]
    assert ordered == _expr(ast)
    stored = _stored_proposal(result["proposal_handle"])
    assert stored is not None
    stored_ops = stored.exact_change["ops"]
    assert stored_ops[0]["set"][param] == _expr(ast)


@pytest.mark.parametrize("kind", sorted(ROUND_TRIP_ASTS))
def test_actions_projection_preserves_ast_node(kind: str):
    """strip_heavy_mutation_blobs não pode corromper nós AST em profundidade."""
    from tv_app.application.gpt_actions.response_compact import (
        project_mutation_actions_payload,
    )

    payload = {
        "proposal": {
            "exact_change": {
                "ops": [{"set": {"start_date": _expr(ROUND_TRIP_ASTS[kind])}}]
            }
        }
    }
    out = project_mutation_actions_payload(payload)
    node = out["proposal"]["exact_change"]["ops"][0]["set"]["start_date"]
    assert node == _expr(ROUND_TRIP_ASTS[kind])


def test_prepare_patch_expression_exact_change_equals_ordered_ops():
    """Caso real da VISTA: patch com datas em expressão + unset preset."""
    result = _prepare(_service(), _patch_op())
    public_op = result["proposal"]["exact_change"]["ops"][0]
    ordered_op = result["orderedOps"][0]
    assert public_op["set"] == ordered_op["set"] == _patch_op()["set"]
    assert public_op["unset"] == ordered_op["unset"] == ["dateRangePreset"]
