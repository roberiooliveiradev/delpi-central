"""Filtro (``type: "input"`` routeParam) com ExpressionSpec em ``defaultValue``.

Cobre: contribuição persistida, rejeição de AST em override runtime (inclusive
legacy ``slide``/``bySourceId``), scoping por rota da camada do Filtro,
precedência A–E (data_source × DataModel), decoração ``resolvedValue`` /
``resolvedDiverged``, validação de escrita multi-target, sanitize, MDD e
PresentationMutation ``upsert_block``.
"""

from __future__ import annotations

import copy
from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.comunicado_input_filters_service import (
    collect_input_filter_contributions,
)
from tv_app.application.services.comunicado_native_config_sanitize import (
    sanitize_comunicado_config,
)
from tv_app.application.services.data import value_expression_service as ves
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
from tv_app.application.services.public_filter_overrides_service import (
    parse_filter_overrides_query,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)

ROUTE_OP = "get_commercial_rol_summary"
TODAY = date(2026, 10, 7)

NO_DATE_OP = "fake_no_date_route"
LOCKED_OP = "fake_locked_start_route"
INT_START_OP = "fake_integer_start_route"
FIXED_START_OP = "fake_fixed_start_route"

_FAKE_ROUTES: dict[str, dict[str, Any]] = {
    NO_DATE_OP: {
        "operationId": NO_DATE_OP,
        "label": "Sem data",
        "paramSchema": {"branch": {"type": "string", "optional": True}},
    },
    LOCKED_OP: {
        "operationId": LOCKED_OP,
        "label": "Data travada",
        "paramSchema": {
            "start_date": {
                "type": "string",
                "format": "date",
                "optional": True,
                "expressionAllowed": False,
            }
        },
    },
    INT_START_OP: {
        "operationId": INT_START_OP,
        "label": "Start inteiro",
        "paramSchema": {"start_date": {"type": "integer", "optional": True}},
    },
    FIXED_START_OP: {
        "operationId": FIXED_START_OP,
        "label": "Start fixo",
        "paramSchema": {"start_date": {"type": "string", "format": "date", "optional": True}},
        "fixedQueryParams": {"start_date": "2020-01-01"},
    },
}


class _Catalog:
    """Catálogo real + rotas fake para contratos multi-target."""

    def __init__(self) -> None:
        self._real = TvDataRouteCatalogService()

    def get_route(self, operation_id):
        if operation_id in _FAKE_ROUTES:
            return _FAKE_ROUTES[operation_id]
        return self._real.get_route(operation_id)

    def is_allowed(self, operation_id):
        return operation_id in _FAKE_ROUTES or self._real.is_allowed(operation_id)

    def __getattr__(self, name):
        return getattr(self._real, name)


def _ident(name):
    return {"kind": "identifier", "value": name}


def _lit(value):
    return {"kind": "literal", "value": value}


def _call(name, *children):
    return {"kind": "call", "value": name, "children": list(children)}


def _spec(ast):
    return {"expression": {"version": 1, "expression": ast}}


TODAY_SPEC = _spec(_ident("today"))


def _filter(block_id="flt_start", *, param_key="start_date", value=TODAY_SPEC, **patch):
    return {
        "id": block_id,
        "type": "input",
        "frame": {"x": 1, "y": 1, "w": 20, "h": 6},
        "input": {"paramKey": param_key, "defaultValue": copy.deepcopy(value), **patch},
    }


def _source(block_id="src_a", op=ROUTE_OP, params=None):
    return {
        "id": block_id,
        "type": "data_source",
        "frame": {"x": 1, "y": 10, "w": 30, "h": 20},
        "dataBinding": {
            "operationId": op,
            "params": dict(params) if params is not None else {"branch": "01"},
            "displayMode": "table",
        },
    }


def _model(params=None, op=ROUTE_OP):
    return {
        "id": "period_model",
        "primaryInputId": "period_src",
        "inputs": [
            {
                "id": "period_src",
                "operationId": op,
                "params": dict(params) if params is not None else {"branch": "01"},
            }
        ],
    }


_USER = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")


def _issues(cfg) -> list[dict[str, str]]:
    return TvDataConfigValidationService(catalog=_Catalog()).validate(cfg, user=_USER)["issues"]


def _codes(cfg) -> list[str]:
    return [str(issue.get("code") or "") for issue in _issues(cfg)]


# ---------------------------------------------------------------------------
# Contribuição + segurança runtime
# ---------------------------------------------------------------------------


