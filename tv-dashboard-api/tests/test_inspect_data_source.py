"""inspect_data_source — superfície READ de inspeção focada de data_source legado.

Contrato: definição persistida + transform canônico + dependências derivadas
do contrato (nunca inferência por nome) + consumers + evidência de runtime sob
demanda (effectiveParams por entrada, inputResults, transformedResult, erros
tipados). Somente leitura — nenhuma proposta/mutação é criada.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from test_data_model_foundation import (
    PLAYLIST_ID,
    SLIDE_ID,
    _enrichment,
    _gateway_by_preset,
    _rol_payload,
    _user,
    _Repo,
)
from test_data_model_migration import _kpi, _slide, _src
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.services.comunicado_data_enrichment_service import (
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService


@pytest.fixture(autouse=True)
def _clear_data_cache():
    reset_comunicado_data_block_cache()
    yield
    reset_comunicado_data_block_cache()


_OP = "get_commercial_rol_summary"
PREV = 4399153.22
CUR = 4516461.10


# ---------------------------------------------------------------------------
# REPRESENTATIVE_DEPENDENCY_FIXTURE — modelado após o caso mensal real:
# pct_weg_sc_m26 = this_month (2026-09-01 → 2026-09-29 no clock de negócio) e
# pct_weg_sc_m25 = auxiliar do mesmo mês no ano anterior via ParamExpression
# (2025-09-01 → 2025-09-29) — estado moderno persistido em produção.
# ---------------------------------------------------------------------------


_M25_START_EXPR = {
    "expression": {
        "version": 1,
        "expression": {
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
        },
    }
}
_M25_END_EXPR = {
    "expression": {
        "version": 1,
        "expression": {
            "kind": "call",
            "value": "Date.AddMonths",
            "children": [
                {"kind": "identifier", "value": "today"},
                {"kind": "literal", "value": -12},
            ],
        },
    }
}


def _pct_sources() -> list[dict]:
    prev = _src(
        "pct_weg_sc_m25",
        preset="this_month",
        label="ROL WEG SC mês equivalente 2025",
        transform=[
            {"op": "rename", "from": "rol", "to": "rol_prev"},
            {"op": "addColumn", "name": "join_key", "expr": "1"},
        ],
    )
    # Período mensal anterior-equivalente via typed expressions — nunca um
    # novo preset hardcoded.
    prev["dataBinding"]["params"] = {
        "branch": "01",
        "customer_segment": "weg",
        "start_date": dict(_M25_START_EXPR),
        "end_date": dict(_M25_END_EXPR),
    }
    cur = _src(
        "pct_weg_sc_m26",
        preset="this_month",
        label="ROL WEG SC MTD",
        transform=[
            {"op": "addColumn", "name": "join_key", "expr": "1"},
            {
                "op": "merge",
                "sourceId": "pct_weg_sc_m25",
                "leftKey": "join_key",
                "rightKey": "join_key",
                "columns": ["rol_prev"],
            },
            {
                "op": "addColumn",
                "name": "value",
                "expr": "(rol / rol_prev - 1) * 100",
            },
        ],
    )
    return [prev, cur]


def _rol_gateway():
    """Mock do gateway distinguindo pelo ano efetivo de start_date — como o
    runtime faz após resolver preset/expressões."""
    gateway = MagicMock()
    calls: list[dict] = []

    def _fetch(operation_id, params=None, **kw):
        params = dict(params or {})
        calls.append(params)
        key = (
            "previous"
            if str(params.get("start_date") or "").startswith("2025")
            else "current"
        )
        return {"previous": _rol_payload(PREV), "current": _rol_payload(CUR)}[key]

    gateway.fetch_by_operation_id.side_effect = _fetch
    gateway.calls = calls
    return gateway


def _dispatch(*, slide: dict, gateway=None) -> GptActionsDispatchService:
    repo = _Repo(slide)
    writes = MagicMock()
    writes.get_slide.side_effect = lambda slide_id, playlist_id=None: repo.get_slide(
        slide_id, playlist_id=playlist_id
    )
    return GptActionsDispatchService(
        repo=repo,
        writes=writes,
        commit=MagicMock(),
        preview=TvDataPreviewService(enrichment=_enrichment(gateway or _rol_gateway())),
    )


def _access(**over):
    base = {
        "can_read": True,
        "can_edit": True,
        "playlist": {"dataDefaults": {"branch": "01"}, "revision": 7},
    }
    base.update(over)
    return SimpleNamespace(**base)


def _inspect(dispatch: GptActionsDispatchService, source_id: str, **kw):
    access = kw.pop("access", _access())
    with patch.object(dispatch._access, "resolve", return_value=access):
        return dispatch.inspect_data_source(
            user=_user(),
            playlist_id=PLAYLIST_ID,
            slide_id=SLIDE_ID,
            data_source_id=source_id,
            authorization=None,
            **kw,
        )


# ---------------------------------------------------------------------------
# Definição + transform + dependências (sem runtime)
# ---------------------------------------------------------------------------


class TestInspectDefinition:
    def test_source_identity_projection(self):
        slide = _slide(_pct_sources())
        out = _inspect(_dispatch(slide=slide), "pct_weg_sc_m26")
        src = out["source"]
        assert src["id"] == "pct_weg_sc_m26"
        assert src["label"] == "ROL WEG SC MTD"
        assert src["queryName"] == "pct_weg_sc_m26"
        assert src["operationId"] == _OP
        assert src["params"]["dateRangePreset"] == "this_month"
        assert src["hasTransform"] is True
        assert out["dataSourceId"] == "pct_weg_sc_m26"
        assert out["playlistId"] == PLAYLIST_ID
        assert out["slideId"] == SLIDE_ID
        assert out["revision"] == 7

    def test_persisted_transform_is_canonical(self):
        slide = _slide(_pct_sources())
        out = _inspect(_dispatch(slide=slide), "pct_weg_sc_m26")
        transform = out["transform"]
        assert transform["version"] == 1
        steps = transform["persisted"]["steps"]
        ops = [s["op"] for s in steps]
        assert ops == ["addColumn", "merge", "addColumn"]
        merge = steps[1]
        assert merge["sourceId"] == "pct_weg_sc_m25"
        assert merge["columns"] == ["rol_prev"]
        assert steps[2]["expr"] == "(rol / rol_prev - 1) * 100"

    def test_dependency_derived_from_contract_not_name(self):
        """A prova de causalidade: dependência vem do merge.sourceId persistido,
        não do sufixo do id."""
        slide = _slide(_pct_sources())
        out = _inspect(_dispatch(slide=slide), "pct_weg_sc_m26")
        assert out["dependencyStatus"] == "RESOLVED"
        dep = out["dependencies"][0]
        assert dep["kind"] == "data_source"
        assert dep["sourceId"] == "pct_weg_sc_m25"
        assert dep["queryName"] == "pct_weg_sc_m25"
        assert dep["status"] == "resolved"
        assert dep["fields"] == ["join_key", "rol_prev"]
        # Params persistidos do dependente — AST de expressão intacto.
        start_spec = dep["params"]["start_date"]["expression"]["expression"]
        assert start_spec["value"] == "Date.StartOfMonth"

    def test_source_without_transform_has_no_dependencies(self):
        slide = _slide(_pct_sources())
        out = _inspect(_dispatch(slide=slide), "pct_weg_sc_m25")
        # m25 tem transform (rename+addColumn) mas nenhum merge → sem deps.
        assert out["dependencyStatus"] == "NONE"
        assert out["dependencies"] == []
        assert out["source"]["hasTransform"] is True

    def test_unresolved_merge_ref_is_inconclusive(self):
        src = _src(
            "pct_nn_sc_m26",
            preset="this_year",
            transform=[
                {
                    "op": "merge",
                    "sourceId": "pct_nn_sc_m25",  # não existe no slide
                    "leftKey": "join_key",
                    "rightKey": "join_key",
                }
            ],
        )
        slide = _slide([src])
        out = _inspect(_dispatch(slide=slide), "pct_nn_sc_m26")
        assert out["dependencyStatus"] == "INCONCLUSIVE"
        assert out["dependencies"] == [
            {"kind": "data_source", "ref": "pct_nn_sc_m25", "status": "unresolved"}
        ]

    def test_consumers_listed(self):
        slide = _slide(
            _pct_sources()
            + [_kpi(block_id="kpi1", field="value", dataSourceId="pct_weg_sc_m26")]
        )
        out = _inspect(_dispatch(slide=slide), "pct_weg_sc_m26")
        assert out["consumers"] == {"kpi1": ["value"]}
        assert out["consumerCount"] == 1

    def test_expression_params_expose_context_references(self):
        """ParamExpression no binding: contextos usados aparecem como
        evidência estática (today/param.*) — sem avaliar."""
        block = _src("expr_src", preset="this_year")
        block["dataBinding"]["params"]["start_date"] = {
            "expression": {
                "version": 1,
                "expression": {
                    "kind": "call",
                    "value": "Date.StartOfMonth",
                    "children": [
                        {"kind": "identifier", "value": "today"},
                    ],
                },
            }
        }
        block["dataBinding"]["params"]["end_date"] = {
            "expression": {
                "version": 1,
                "expression": {
                    "kind": "identifier",
                    "value": "param.branch",
                },
            }
        }
        slide = _slide([block])
        out = _inspect(_dispatch(slide=slide), "expr_src")
        assert out["source"]["contextReferences"] == ["param.branch", "today"]

    def test_missing_source_404(self):
        slide = _slide(_pct_sources())
        with pytest.raises(GptActionsError) as exc_info:
            _inspect(_dispatch(slide=slide), "pct_ghost")
        assert exc_info.value.status_code == 404
        assert exc_info.value.details == {"dataSourceId": "pct_ghost"}

    def test_no_read_access_404(self):
        slide = _slide(_pct_sources())
        with pytest.raises(GptActionsError) as exc_info:
            _inspect(
                _dispatch(slide=slide),
                "pct_weg_sc_m26",
                access=_access(can_read=False),
            )
        assert exc_info.value.status_code == 404

    def test_no_secrets_in_payload(self):
        slide = _slide(_pct_sources())
        out = _inspect(
            _dispatch(slide=slide), "pct_weg_sc_m26", include_runtime=True
        )
        payload = json.dumps(out).lower()
        for token in ("authorization", "bearer", "token", "secret", "password"):
            assert token not in payload


# ---------------------------------------------------------------------------
# Runtime (include_runtime)
# ---------------------------------------------------------------------------


class TestInspectRuntime:
    def test_default_include_runtime_false(self):
        slide = _slide(_pct_sources())
        out = _inspect(_dispatch(slide=slide), "pct_weg_sc_m26")
        assert out["runtime"]["state"] == "not_executed"

    def test_runtime_dependency_contract(self):
        """Contrato §30: dependência B aparece em dependencies, inputResults e
        effectiveParams — sem inferência do caller."""
        slide = _slide(_pct_sources())
        out = _inspect(
            _dispatch(slide=slide), "pct_weg_sc_m26", include_runtime=True
        )
        runtime = out["runtime"]
        assert runtime["state"] == "ready"

        dep_ids = {d.get("sourceId") for d in out["dependencies"]}
        input_ids = {i["sourceId"] for i in runtime["inputResults"]}
        assert "pct_weg_sc_m25" in dep_ids
        assert "pct_weg_sc_m25" in input_ids

        prev = next(
            i for i in runtime["inputResults"] if i["sourceId"] == "pct_weg_sc_m25"
        )
        # AST autorado: persistido intacto em dependencies[].params; a
        # resolução por parâmetro fica no trace paramExpressions (requested
        # mostra o merge já resolvido — mesmo contrato do enrichment canônico).
        dep_entry = out["dependencies"][0]
        persisted_start = dep_entry["params"]["start_date"]["expression"]["expression"]
        assert persisted_start["kind"] == "call"
        assert persisted_start["value"] == "Date.StartOfMonth"
        assert prev["effectiveParams"]["start_date"] == "2025-09-01"
        assert prev["effectiveParams"]["end_date"] == "2025-09-29"
        # Valor que entrou no transform: campo consumido do sibling.
        assert prev["fields"]["rol_prev"] == pytest.approx(PREV)
        assert prev["rowCount"] >= 1

        # Params efetivos do alvo.
        assert runtime["requestedParams"]["dateRangePreset"] == "this_month"
        assert runtime["effectiveParams"]["start_date"] == "2026-09-01"
        assert runtime["effectiveParams"]["end_date"] == "2026-09-29"
        assert runtime["requestedParams"]["branch"] == "01"

        # Valor que saiu do transform — variação calculada, não recriada.
        result = runtime["transformedResult"]
        assert result is not None
        value = result["rows"][0]["value"]
        assert value == pytest.approx((CUR / PREV - 1) * 100)
        assert runtime["transformError"] is None
        assert runtime["executionOrder"].index("pct_weg_sc_m25") < runtime[
            "executionOrder"
        ].index("pct_weg_sc_m26")

    def test_runtime_expression_trace_on_dependency(self):
        """Estado moderno de produção: o AST fica persistido em source.params e
        o trace paramExpressions expõe, por parâmetro, o AST + expectedType +
        valor resolvido pelo backend (effectiveParams)."""
        slide = _slide(_pct_sources())
        out = _inspect(
            _dispatch(slide=slide), "pct_weg_sc_m26", include_runtime=True
        )
        prev = next(
            i
            for i in out["runtime"]["inputResults"]
            if i["sourceId"] == "pct_weg_sc_m25"
        )
        trace = {
            entry["param"]: entry for entry in prev.get("paramExpressions") or []
        }
        assert trace["start_date"]["resolved"] == "2025-09-01"
        assert trace["end_date"]["resolved"] == "2025-09-29"

    def test_runtime_single_source_no_merge(self):
        slide = _slide(
            [
                _src(
                    "solo",
                    transform=[
                        {"op": "select", "columns": ["rol", "branch"]},
                    ],
                )
            ]
        )
        out = _inspect(_dispatch(slide=slide), "solo", include_runtime=True)
        assert out["runtime"]["state"] == "ready"
        assert out["runtime"]["inputResults"] == []
        row = out["runtime"]["transformedResult"]["rows"][0]
        assert set(row.keys()) <= {"rol", "branch"}

    def test_runtime_unresolved_merge_surfaces_typed_error(self):
        src = _src(
            "pct_nn_sc_m26",
            transform=[
                {"op": "addColumn", "name": "join_key", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "pct_nn_sc_m25",
                    "leftKey": "join_key",
                    "rightKey": "join_key",
                },
            ],
        )
        slide = _slide([src])
        out = _inspect(_dispatch(slide=slide), "pct_nn_sc_m26", include_runtime=True)
        runtime = out["runtime"]
        assert runtime["state"] == "error"
        assert runtime["transformError"]["code"] == "m.merge_source_unavailable"

    def test_runtime_transform_expression_error(self):
        src = _src(
            "broken",
            transform=[
                {"op": "addColumn", "name": "x", "expr": "1 /"},
            ],
        )
        slide = _slide([src])
        out = _inspect(_dispatch(slide=slide), "broken", include_runtime=True)
        assert out["runtime"]["state"] == "error"
        assert out["runtime"]["transformError"] is not None

    def test_runtime_fetch_error_is_error_not_empty(self):
        gateway = _gateway_by_preset(
            {"current": _rol_payload(CUR)},
            fails={"current": RuntimeError("upstream down")},
        )
        slide = _slide([_src("failing")])
        out = _inspect(
            _dispatch(slide=slide, gateway=gateway), "failing", include_runtime=True
        )
        assert out["runtime"]["state"] == "error"

    def test_runtime_never_persists(self):
        """READ: nenhum write/port de mutação é chamado pelo caminho."""
        slide = _slide(_pct_sources())
        dispatch = _dispatch(slide=slide)
        _inspect(dispatch, "pct_weg_sc_m26", include_runtime=True)
        assert not dispatch._writes.create_proposal.called
        assert not dispatch._writes.update_slide.called
        assert not dispatch._commit.commit.called


# ---------------------------------------------------------------------------
# MCP surface
# ---------------------------------------------------------------------------


class TestMcpSurface:
    def test_tool_registered_read_class(self):
        import asyncio

        from tv_app.interface.mcp.constants import MCP_TOOL_NAMES, TOOL_CLASS
        from tv_app.interface.mcp.server import create_mcp_server

        assert "inspect_data_source" in MCP_TOOL_NAMES
        assert TOOL_CLASS["inspect_data_source"] == "READ"
        tools = asyncio.run(create_mcp_server().list_tools())
        tool = next(t for t in tools if t.name == "inspect_data_source")
        assert tool.annotations.read_only_hint is True

    def test_bridge_passes_authorization_and_runtime_flag(self):
        from test_vista_mcp_read_surface import _ctx, _viewer
        from tv_app.interface.mcp import tool_bridge

        seen = {}

        def _capture(*, user, playlist_id, slide_id, data_source_id, authorization, include_runtime):
            seen.update(
                authorization=authorization,
                include_runtime=include_runtime,
                data_source_id=data_source_id,
            )
            return {"dataSourceId": data_source_id}

        with _ctx(_viewer(), "Bearer user-token-xyz"), patch.object(
            tool_bridge._dispatch, "inspect_data_source", side_effect=_capture
        ):
            result = tool_bridge.tool_inspect_data_source(
                playlist_id="p",
                slide_id="s",
                data_source_id="pct_weg_sc_m26",
                include_runtime=True,
            )
        assert result.is_error is False
        assert seen["authorization"] == "Bearer user-token-xyz"
        assert seen["include_runtime"] is True
        assert seen["data_source_id"] == "pct_weg_sc_m26"

    def test_bridge_default_include_runtime_false(self):
        import inspect as py_inspect

        from tv_app.interface.mcp.tool_bridge import tool_inspect_data_source

        sig = py_inspect.signature(tool_inspect_data_source)
        assert sig.parameters["include_runtime"].default is False

    def test_bridge_domain_error_preserved(self):
        from test_vista_mcp_read_surface import _ctx, _viewer
        from tv_app.interface.mcp import tool_bridge

        with _ctx(_viewer()), patch.object(
            tool_bridge._dispatch,
            "inspect_data_source",
            side_effect=GptActionsError(
                'Data source "x" não encontrado no slide.',
                code="RESOURCE_NOT_FOUND",
                status_code=404,
                details={"dataSourceId": "x"},
            ),
        ):
            result = tool_bridge.tool_inspect_data_source(
                playlist_id="p", slide_id="s", data_source_id="x"
            )
        assert result.is_error is True
        body = result.structured_content
        assert body["code"] == "RESOURCE_NOT_FOUND"
        assert body["httpStatus"] == 404
        assert body["details"] == {"dataSourceId": "x"}
