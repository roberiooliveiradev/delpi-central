"""Input como variável reutilizável do slide (``input.<key>``).

Cobre contrato persistido, validação do nativeConfig candidato, motor de
expressões, contexto único do slide (precedência override → default),
override público slide-scoped, PresentationMutation (mesmo lote, sem ordem)
e paridade data_source × DataModel com o aceite temporal da Carteira Semanal.
"""

from __future__ import annotations

import copy
from datetime import date, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from tv_app.application.services import comunicado_input_contract_service as contract
from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.comunicado_native_config_sanitize import (
    sanitize_comunicado_config,
)
from tv_app.application.services.data import value_expression_service as ves
from tv_app.application.services.data.m_query.m_expression_interpreter import MExpressionError
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_mutation_telemetry import (
    reset_presentation_mutation_telemetry,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.tv_data_config_validation_service import (
    TvDataConfigValidationService,
)
from tv_app.application.services.data.value_expression_service import (
    InputVariableScope,
    build_evaluation_context,
    resolve_param_expressions,
    validate_expression_param_value,
    validate_shared_layer_expressions,
)
from tv_app.application.services.public_filter_overrides_service import (
    allowlist_filter_overrides,
    parse_filter_overrides_query,
    slide_input_overrides,
)
from tv_app.application.services.presentation_payload_service import (
    PresentationPayloadService,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)

ROUTE_OP = "get_commercial_rol_summary"
ROUTE = {
    "operationId": ROUTE_OP,
    "label": "ROL",
    "paramStrategy": "date_range",
    "dateRangeKeys": ["start_date", "end_date"],
    "paramSchema": {
        "branch": {"type": "string", "optional": True},
        "start_date": {"type": "string", "format": "date", "optional": True},
        "end_date": {"type": "string", "format": "date", "optional": True},
        "locked": {"type": "string", "expressionAllowed": False, "optional": True},
        "limit": {"type": "integer", "optional": True},
    },
}

MEETING_DAY_SCHEMA = {
    "type": "integer",
    "enum": [0, 1, 2, 3, 4],
    "enumLabels": {
        "0": "Segunda-feira",
        "1": "Terça-feira",
        "2": "Quarta-feira",
        "3": "Quinta-feira",
        "4": "Sexta-feira",
    },
}


def _lit(value):
    return {"kind": "literal", "value": value}


def _ident(name):
    return {"kind": "identifier", "value": name}


def _call(name, *children):
    return {"kind": "call", "value": name, "children": list(children)}


def _spec(ast):
    return {"expression": {"version": 1, "expression": ast}}


def _is_meeting_day():
    return {
        "kind": "binary",
        "value": "=",
        "children": [
            _call("Date.DayOfWeek", _ident("today"), _ident("Monday")),
            _ident("input.meeting_day"),
        ],
    }


# Regra da Carteira: dia da reunião → semana anterior fechada; senão semana corrente até hoje.
CARTEIRA_START = _spec(
    {
        "kind": "if",
        "children": [
            _is_meeting_day(),
            _call(
                "Date.StartOfWeek",
                _call("Date.AddWeeks", _ident("today"), _lit(-1)),
                _ident("Monday"),
            ),
            _call("Date.StartOfWeek", _ident("today"), _ident("Monday")),
        ],
    }
)
CARTEIRA_END = _spec(
    {
        "kind": "if",
        "children": [
            _is_meeting_day(),
            _call(
                "Date.AddDays",
                _call("Date.StartOfWeek", _ident("today"), _ident("Monday")),
                _lit(-3),
            ),
            _ident("today"),
        ],
    }
)


def _variable_block(block_id="in_md", **input_patch) -> dict[str, Any]:
    input_cfg = {
        "binding": {"kind": "variable", "key": "meeting_day"},
        "valueSchema": copy.deepcopy(MEETING_DAY_SCHEMA),
        "label": "Dia de referência da reunião",
        "defaultValue": 0,
    }
    input_cfg.update(input_patch)
    return {"id": block_id, "type": "input", "frame": {"x": 1, "y": 1, "w": 10, "h": 5}, "input": input_cfg}


def _scope(value=0, **kwargs) -> InputVariableScope:
    return contract.build_input_variable_scope(
        [_variable_block(defaultValue=value)], **kwargs
    )


def _ctx(day: date):
    return build_evaluation_context(today=day, now=datetime(day.year, day.month, day.day, 12))


# ---------------------------------------------------------------------------
# Contrato persistido / validação do bloco
# ---------------------------------------------------------------------------


class TestInputContract:
    def test_valid_variable_declaration(self):
        declaration = contract.read_input_variable(_variable_block())
        assert declaration is not None
        assert declaration.key == "meeting_day"
        assert declaration.value_schema == MEETING_DAY_SCHEMA
        assert declaration.default_value == 0

    def test_legacy_input_is_not_validated_by_new_contract(self):
        legacy = {"id": "in_b", "type": "input", "input": {"paramKey": "branch", "defaultValue": "01"}}
        assert contract.read_input_variable(legacy) is None
        assert contract.collect_input_variables([legacy]) == ([], [])

    @pytest.mark.parametrize(
        ("patch", "code"),
        [
            ({"binding": {"kind": "variable", "key": "1bad"}}, "input.variable_key_invalid"),
            ({"binding": {"kind": "variable", "key": "has space"}}, "input.variable_key_invalid"),
            ({"binding": {"kind": "routeParam", "key": "branch"}}, "input.binding_invalid"),
            ({"binding": {"kind": "variable", "key": "md", "extra": 1}}, "input.binding_invalid"),
            ({"paramKey": "branch"}, "input.binding_ambiguous"),
            ({"targetScope": "sources"}, "input.binding_ambiguous"),
            ({"targetSourceIds": ["src_1"]}, "input.binding_ambiguous"),
            ({"valueSchema": None}, "input.value_schema_invalid"),
            ({"valueSchema": {"type": "array"}}, "input.value_schema_invalid"),
            ({"valueSchema": {"type": "integer", "format": "date"}}, "input.value_schema_invalid"),
            ({"valueSchema": {"type": "string", "format": "date-time"}}, "input.value_schema_invalid"),
            ({"valueSchema": {"type": "integer", "enum": ["0", "1"]}}, "input.value_schema_invalid"),
            ({"valueSchema": {"type": "integer", "enum": [0, 0]}}, "input.value_schema_invalid"),
            ({"valueSchema": {"type": "boolean", "enum": [True]}}, "input.value_schema_invalid"),
            ({"valueSchema": {"type": "integer", "enumLabels": {"0": "x"}}}, "input.value_schema_invalid"),
            (
                {"valueSchema": {"type": "integer", "enum": [0], "enumLabels": {"9": "x"}}},
                "input.value_schema_invalid",
            ),
            ({"valueSchema": {"type": "integer", "multiple": True}}, "input.value_schema_invalid"),
            ({"defaultValue": 9}, "input.value_invalid"),
            ({"defaultValue": "segunda"}, "input.value_invalid"),
            ({"defaultValue": True}, "input.value_invalid"),
        ],
    )
    def test_invalid_shapes_fail_closed(self, patch, code):
        with pytest.raises(contract.InputContractError) as exc:
            contract.read_input_variable(_variable_block(**patch))
        assert exc.value.code == code

    def test_date_variable_uses_param_schema_shape(self):
        block = _variable_block(
            binding={"kind": "variable", "key": "reference_date"},
            valueSchema={"type": "string", "format": "date"},
            defaultValue="2026-10-05",
        )
        declaration = contract.read_input_variable(block)
        assert declaration is not None
        assert declaration.value_schema == {"type": "string", "format": "date"}
        with pytest.raises(contract.InputContractError):
            contract.read_input_variable({**block, "input": {**block["input"], "defaultValue": "05/10/2026"}})

    def test_duplicate_key_in_slide_is_rejected(self):
        declarations, issues = contract.collect_input_variables(
            [_variable_block("in_a"), _variable_block("in_b")]
        )
        assert [item.block_id for item in declarations] == ["in_a"]
        assert issues[0]["code"] == "input.variable_key_duplicate"

    def test_sanitize_strips_runtime_decoration(self):
        block = _variable_block()
        block["input"]["resolvedField"] = {"type": "integer"}
        block["input"]["paramAvailable"] = True
        cleaned = sanitize_comunicado_config({"blocks": [block]})["blocks"][0]["input"]
        assert "resolvedField" not in cleaned and "paramAvailable" not in cleaned
        assert cleaned["binding"] == {"kind": "variable", "key": "meeting_day"}
        assert cleaned["valueSchema"] == MEETING_DAY_SCHEMA


# ---------------------------------------------------------------------------
# Contexto do slide — precedência override → default → ausente
# ---------------------------------------------------------------------------


class TestInputScope:
    def test_default_value_is_used_without_override(self):
        scope = _scope(0)
        assert scope.values == {"meeting_day": 0}
        assert scope.schemas["meeting_day"] == MEETING_DAY_SCHEMA

    def test_valid_session_override_wins_and_is_coerced(self):
        scope = _scope(0, overrides_by_input_id={"in_md": "2"})
        assert scope.values == {"meeting_day": 2}

    def test_invalid_override_marks_invalid_without_default_fallback(self):
        scope = _scope(0, overrides_by_input_id={"in_md": 7})
        assert "meeting_day" not in scope.values
        assert scope.invalid == {"meeting_day": "input.value_invalid"}

    def test_explicit_null_is_not_absence(self):
        scope = _scope(0, overrides_by_input_id={"in_md": None})
        assert "meeting_day" not in scope.values
        assert scope.invalid == {}

    def test_override_for_unknown_block_is_ignored(self):
        scope = _scope(0, overrides_by_input_id={"other": 3})
        assert scope.values == {"meeting_day": 0}

    def test_duplicate_keys_are_excluded_at_runtime(self):
        scope = contract.build_input_variable_scope(
            [_variable_block("in_a"), _variable_block("in_b", defaultValue=2)]
        )
        assert scope.schemas == {} and scope.values == {}


# ---------------------------------------------------------------------------
# Motor de expressões
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("today", "meeting_day", "expected"),
    [
        (date(2026, 10, 5), 0, ("2026-09-28", "2026-10-02")),
        (date(2026, 10, 7), 0, ("2026-10-05", "2026-10-07")),
        (date(2026, 10, 7), 2, ("2026-09-28", "2026-10-02")),
        (date(2026, 10, 6), 2, ("2026-10-05", "2026-10-06")),
    ],
)
def test_carteira_temporal_acceptance_engine(today, meeting_day, expected):
    out = resolve_param_expressions(
        {"start_date": CARTEIRA_START, "end_date": CARTEIRA_END, "branch": "01"},
        route=ROUTE,
        context=_ctx(today),
        input_scope=_scope(meeting_day),
    )
    assert out.error is None
    assert (out.params["start_date"], out.params["end_date"]) == expected
    assert not any(str(key).startswith("input") for key in out.params)
    assert out.params["branch"] == "01"