class TestContribution:
    def test_persisted_expression_enters_slide_layer(self):
        contrib = collect_input_filter_contributions(
            [_filter()],
            schema_by_source_id={},
            slide_schemas=[{"start_date": {"type": "string", "format": "date"}}],
        )
        assert contrib["slide"] == {"start_date": TODAY_SPEC}

    def test_persisted_expression_requires_declared_field(self):
        contrib = collect_input_filter_contributions(
            [_filter()],
            schema_by_source_id={},
            slide_schemas=[{"branch": {"type": "string"}}],
        )
        assert contrib["slide"] == {}

    def test_persisted_expression_reaches_targeted_source_only(self):
        block = _filter(targetScope="sources", targetSourceIds=["src_a"])
        schema = {"start_date": {"type": "string", "format": "date"}}
        contrib = collect_input_filter_contributions(
            [block],
            schema_by_source_id={"src_a": schema, "src_b": schema},
            slide_schemas=[schema, schema],
        )
        assert contrib["bySourceId"] == {"src_a": {"start_date": TODAY_SPEC}}
        assert contrib["slide"] == {}

    def test_variable_filter_default_never_contributes_expression(self):
        block = {
            "id": "in_var",
            "type": "input",
            "input": {
                "paramKey": "start_date",
                "binding": {"kind": "variable", "key": "x"},
                "defaultValue": TODAY_SPEC,
            },
        }
        contrib = collect_input_filter_contributions(
            [block], schema_by_source_id={}, slide_schemas=None
        )
        assert contrib["slide"] == {}

    @pytest.mark.parametrize(
        "overrides",
        [
            {"slide": {"start_date": TODAY_SPEC}},
            {"bySourceId": {"src_a": {"start_date": TODAY_SPEC}}},
            {"slide": {"start_date": ["2026-01-01"]}},
        ],
    )
    def test_runtime_structured_override_is_dropped(self, overrides):
        schema = {"start_date": {"type": "string", "format": "date"}}
        contrib = collect_input_filter_contributions(
            [],
            runtime_overrides=overrides,
            schema_by_source_id={"src_a": schema},
            slide_schemas=[schema],
        )
        assert contrib["slide"] == {}
        assert all(not bucket for bucket in contrib["bySourceId"].values())

    def test_runtime_scalar_override_still_applies(self):
        schema = {"start_date": {"type": "string", "format": "date"}}
        contrib = collect_input_filter_contributions(
            [_filter()],
            runtime_overrides={"slide": {"start_date": "2026-05-05"}},
            schema_by_source_id={},
            slide_schemas=[schema],
        )
        assert contrib["slide"] == {"start_date": "2026-05-05"}


class TestPublicOverrideParse:
    def test_ast_is_rejected_in_every_legacy_channel(self):
        raw = (
            '{"slide":{"start_date":{"expression":{"version":1,"expression":'
            '{"kind":"identifier","value":"today"}}},"branch":"02"},'
            '"bySourceId":{"src_a":{"start_date":{"expression":{}},"branch":"01"}},'
            '"end_date":{"expression":{}},"limit":[1,2],"customer_segment":"weg"}'
        )
        parsed = parse_filter_overrides_query(raw)
        assert parsed["slide"] == {"branch": "02", "customer_segment": "weg"}
        assert parsed["bySourceId"] == {"src_a": {"branch": "01"}}

    def test_scalar_and_null_overrides_preserved(self):
        parsed = parse_filter_overrides_query(
            '{"slide":{"start_date":"2026-05-05","branch":null},"bySourceId":{"s":{"limit":5}}}'
        )
        assert parsed == {
            "slide": {"start_date": "2026-05-05", "branch": None},
            "bySourceId": {"s": {"limit": 5}},
        }


# ---------------------------------------------------------------------------
# Runtime: precedência A–E, scoping, decoração
# ---------------------------------------------------------------------------


@pytest.fixture
def _runtime(monkeypatch):
    reset_comunicado_data_block_cache()
    monkeypatch.setattr(ves, "calendar_today", lambda today=None, tz_name=None: today or TODAY)
    yield
    reset_comunicado_data_block_cache()


def _gateway():
    gateway = MagicMock()
    calls: list[tuple[str, dict]] = []

    def _fetch(operation_id, params=None, **kwargs):
        calls.append((operation_id, dict(params or {})))
        return {
            "meta": {"shape": "scalar", "entity": "commercial_rol_summary"},
            "data": {"branch": "01", "rol": 1.0},
            "route": {"label": "ROL", "valueFields": ["rol"]},
        }

    gateway.fetch_by_operation_id.side_effect = _fetch
    gateway.calls = calls
    return gateway