class TestEngine:
    def test_input_ref_without_scope_is_rejected(self):
        out = resolve_param_expressions(
            {"start_date": CARTEIRA_START}, route=ROUTE, context=_ctx(date(2026, 10, 5))
        )
        assert out.error is not None
        assert out.error["code"] == "m.expression_reference_not_allowed"

    def test_undeclared_key_is_rejected(self):
        spec = _spec(_call("Date.AddDays", _ident("today"), _ident("input.other")))
        out = resolve_param_expressions(
            {"start_date": spec}, route=ROUTE, context=_ctx(date(2026, 10, 5)), input_scope=_scope()
        )
        assert out.error["code"] == "m.expression_reference_not_allowed"

    def test_missing_value_fails_closed(self):
        scope = contract.build_input_variable_scope([_variable_block(defaultValue=None)])
        out = resolve_param_expressions(
            {"start_date": CARTEIRA_START}, route=ROUTE, context=_ctx(date(2026, 10, 5)), input_scope=scope
        )
        assert out.error["code"] == "m.input_value_missing"

    def test_invalid_override_fails_closed(self):
        out = resolve_param_expressions(
            {"start_date": CARTEIRA_START},
            route=ROUTE,
            context=_ctx(date(2026, 10, 5)),
            input_scope=_scope(0, overrides_by_input_id={"in_md": "segunda"}),
        )
        assert out.error["code"] == "m.input_value_invalid"

    def test_type_from_value_schema_is_enforced(self):
        flag_scope = contract.build_input_variable_scope(
            [
                _variable_block(
                    binding={"kind": "variable", "key": "flag"},
                    valueSchema={"type": "boolean"},
                    defaultValue=True,
                )
            ]
        )
        spec = _spec(_call("Date.AddDays", _ident("today"), _ident("input.flag")))
        with pytest.raises(MExpressionError):
            validate_expression_param_value("start_date", spec, route=ROUTE, input_scope=flag_scope)

    def test_date_variable_evaluates_as_date(self):
        scope = contract.build_input_variable_scope(
            [
                _variable_block(
                    binding={"kind": "variable", "key": "reference_date"},
                    valueSchema={"type": "string", "format": "date"},
                    defaultValue="2026-10-05",
                )
            ]
        )
        spec = _spec(_call("Date.AddDays", _ident("input.reference_date"), _lit(-7)))
        out = resolve_param_expressions(
            {"start_date": spec}, route=ROUTE, context=_ctx(date(2026, 10, 7)), input_scope=scope
        )
        assert out.error is None
        assert out.params["start_date"] == "2026-09-28"

    def test_param_refs_and_expression_allowed_still_apply(self):
        spec = _spec(_ident("input.meeting_day"))
        with pytest.raises(MExpressionError) as exc:
            validate_expression_param_value("locked", spec, route=ROUTE, input_scope=_scope())
        assert exc.value.code == "m.expression_param_not_allowed"
        with pytest.raises(MExpressionError):
            validate_expression_param_value("nope", spec, route=ROUTE, input_scope=_scope())

    def test_integer_param_accepts_integer_variable(self):
        out = resolve_param_expressions(
            {"limit": _spec(_ident("input.meeting_day"))},
            route=ROUTE,
            context=_ctx(date(2026, 10, 7)),
            input_scope=_scope(3),
        )
        assert out.error is None and out.params["limit"] == 3

    def test_defer_accepts_undeclared_only_when_requested(self):
        spec = _spec(_call("Date.AddDays", _ident("today"), _ident("input.later")))
        with pytest.raises(MExpressionError):
            validate_expression_param_value("start_date", spec, route=ROUTE)
        validate_expression_param_value("start_date", spec, route=ROUTE, defer_undeclared_inputs=True)

    def test_playlist_layer_never_accepts_input_refs(self):
        with pytest.raises(MExpressionError):
            validate_shared_layer_expressions({"start_date": CARTEIRA_START}, routes=[ROUTE])
        validate_shared_layer_expressions(
            {"start_date": CARTEIRA_START}, routes=[ROUTE], input_scope=_scope()
        )


# ---------------------------------------------------------------------------
# Validação de escrita sobre o nativeConfig candidato
# ---------------------------------------------------------------------------


class _Catalog:
    def get_route(self, operation_id):
        return ROUTE if operation_id == ROUTE_OP else None

    def is_allowed(self, operation_id):
        return operation_id == ROUTE_OP


def _source(block_id="src_sc", params=None):
    return {
        "id": block_id,
        "type": "data_source",
        "frame": {"x": 1, "y": 10, "w": 30, "h": 20},
        "dataBinding": {
            "operationId": ROUTE_OP,
            "params": params
            if params is not None
            else {"branch": "01", "start_date": CARTEIRA_START, "end_date": CARTEIRA_END},
            "displayMode": "table",
        },
    }


def _issues(cfg):
    result = TvDataConfigValidationService(catalog=_Catalog()).validate(
        cfg, user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    )
    return [issue.get("code") for issue in result["issues"]]


class TestCandidateValidation:
    def test_declared_variable_and_expression_are_valid(self):
        assert _issues({"version": 5, "blocks": [_variable_block(), _source()]}) == []

    def test_reference_to_undeclared_input_fails(self):
        codes = _issues({"version": 5, "blocks": [_source()]})
        assert "input.reference_undeclared" in codes

    def test_invalid_input_shape_fails_validation(self):
        codes = _issues({"version": 5, "blocks": [_variable_block(paramKey="branch"), _source()]})
        assert "input.binding_ambiguous" in codes

    def test_duplicate_key_fails_validation(self):
        codes = _issues(
            {"version": 5, "blocks": [_variable_block("a"), _variable_block("b"), _source()]}
        )
        assert "input.variable_key_duplicate" in codes

    def test_type_mismatch_against_value_schema_fails(self):
        flag = _variable_block(valueSchema={"type": "boolean"}, defaultValue=True)
        mistyped = _spec(_call("Date.AddDays", _ident("today"), _ident("input.meeting_day")))
        codes = _issues(
            {"version": 5, "blocks": [flag, _source(params={"start_date": mistyped})]}
        )
        assert "expression.type_mismatch" in codes

    def test_data_model_input_reference_is_validated(self):
        model = {
            "id": "cs_period_model",
            "primaryInputId": "period_src",
            "inputs": [
                {
                    "id": "period_src",
                    "operationId": ROUTE_OP,
                    "params": {"start_date": CARTEIRA_START, "end_date": CARTEIRA_END},
                }
            ],
        }
        assert _issues({"version": 5, "blocks": [_variable_block()], "dataModels": [model]}) == []
        assert "input.reference_undeclared" in _issues(
            {"version": 5, "blocks": [], "dataModels": [model]}
        )

    def test_slide_filters_may_reference_declared_variable(self):
        cfg = {
            "version": 5,
            "blocks": [_variable_block(), _source(params={"branch": "01"})],
            "dataFilters": {"start_date": CARTEIRA_START},
        }
        assert _issues(cfg) == []
        cfg["blocks"] = [_source(params={"branch": "01"})]
        assert "input.reference_undeclared" in _issues(cfg)

    def test_legacy_slide_unchanged(self):
        legacy = {"id": "in_b", "type": "input", "input": {"paramKey": "branch", "defaultValue": "01"}}
        assert _issues({"version": 5, "blocks": [legacy, _source(params={"branch": "01"})]}) == []