def _enrich(cfg, *, playlist_defaults=None, filter_overrides=None):
    gateway = _gateway()
    service = ComunicadoDataEnrichmentService(catalog=_Catalog(), gateway=gateway)
    enriched = service.enrich_blocks(
        cfg["blocks"],
        cfg=cfg,
        authorization=None,
        user=_USER,
        playlist_defaults=playlist_defaults,
        filter_overrides=filter_overrides,
    )
    return {block["id"]: block for block in enriched}, gateway.calls


def _start_dates(calls, op=ROUTE_OP):
    return sorted({params.get("start_date") for called_op, params in calls if called_op == op})


_PLAYLIST = {"start_date": "2026-01-01"}
_SLIDE = {"start_date": "2026-02-01"}
_SOURCE = {"branch": "01", "start_date": "2026-03-01"}


def _precedence_cfg(filter_block, *, consumer):
    blocks = [filter_block] if filter_block else []
    cfg: dict[str, Any] = {"version": 5, "blocks": blocks, "dataFilters": dict(_SLIDE)}
    if consumer == "data_source":
        cfg["blocks"] = [*blocks, _source(params=_SOURCE)]
    else:
        cfg["dataModels"] = [_model(params=_SOURCE)]
    return cfg


@pytest.mark.usefixtures("_runtime")
@pytest.mark.parametrize("consumer", ["data_source", "data_model"])
@pytest.mark.parametrize(
    ("case", "filter_block", "overrides", "expected"),
    [
        ("A_filter_expression_wins", _filter(), None, "2026-10-07"),
        (
            "B_runtime_override_wins",
            _filter(),
            {"slide": {"start_date": "2026-05-05"}, "bySourceId": {}},
            "2026-05-05",
        ),
        (
            "C_cleared_override_returns_to_expression",
            _filter(),
            {"slide": {"start_date": None}, "bySourceId": {}},
            "2026-10-07",
        ),
        ("D_literal_filter_unchanged", _filter(value="2026-04-04"), None, "2026-04-04"),
        ("E_no_filter_source_wins", None, None, "2026-03-01"),
    ],
)
def test_precedence_table(consumer, case, filter_block, overrides, expected):
    cfg = _precedence_cfg(copy.deepcopy(filter_block), consumer=consumer)
    _blocks, calls = _enrich(cfg, playlist_defaults=_PLAYLIST, filter_overrides=overrides)
    assert _start_dates(calls) == [expected], case


@pytest.mark.usefixtures("_runtime")
@pytest.mark.parametrize("other_op", [LOCKED_OP, FIXED_START_OP])
def test_expression_scoped_to_routes_that_allow_it(other_op):
    """Rota que declara mas não aceita expressão não recebe o AST (sem erro); a outra resolve."""
    cfg = {
        "version": 5,
        "blocks": [
            _filter(),
            _source("src_a", params={"branch": "01", "start_date": "2026-03-01"}),
            _source("src_other", op=other_op, params={"start_date": "2026-03-01"}),
        ],
    }
    blocks, calls = _enrich(cfg)
    assert _start_dates(calls) == ["2026-10-07"]
    other_calls = [params for op, params in calls if op == other_op]
    assert other_calls and all(
        not isinstance(params.get("start_date"), dict) for params in other_calls
    )
    assert not blocks["src_other"]["resolved"].get("error"), blocks["src_other"]["resolved"]


@pytest.mark.usefixtures("_runtime")
def test_sources_scope_reaches_only_marked_source():
    cfg = {
        "version": 5,
        "blocks": [
            _filter(targetScope="sources", targetSourceIds=["src_a"]),
            _source("src_a", params={"branch": "01", "start_date": "2026-03-01"}),
            _source("src_b", params={"branch": "02", "start_date": "2026-03-01"}),
        ],
    }
    _blocks, calls = _enrich(cfg)
    by_branch = {params.get("branch"): params.get("start_date") for _op, params in calls}
    assert by_branch == {"01": "2026-10-07", "02": "2026-03-01"}


@pytest.mark.usefixtures("_runtime")
def test_self_reference_fails_closed_without_fetch():
    cfg = {
        "version": 5,
        "blocks": [
            _filter(value=_spec(_ident("param.start_date"))),
            _source(params={"branch": "01"}),
        ],
    }
    blocks, calls = _enrich(cfg)
    assert calls == []
    assert blocks["src_a"]["resolved"].get("error")