# ---------------------------------------------------------------------------
# PresentationMutation — mesmo lote cria input + expressão, sem ordem entre ops
# ---------------------------------------------------------------------------

SLIDE_ID = "11111111-1111-1111-1111-111111111111"
PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"


class _Repo:
    def __init__(self, blocks, data_models=None):
        native_config: dict[str, Any] = {"version": 5, "blocks": copy.deepcopy(blocks)}
        if data_models is not None:
            native_config["dataModels"] = copy.deepcopy(data_models)
        self.slides = {
            SLIDE_ID: {
                "id": SLIDE_ID,
                "title": "Carteira Semanal",
                "durationSec": 30,
                "isActive": True,
                "nativeConfig": native_config,
            }
        }
        self.updated: list[dict[str, Any]] = []

    def get_slide(self, slide_id, *, playlist_id=None):
        return copy.deepcopy(self.slides[str(slide_id)])

    def get_by_id(self, playlist_id):
        return {"id": str(playlist_id), "dataDefaults": {}, "revision": 7}

    def get_revision(self, playlist_id):
        return 7


class _Resolution:
    def resolve_blocks(self, blocks, **kwargs):
        return [dict(block, resolved={}) for block in blocks]

    def enrich_data_models(self, models, **kwargs):
        return {}


@pytest.fixture
def _mutation_env():
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()
    yield
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()