@pytest.mark.usefixtures("_runtime")
def test_decoration_single_value():
    cfg = {
        "version": 5,
        "blocks": [_filter(), _source("src_a"), _source("src_b", params={"branch": "02"})],
        "dataModels": [_model()],
    }
    blocks, _calls = _enrich(cfg)
    decorated = blocks["flt_start"]["input"]
    assert decorated["resolvedValue"] == "2026-10-07"
    assert decorated["resolvedDiverged"] is False
    assert decorated["defaultValue"] == TODAY_SPEC


@pytest.mark.usefixtures("_runtime")
def test_decoration_divergent_consumers():
    rel = _spec(_call("Date.AddDays", _ident("param.end_date"), _lit(-7)))
    cfg = {
        "version": 5,
        "blocks": [
            _filter(value=rel),
            _source("src_a", params={"branch": "01", "end_date": "2026-10-10"}),
            _source("src_b", params={"branch": "02", "end_date": "2026-10-20"}),
        ],
    }
    blocks, calls = _enrich(cfg)
    decorated = blocks["flt_start"]["input"]
    assert decorated["resolvedDiverged"] is True
    assert "resolvedValue" not in decorated
    assert _start_dates(calls) == ["2026-10-03", "2026-10-13"]


@pytest.mark.usefixtures("_runtime")
def test_decoration_follows_runtime_override():
    cfg = {"version": 5, "blocks": [_filter(), _source()]}
    blocks, _calls = _enrich(
        cfg, filter_overrides={"slide": {"start_date": "2026-05-05"}, "bySourceId": {}}
    )
    assert blocks["flt_start"]["input"]["resolvedValue"] == "2026-05-05"


@pytest.mark.usefixtures("_runtime")
def test_literal_filter_is_not_decorated():
    cfg = {"version": 5, "blocks": [_filter(value="2026-04-04"), _source()]}
    blocks, _calls = _enrich(cfg)
    assert "resolvedValue" not in blocks["flt_start"]["input"]
    assert "resolvedDiverged" not in blocks["flt_start"]["input"]


@pytest.mark.usefixtures("_runtime")
@pytest.mark.parametrize("value", [TODAY_SPEC, "2026-04-04"])
def test_data_model_only_slide_receives_filter(value):
    cfg = {"version": 5, "blocks": [_filter(value=value)], "dataModels": [_model()]}
    _blocks, calls = _enrich(cfg)
    expected = "2026-10-07" if isinstance(value, dict) else "2026-04-04"
    assert _start_dates(calls) == [expected]


@pytest.mark.usefixtures("_runtime")
def test_mixed_slide_intersection_unchanged_for_literal():
    """Fallback de schema só vale para slide sem fonte: slide mista mantém a interseção das fontes."""
    cfg = {
        "version": 5,
        "blocks": [
            _filter(param_key="customer_segment", value="weg"),
            _source("src_nodate", op=NO_DATE_OP, params={"branch": "01"}),
        ],
        "dataModels": [_model()],
    }
    _blocks, calls = _enrich(cfg)
    assert all("customer_segment" not in params for _op, params in calls)


# ---------------------------------------------------------------------------
# Validação de escrita (multi-target, per-route)
# ---------------------------------------------------------------------------