def _preview(blocks, ops, data_models=None):
    service = PresentationPatchService(
        catalog=_Catalog(), repo=_Repo(blocks, data_models), resolution=_Resolution()
    )
    return service.preview(
        {"target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID}, "ops": ops},
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
        authorization="Bearer x",
    )


_UPSERT_VARIABLE = {"op": "upsert_block", "block": {k: v for k, v in _variable_block().items() if k != "frame"} | {"frame": {"x": 1, "y": 1, "w": 10, "h": 5}}}
_PATCH_EXPRESSION = {
    "op": "patch_data_source_params",
    "blockId": "src_sc",
    "set": {"start_date": CARTEIRA_START, "end_date": CARTEIRA_END},
}


@pytest.mark.usefixtures("_mutation_env")
class TestMutationBatch:
    def test_same_batch_input_then_expression(self):
        result = _preview([_source(params={"branch": "01"})], [_UPSERT_VARIABLE, _PATCH_EXPRESSION])
        assert result["ok"] is True
        blocks = {block["id"]: block for block in result["nativeConfig"]["blocks"]}
        assert blocks["in_md"]["input"]["binding"] == {"kind": "variable", "key": "meeting_day"}
        assert blocks["in_md"]["input"]["valueSchema"] == MEETING_DAY_SCHEMA
        assert blocks["src_sc"]["dataBinding"]["params"]["start_date"] == CARTEIRA_START

    def test_same_batch_expression_then_input(self):
        result = _preview([_source(params={"branch": "01"})], [_PATCH_EXPRESSION, _UPSERT_VARIABLE])
        assert result["ok"] is True

    def test_expression_without_input_fails(self):
        with pytest.raises(PresentationPatchError, match="input.meeting_day"):
            _preview([_source(params={"branch": "01"})], [_PATCH_EXPRESSION])

    def test_same_batch_removing_referenced_input_fails(self):
        with pytest.raises(PresentationPatchError, match="input.meeting_day"):
            _preview(
                [_variable_block(), _source()],
                [{"op": "delete_block", "blockId": "in_md"}],
            )

    def test_upsert_invalid_variable_fails(self):
        bad = copy.deepcopy(_UPSERT_VARIABLE)
        bad["block"]["input"]["defaultValue"] = 9
        with pytest.raises(PresentationPatchError, match="tipo declarado"):
            _preview([_source(params={"branch": "01"})], [bad])


# ---------------------------------------------------------------------------
# Override público slide-scoped
# ---------------------------------------------------------------------------


class TestPublicOverrides:
    def test_parse_keeps_by_slide_id_and_legacy(self):
        parsed = parse_filter_overrides_query(
            '{"slide":{"branch":"02"},"bySlideId":{"A":{"byInputId":{"in_md":2,"bad":{"x":1}}}}}'
        )
        assert parsed["slide"] == {"branch": "02"}
        assert parsed["bySlideId"] == {"A": {"in_md": 2}}

    def test_legacy_parse_unchanged(self):
        assert parse_filter_overrides_query('{"slide":{"branch":"02"}}') == {
            "slide": {"branch": "02"},
            "bySourceId": {},
        }

    def test_override_reaches_only_its_slide_even_with_same_key(self):
        parsed = parse_filter_overrides_query('{"bySlideId":{"A":{"byInputId":{"in_md":2}}}}')
        slide_a_blocks = [_variable_block("in_md")]
        slide_b_blocks = [_variable_block("in_md")]
        assert slide_input_overrides(parsed, slide_id="A", slide_blocks=slide_a_blocks) == {"in_md": 2}
        assert slide_input_overrides(parsed, slide_id="B", slide_blocks=slide_b_blocks) == {}

    def test_override_for_non_variable_block_is_dropped(self):
        parsed = parse_filter_overrides_query('{"bySlideId":{"A":{"byInputId":{"in_b":"02","src":1}}}}')
        blocks = [
            {"id": "in_b", "type": "input", "input": {"paramKey": "branch"}},
            _source("src"),
        ]
        assert slide_input_overrides(parsed, slide_id="A", slide_blocks=blocks) == {}

    def test_variable_overrides_never_enter_legacy_allowlist(self):
        parsed = parse_filter_overrides_query('{"bySlideId":{"A":{"byInputId":{"in_md":2}}}}')
        safe = allowlist_filter_overrides(parsed, allowed_slide_keys=set(), allowed_by_source={})
        assert safe is None

    def test_payload_service_merges_only_own_slice(self):
        parsed = parse_filter_overrides_query(
            '{"slide":{"branch":"02"},"bySlideId":{"A":{"byInputId":{"in_md":2}}}}'
        )
        safe = {"slide": {"branch": "02"}, "bySourceId": {}}
        slide_a = {"id": "A", "nativeConfig": {"blocks": [_variable_block("in_md")]}}
        slide_b = {"id": "B", "nativeConfig": {"blocks": [_variable_block("in_md")]}}
        merged_a = PresentationPayloadService._slide_filter_overrides(safe, parsed, slide_a)
        merged_b = PresentationPayloadService._slide_filter_overrides(safe, parsed, slide_b)
        assert merged_a == {"slide": {"branch": "02"}, "bySourceId": {}, "byInputId": {"in_md": 2}}
        assert merged_b is safe


# ---------------------------------------------------------------------------
# Paridade data_source × DataModel no mesmo request (Carteira)
# ---------------------------------------------------------------------------


@pytest.fixture
def _clear_cache():
    reset_comunicado_data_block_cache()
    yield
    reset_comunicado_data_block_cache()


def _frozen_today(monkeypatch, day: date):
    monkeypatch.setattr(ves, "calendar_today", lambda today=None, tz_name=None: today or day)


def _payload():
    return {
        "meta": {"shape": "scalar", "entity": "commercial_rol_summary"},
        "data": {"branch": "01", "rol": 1.0},
        "route": {"label": "ROL", "valueFields": ["rol"]},
    }


def _recording_gateway():
    gateway = MagicMock()
    calls: list[tuple[str, dict]] = []

    def _fetch(operation_id, params=None, **kwargs):
        calls.append((operation_id, dict(params or {})))
        return _payload()

    gateway.fetch_by_operation_id.side_effect = _fetch
    gateway.calls = calls
    return gateway


def _carteira_cfg():
    sources = [
        _source(block_id, params={"branch": branch, "start_date": CARTEIRA_START, "end_date": CARTEIRA_END})
        for block_id, branch in (
            ("cs_sc_summary", "01"),
            ("cs_es_summary", "02"),
            ("cs_sc_customers", "01"),
            ("cs_es_customers", "02"),
        )
    ]
    model = {
        "id": "cs_period_model",
        "primaryInputId": "period_src",
        "inputs": [
            {
                "id": "period_src",
                "operationId": ROUTE_OP,
                "params": {"branch": "01", "start_date": CARTEIRA_START, "end_date": CARTEIRA_END},
            }
        ],
    }
    return {"version": 5, "blocks": [_variable_block(), *sources], "dataModels": [model]}


@pytest.mark.usefixtures("_clear_cache")
@pytest.mark.parametrize(
    ("today", "override", "expected"),
    [
        (date(2026, 10, 5), None, ("2026-09-28", "2026-10-02")),
        (date(2026, 10, 7), None, ("2026-10-05", "2026-10-07")),
        (date(2026, 10, 7), 2, ("2026-09-28", "2026-10-02")),
        (date(2026, 10, 6), 2, ("2026-10-05", "2026-10-06")),
    ],
)
def test_carteira_parity_all_consumers(monkeypatch, today, override, expected):
    _frozen_today(monkeypatch, today)
    gateway = _recording_gateway()
    enrichment = ComunicadoDataEnrichmentService(catalog=TvDataRouteCatalogService(), gateway=gateway)
    cfg = _carteira_cfg()
    filter_overrides = None if override is None else {"slide": {}, "bySourceId": {}, "byInputId": {"in_md": override}}
    enriched = enrichment.enrich_blocks(
        cfg["blocks"], cfg=cfg, authorization=None, filter_overrides=filter_overrides
    )
    periods = {(params.get("start_date"), params.get("end_date")) for _op, params in gateway.calls}
    assert periods == {expected}
    # 4 data_source (2 combinações únicas de params) + DataModel com a mesma combinação da SC.
    assert gateway.calls, "nenhum fetch executado"
    assert all("meeting_day" not in params and not any(k.startswith("input") for k in params) for _op, params in gateway.calls)
    by_id = {block["id"]: block for block in enriched}
    for source_id in ("cs_sc_summary", "cs_es_summary", "cs_sc_customers", "cs_es_customers"):
        assert not by_id[source_id]["resolved"].get("error"), by_id[source_id]["resolved"]
    decorated = by_id["in_md"]["input"]
    assert decorated["paramAvailable"] is True
    assert decorated["resolvedField"]["enumLabels"]["2"] == "Quarta-feira"


@pytest.mark.usefixtures("_clear_cache")
def test_data_model_resolves_same_variable_as_data_source(monkeypatch):
    _frozen_today(monkeypatch, date(2026, 10, 7))
    gateway = _recording_gateway()
    enrichment = ComunicadoDataEnrichmentService(catalog=TvDataRouteCatalogService(), gateway=gateway)
    cfg = _carteira_cfg()
    cfg["blocks"] = [_variable_block()]
    resolved = enrichment.enrich_data_models(
        cfg["dataModels"], cfg=cfg, authorization=None
    )
    assert not resolved["cs_period_model"].get("error"), resolved["cs_period_model"]
    assert [(p["start_date"], p["end_date"]) for _op, p in gateway.calls] == [("2026-10-05", "2026-10-07")]


@pytest.mark.usefixtures("_clear_cache")
def test_invalid_override_blocks_fetch_fail_closed(monkeypatch):
    _frozen_today(monkeypatch, date(2026, 10, 7))
    gateway = _recording_gateway()
    enrichment = ComunicadoDataEnrichmentService(catalog=TvDataRouteCatalogService(), gateway=gateway)
    cfg = _carteira_cfg()
    enriched = enrichment.enrich_blocks(
        cfg["blocks"],
        cfg=cfg,
        authorization=None,
        filter_overrides={"slide": {}, "bySourceId": {}, "byInputId": {"in_md": 9}},
    )
    assert gateway.calls == []
    source = next(block for block in enriched if block["id"] == "cs_sc_summary")
    assert source["resolved"].get("error")
    trace = source["resolved"].get("paramExpressions") or []
    assert any((entry.get("error") or {}).get("code") == "m.input_value_invalid" for entry in trace)


@pytest.mark.usefixtures("_clear_cache")
def test_slide_b_does_not_receive_slide_a_override(monkeypatch):
    """Mesma key/blockId em A e B: B usa o próprio default."""
    _frozen_today(monkeypatch, date(2026, 10, 7))
    parsed = parse_filter_overrides_query('{"bySlideId":{"A":{"byInputId":{"in_md":2}}}}')
    cfg = _carteira_cfg()
    slide_b = {"id": "B", "nativeConfig": cfg}
    overrides_b = PresentationPayloadService._slide_filter_overrides(None, parsed, slide_b)
    gateway = _recording_gateway()
    enrichment = ComunicadoDataEnrichmentService(catalog=TvDataRouteCatalogService(), gateway=gateway)
    enrichment.enrich_blocks(cfg["blocks"], cfg=cfg, authorization=None, filter_overrides=overrides_b)
    assert {(p["start_date"], p["end_date"]) for _op, p in gateway.calls} == {("2026-10-05", "2026-10-07")}


# ---------------------------------------------------------------------------
# MDD: export → import → export preserva binding/valueSchema/expressões input.*
# ---------------------------------------------------------------------------


def test_slide_template_mdd_roundtrip_preserves_variable_input():
    from tv_app.application.services.slide_template_mdd_service import (
        build_slide_template_mdd,
        parse_slide_template_mdd,
    )

    cfg = _carteira_cfg()

    def export(native_config):
        raw, _name = build_slide_template_mdd(
            key="carteira",
            label="Carteira",
            description=None,
            title="Carteira",
            duration_sec=30,
            native_config=native_config,
        )
        return raw

    imported = parse_slide_template_mdd(export(cfg))["nativeConfig"]
    reimported = parse_slide_template_mdd(export(imported))["nativeConfig"]
    assert imported == cfg
    assert reimported == cfg
    assert contract.collect_input_variables(reimported["blocks"])[1] == []
    assert _issues(reimported) == []


def test_deck_package_roundtrip_preserves_variable_input():
    from tv_app.application.services.tv_deck_binding_validator import TvDeckBindingValidator
    from tv_app.application.services.tv_deck_package_service import (
        TvDeckPackageService,
        _PreviewStore,
    )

    cfg = _carteira_cfg()
    section_id = "22222222-2222-2222-2222-222222222222"
    playlist = {
        "id": PLAYLIST_ID,
        "name": "Deck",
        "description": None,
        "viewportProfile": "full_hd",
        "transitionStyle": "fade",
        "defaultDurationSec": 30,
        "globalRefreshSec": None,
        "dataDefaults": {},
        "masterConfig": {},
        "ownerUserId": "u1",
        "createdBy": "u1",
        "revision": 1,
    }
    sections = [
        {
            "id": section_id,
            "name": "Principal",
            "sortOrder": 0,
            "isCollapsed": False,
            "isActive": True,
            "isMain": True,
            "defaultDurationSec": None,
            "transitionStyle": None,
            "masterConfig": {},
        }
    ]

    def slide_row(native_config):
        return {
            "id": SLIDE_ID,
            "sectionId": section_id,
            "sortOrder": 0,
            "slideType": "native",
            "durationSec": 30,
            "title": "Carteira",
            "nativeScreenKey": "custom_message",
            "nativeConfig": native_config,
            "externalUrl": None,
            "externalSandbox": None,
            "isActive": True,
            "transitionStyle": None,
        }

    repo = MagicMock()
    repo.get_by_id.return_value = playlist
    repo.list_sections.return_value = sections
    repo.list_slides.return_value = [slide_row(cfg)]
    repo.create.return_value = {**playlist, "id": "33333333-3333-3333-3333-333333333333"}
    repo.update.return_value = repo.create.return_value
    repo.import_sections_from_deck.return_value = {section_id: section_id}
    repo.import_slides_from_deck.return_value = []
    media_repo = MagicMock()
    media_repo.list_for_playlist.return_value = []
    catalog = MagicMock()
    catalog.get_route.return_value = None
    service = TvDeckPackageService(
        playlist_repo=repo,
        media_repo=media_repo,
        media_storage=MagicMock(),
        binding_validator=TvDeckBindingValidator(catalog=catalog),
        max_bytes=10 * 1024 * 1024,
        preview_store=_PreviewStore(ttl_seconds=60),
    )

    def import_native_config(payload):
        preview = service.preview_import(payload)
        service.apply_import(import_token=preview["importToken"], created_by="u1", binding_policy="lenient")
        imported_slides = repo.import_slides_from_deck.call_args.args[1]
        return imported_slides[0]["nativeConfig"]

    first_payload, _ = service.export_package(PLAYLIST_ID, exported_by="u1")
    imported = import_native_config(first_payload)
    repo.list_slides.return_value = [slide_row(imported)]
    second_payload, _ = service.export_package(PLAYLIST_ID, exported_by="u1")
    reimported = import_native_config(second_payload)

    assert imported == cfg
    assert reimported == cfg
    variable = next(block for block in reimported["blocks"] if block["id"] == "in_md")["input"]
    assert variable["binding"] == {"kind": "variable", "key": "meeting_day"}
    assert variable["valueSchema"] == MEETING_DAY_SCHEMA


# ---------------------------------------------------------------------------
# Runtime por tipo, segurança existente e isolamento adicional
# ---------------------------------------------------------------------------


def _typed_scope(key, value_schema, default):
    return contract.build_input_variable_scope(
        [_variable_block(binding={"kind": "variable", "key": key}, valueSchema=value_schema, defaultValue=default)]
    )


def test_string_variable_feeds_string_param():
    out = resolve_param_expressions(
        {"branch": _spec(_ident("input.branch_code"))},
        route=ROUTE,
        context=_ctx(date(2026, 10, 7)),
        input_scope=_typed_scope("branch_code", {"type": "string", "enum": ["01", "02"]}, "02"),
    )
    assert out.error is None and out.params["branch"] == "02"


@pytest.mark.parametrize(("flag", "expected"), [(True, "01"), (False, "02")])
def test_boolean_variable_evaluates_as_logical(flag, expected):
    spec = _spec({"kind": "if", "children": [_ident("input.use_sc"), _lit("01"), _lit("02")]})
    out = resolve_param_expressions(
        {"branch": spec},
        route=ROUTE,
        context=_ctx(date(2026, 10, 7)),
        input_scope=_typed_scope("use_sc", {"type": "boolean"}, flag),
    )
    assert out.error is None and out.params["branch"] == expected


def test_candidate_validation_keeps_route_param_guards():
    locked = _source(params={"locked": _spec(_ident("input.meeting_day"))})
    unknown = _source(params={"nope": _spec(_ident("input.meeting_day"))})
    assert _issues({"version": 5, "blocks": [_variable_block(), locked]})
    assert _issues({"version": 5, "blocks": [_variable_block(), unknown]})


def _branch_variable_cfg(branch_value):
    variable = _variable_block(
        binding={"kind": "variable", "key": "branch_code"},
        valueSchema={"type": "string"},
        defaultValue=branch_value,
    )
    return {"version": 5, "blocks": [variable, _source(params={"branch": _spec(_ident("input.branch_code"))})]}


@pytest.mark.usefixtures("_clear_cache")
def test_route_enum_still_rejects_branch_from_variable():
    gateway = _recording_gateway()
    enrichment = ComunicadoDataEnrichmentService(catalog=TvDataRouteCatalogService(), gateway=gateway)
    cfg = _branch_variable_cfg("99")
    enriched = enrichment.enrich_blocks(cfg["blocks"], cfg=cfg, authorization=None)
    resolved = next(block for block in enriched if block["id"] == "src_sc")["resolved"]
    assert resolved["paramExpressions"][0]["error"]["code"] == "m.expression_type_mismatch"
    assert gateway.calls == []


@pytest.mark.usefixtures("_clear_cache")
def test_branch_policy_runs_on_value_resolved_from_variable(monkeypatch):
    from tv_app.application.services import comunicado_data_enrichment_service as enrichment_module

    seen: list[Any] = []

    def _deny_es(route, params, *, user=None):
        seen.append((params or {}).get("branch"))
        if (params or {}).get("branch") == "02":
            raise ValueError("filial não permitida")

    monkeypatch.setattr(enrichment_module, "validate_data_route_branch", _deny_es)
    gateway = _recording_gateway()
    enrichment = ComunicadoDataEnrichmentService(catalog=TvDataRouteCatalogService(), gateway=gateway)
    cfg = _branch_variable_cfg("02")
    with pytest.raises(ValueError, match="filial"):
        enrichment.enrich_blocks(cfg["blocks"], cfg=cfg, authorization=None)
    assert seen == ["02"]
    assert gateway.calls == []


@pytest.mark.usefixtures("_clear_cache")
def test_sources_with_different_routes_receive_same_variable_context(monkeypatch):
    _frozen_today(monkeypatch, date(2026, 10, 7))
    gateway = _recording_gateway()
    enrichment = ComunicadoDataEnrichmentService(catalog=TvDataRouteCatalogService(), gateway=gateway)
    other = _source("src_portfolio")
    other["dataBinding"]["operationId"] = "get_billing_portfolio_summary"
    cfg = {"version": 5, "blocks": [_variable_block(), _source(), other]}
    enrichment.enrich_blocks(
        cfg["blocks"],
        cfg=cfg,
        authorization=None,
        filter_overrides={"slide": {}, "bySourceId": {}, "byInputId": {"in_md": 2}},
    )
    by_op = {op: (p["start_date"], p["end_date"]) for op, p in gateway.calls}
    assert by_op == {
        ROUTE_OP: ("2026-09-28", "2026-10-02"),
        "get_billing_portfolio_summary": ("2026-09-28", "2026-10-02"),
    }


def test_slide_without_variable_receives_no_input_overrides():
    parsed = parse_filter_overrides_query('{"bySlideId":{"A":{"byInputId":{"in_md":2}}}}')
    slide_b = {"id": "B", "nativeConfig": {"version": 5, "blocks": [_source(params={"branch": "01"})]}}
    assert PresentationPayloadService._slide_filter_overrides(None, parsed, slide_b) is None
    slide_a = {"id": "A", "nativeConfig": _carteira_cfg()}
    overrides_a = PresentationPayloadService._slide_filter_overrides(None, parsed, slide_a)
    assert overrides_a["byInputId"] == {"in_md": 2}


# ---------------------------------------------------------------------------
# Carteira Semanal — proposta de PresentationMutation (preview, sem persistir)
# ---------------------------------------------------------------------------


def _with_hardcoded_monday(node):
    """Estado atual da Carteira: o dia da reunião é o literal 0 (Monday) em cada consumidor."""
    if isinstance(node, dict):
        if node == _ident("input.meeting_day"):
            return _lit(0)
        return {key: _with_hardcoded_monday(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_with_hardcoded_monday(item) for item in node]
    return node


CARTEIRA_SOURCE_IDS = ("cs_sc_summary", "cs_es_summary", "cs_sc_customers", "cs_es_customers")
CARTEIRA_MUTATION_OPS = [
    _UPSERT_VARIABLE,
    *(
        {
            "op": "patch_data_source_params",
            "blockId": source_id,
            "set": {"start_date": CARTEIRA_START, "end_date": CARTEIRA_END},
        }
        for source_id in CARTEIRA_SOURCE_IDS
    ),
    {
        "op": "patch_data_model",
        "modelId": "cs_period_model",
        "inputPatches": [
            {"inputId": "period_src", "params": {"set": {"start_date": CARTEIRA_START, "end_date": CARTEIRA_END}}}
        ],
    },
]


@pytest.mark.usefixtures("_mutation_env")
def test_carteira_mutation_proposal_previews_on_current_slide():
    current = _with_hardcoded_monday(_carteira_cfg())
    current_blocks = [block for block in current["blocks"] if block["type"] != "input"]
    assert "input.meeting_day" not in str(current)

    result = _preview(current_blocks, CARTEIRA_MUTATION_OPS, data_models=current["dataModels"])

    assert result["ok"] is True
    native_config = result["nativeConfig"]
    blocks = {block["id"]: block for block in native_config["blocks"]}
    assert blocks["in_md"]["input"]["binding"] == {"kind": "variable", "key": "meeting_day"}
    for source_id in CARTEIRA_SOURCE_IDS:
        params = blocks[source_id]["dataBinding"]["params"]
        assert (params["start_date"], params["end_date"]) == (CARTEIRA_START, CARTEIRA_END)
    period_src = native_config["dataModels"][0]["inputs"][0]["params"]
    assert (period_src["start_date"], period_src["end_date"]) == (CARTEIRA_START, CARTEIRA_END)
    assert _issues(native_config) == []


@pytest.mark.usefixtures("_mutation_env")
def test_carteira_mutation_without_input_is_rejected():
    current = _with_hardcoded_monday(_carteira_cfg())
    current_blocks = [block for block in current["blocks"] if block["type"] != "input"]
    with pytest.raises(PresentationPatchError, match="input.meeting_day"):
        _preview(current_blocks, CARTEIRA_MUTATION_OPS[1:], data_models=current["dataModels"])