class TestWriteValidation:
    def test_valid_expression_filter(self):
        assert _issues({"version": 5, "blocks": [_filter(), _source()]}) == []

    def test_valid_expression_filter_on_data_model_slide(self):
        assert _issues({"version": 5, "blocks": [_filter()], "dataModels": [_model()]}) == []

    def test_route_forbidding_expression_rejects(self):
        issues = _issues(
            {"version": 5, "blocks": [_filter(), _source(), _source("src_l", op=LOCKED_OP)]}
        )
        assert [
            (issue["field"], issue["code"]) for issue in issues
        ] == [("blocks[0].input.defaultValue", "m.expression_param_not_allowed")]

    def test_incompatible_second_route_rejects_not_first_route_only(self):
        issues = _issues(
            {"version": 5, "blocks": [_filter(), _source(), _source("src_i", op=INT_START_OP)]}
        )
        assert [(issue["field"], issue["code"]) for issue in issues] == [
            ("blocks[0].input.defaultValue", "expression.type_mismatch")
        ]

    def test_unmarked_incompatible_source_is_ignored_in_sources_scope(self):
        cfg = {
            "version": 5,
            "blocks": [
                _filter(targetScope="sources", targetSourceIds=["src_a"]),
                _source(),
                _source("src_i", op=INT_START_OP),
            ],
        }
        assert _issues(cfg) == []

    def test_undeclared_param_rejects(self):
        codes = _codes({"version": 5, "blocks": [_filter(param_key="nope"), _source()]})
        assert "m.expression_param_not_allowed" in codes

    def test_fixed_route_excluded_but_not_veto(self):
        cfg = {
            "version": 5,
            "blocks": [_filter(), _source(), _source("src_f", op=FIXED_START_OP)],
        }
        assert _issues(cfg) == []
        only_fixed = {"version": 5, "blocks": [_filter(), _source("src_f", op=FIXED_START_OP)]}
        assert "m.expression_param_not_allowed" in _codes(only_fixed)

    def test_input_reference_must_be_declared(self):
        rel = _spec(_call("Date.AddDays", _ident("today"), _ident("input.offset")))
        assert "input.reference_undeclared" in _codes(
            {"version": 5, "blocks": [_filter(value=rel), _source()]}
        )
        variable = {
            "id": "in_offset",
            "type": "input",
            "frame": {"x": 1, "y": 30, "w": 10, "h": 5},
            "input": {
                "paramKey": "",
                "binding": {"kind": "variable", "key": "offset"},
                "valueSchema": {"type": "integer"},
                "defaultValue": -7,
            },
        }
        assert _issues({"version": 5, "blocks": [variable, _filter(value=rel), _source()]}) == []

    def test_variable_default_expression_rejected(self):
        variable = {
            "id": "in_var",
            "type": "input",
            "frame": {"x": 1, "y": 30, "w": 10, "h": 5},
            "input": {
                "paramKey": "",
                "binding": {"kind": "variable", "key": "day"},
                "valueSchema": {"type": "string", "format": "date"},
                "defaultValue": TODAY_SPEC,
            },
        }
        assert _codes({"version": 5, "blocks": [variable, _source()]})

    def test_literal_filter_unchanged(self):
        assert _issues({"version": 5, "blocks": [_filter(value="2026-04-04"), _source()]}) == []


# ---------------------------------------------------------------------------
# Persistência: sanitize, MDD, PresentationMutation
# ---------------------------------------------------------------------------


def test_sanitize_keeps_expression_and_strips_runtime_decoration():
    block = _filter()
    block["input"].update(
        resolvedValue="2026-10-07", resolvedDiverged=False, resolvedField={}, paramAvailable=True
    )
    cleaned = sanitize_comunicado_config({"version": 5, "blocks": [block]})
    assert cleaned["blocks"][0]["input"] == {"paramKey": "start_date", "defaultValue": TODAY_SPEC}


def test_slide_template_mdd_roundtrip_preserves_filter_expression():
    from tv_app.application.services.slide_template_mdd_service import (
        build_slide_template_mdd,
        parse_slide_template_mdd,
    )

    cfg = {"version": 5, "blocks": [_filter(), _source()]}

    def export(native_config):
        raw, _name = build_slide_template_mdd(
            key="filtro",
            label="Filtro",
            description=None,
            title="Filtro",
            duration_sec=30,
            native_config=native_config,
        )
        return raw

    imported = parse_slide_template_mdd(export(cfg))["nativeConfig"]
    reimported = parse_slide_template_mdd(export(imported))["nativeConfig"]
    assert imported == cfg
    assert reimported == cfg


SLIDE_ID = "11111111-1111-1111-1111-111111111111"
PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"


class _Repo:
    def __init__(self, blocks):
        self.slides = {
            SLIDE_ID: {
                "id": SLIDE_ID,
                "title": "Filtro",
                "durationSec": 30,
                "isActive": True,
                "nativeConfig": {"version": 5, "blocks": copy.deepcopy(blocks)},
            }
        }

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


def _preview(blocks, ops):
    service = PresentationPatchService(
        catalog=_Catalog(), repo=_Repo(blocks), resolution=_Resolution()
    )
    return service.preview(
        {"target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID}, "ops": ops},
        user=_USER,
        authorization="Bearer x",
    )


@pytest.mark.usefixtures("_mutation_env")
class TestMutation:
    def test_upsert_filter_with_expression(self):
        result = _preview([_source()], [{"op": "upsert_block", "block": _filter()}])
        assert result["ok"] is True
        blocks = {block["id"]: block for block in result["nativeConfig"]["blocks"]}
        assert blocks["flt_start"]["input"]["defaultValue"] == TODAY_SPEC

    def test_upsert_filter_with_forbidden_expression_fails(self):
        with pytest.raises(PresentationPatchError):
            _preview(
                [_source(), _source("src_l", op=LOCKED_OP)],
                [{"op": "upsert_block", "block": _filter()}],
            )
