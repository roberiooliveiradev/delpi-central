"""ISSUE #129 residual closure — suggest_change state integrity (F1)
and composition/reconciliation semantics (F2).

E01–E10: persisted slide read and visualEvidence must never convert a
real failure into "empty slide" / "preview unavailable".

C01–C12: create vs additive vs explicit redesign are distinct
semantics — obsolete blocks only leave via governed delete_block on
explicit redesign; create/additive never delete persisted blocks.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.services.data.presentation_command_planner_service import (
    PresentationCommandPlannerService,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)
from tv_app.application.services.data.slide_preview_render_service import (
    SlidePreviewRenderService,
)
from tv_app.application.services.editor_focus_store import EditorFocusStore
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
)

PID = str(uuid.uuid4())
SID = str(uuid.uuid4())

SLIDE_NATIVE = {
    "version": 1,
    "blocks": [
        {
            "id": "tbl-old",
            "type": "table_view",
            "frame": {"x": 0, "y": 60, "w": 40, "h": 35},
        },
        {
            "id": "blk-kpi",
            "type": "kpi_view",
            "frame": {"x": 0, "y": 8, "w": 18, "h": 18},
        },
    ],
}


def _user():
    return SimpleNamespace(
        is_superadmin=True,
        permissions=["tv-dashboard.read", "tv-dashboard.write"],
        roles=[], groups=[], id="u1", email="a@d.local",
    )


def _writes(*, blocks=None, slide_present=True):
    writes = MagicMock()
    writes.get_revision.return_value = 7
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": PID, "dataDefaults": {}}
    if slide_present:
        native = {
            "version": 1,
            "blocks": list(blocks if blocks is not None else SLIDE_NATIVE["blocks"]),
        }
        writes.get_slide.return_value = {
            "id": SID, "title": "T", "nativeConfig": native,
        }
        # persisted blocks come from the canonical nativeConfig — the
        # real write service has no slide_blocks member.
        del writes.slide_blocks
    else:
        writes.get_slide.side_effect = PresentationWriteError(
            "Tela não encontrada.",
            status_code=404,
            code="RESOURCE_NOT_FOUND",
        )
        del writes.slide_blocks
    return writes


def _dispatch(writes):
    suggest = MagicMock()
    suggest.suggest.return_value = {"suggestions": []}
    d = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock(), suggest=suggest,
    )
    d._access.resolve = MagicMock(
        return_value=SimpleNamespace(
            can_edit=True, can_read=True, level="owner",
            playlist={"id": PID, "dataDefaults": {}},
        )
    )
    d._access.actor_id = MagicMock(return_value="u1")
    return d


def _ready_plan(ops):
    return {
        "status": "ready",
        "ops": ops,
        "matchedCapabilityKeys": [],
        "clarificationKey": None,
        "reason": None,
    }


def _suggest(d, message, host=None, ops=None):
    if ops is None:
        ops = [
            {
                "op": "upsert_block",
                "block": {
                    "type": "kpi_view",
                    "frame": {"x": 0, "y": 8, "w": 18, "h": 18},
                },
            }
        ]
    plan = _ready_plan(ops)
    with (
        patch.object(
            PresentationCommandPlannerService, "plan", return_value=plan
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
        patch(
            "tv_app.application.services.editor_focus_store.editor_focus_store",
            EditorFocusStore(ttl_seconds=90),
        ),
    ):
        return d.suggest_change(
            user=_user(),
            message=message,
            host_context=host if host is not None
            else {"playlistId": PID, "slideId": SID},
            authorization=None,
        )


# ----------------------------------------------------------------------
# F1 — error handling & state integrity (E01–E10)
# ----------------------------------------------------------------------


def test_e01_slide_read_unexpected_error_never_becomes_empty_slide():
    """E01 — get_slide raising an unexpected failure must surface, not
    masquerade as 'slide has no blocks'."""
    writes = _writes()
    writes.get_slide.side_effect = RuntimeError("persistence down")
    d = _dispatch(writes)
    with pytest.raises(RuntimeError, match="persistence down"):
        _suggest(d, "crie um painel de OEE")


def test_e02_block_extraction_failure_never_discards_persisted_state():
    """E02 — a slide_blocks failure must not silently produce
    existing_blocks=[]."""
    writes = _writes()
    writes.slide_blocks = MagicMock(
        side_effect=RuntimeError("block decode boom")
    )
    d = _dispatch(writes)
    with pytest.raises(RuntimeError, match="block decode boom"):
        _suggest(d, "crie um painel de OEE")


def test_e03_legit_empty_slide_still_composes():
    """E03 — a persisted slide without blocks is a legitimate empty
    state: composition proceeds and evidence is available."""
    writes = _writes(blocks=[])
    d = _dispatch(writes)
    out = _suggest(d, "crie um painel de OEE")
    assert out["ops"]
    assert not any(op.get("op") == "delete_block" for op in out["ops"])
    ev = out.get("visualEvidence") or {}
    assert ev.get("status") == "available"
    assert ev.get("basisRevision") == "7"


def test_e04_missing_slide_reports_canonical_not_found():
    """E04 — genuine absence (typed 404) keeps the SLIDE_NOT_FOUND
    contract — it is not an error."""
    writes = _writes(slide_present=False)
    d = _dispatch(writes)
    out = _suggest(d, "crie um painel de OEE")
    ev = out.get("visualEvidence") or {}
    assert ev.get("status") == "unavailable"
    assert ev.get("failureCode") == "SLIDE_NOT_FOUND"


def test_e05_authorization_failure_propagates_not_not_found():
    """E05 — a non-NOT_FOUND write error (e.g. authorization) is never
    reclassified as legitimate absence."""
    writes = _writes()
    writes.get_slide.side_effect = PresentationWriteError(
        "Acesso negado.", status_code=403, code="ACCESS_DENIED",
    )
    d = _dispatch(writes)
    with pytest.raises(PresentationWriteError) as excinfo:
        _suggest(d, "crie um painel de OEE")
    assert excinfo.value.code == "ACCESS_DENIED"


def test_e06_preview_service_defect_is_diagnosable():
    """E06 — a programming error inside the preview service must not be
    relabelled PREVIEW_UNAVAILABLE."""
    writes = _writes(blocks=[])
    d = _dispatch(writes)
    broken = MagicMock(spec=SlidePreviewRenderService)
    broken.build_preview_payload.side_effect = TypeError("None is not subscriptable")
    with patch(
        "tv_app.application.services.data.slide_preview_render_service"
        ".get_slide_preview_render_service",
        return_value=broken,
    ):
        with pytest.raises(TypeError):
            _suggest(d, "crie um painel de OEE")


def test_e07_editor_disconnected_keeps_editor_not_open():
    """E07 — editor offline is a legitimate operational state and stays
    EDITOR_NOT_OPEN."""
    writes = _writes(blocks=[])
    d = _dispatch(writes)
    out = _suggest(d, "crie um painel de OEE")
    ev = out.get("visualEvidence") or {}
    assert ev.get("status") == "available"
    rendered = ev.get("rendered") or {}
    assert rendered.get("status") == "unavailable"
    assert rendered.get("failureCode") == "EDITOR_NOT_OPEN"


def test_e08_design_audit_defect_is_diagnosable():
    """E08 — a defect in the structural audit must surface instead of
    being flattened into PREVIEW_UNAVAILABLE."""
    writes = _writes(blocks=[])
    d = _dispatch(writes)
    with patch(
        "tv_app.application.gpt_actions.dispatch_service"
        ".DesignIntelligenceService.design_audit",
        side_effect=AttributeError("audit internals broken"),
    ):
        with pytest.raises(AttributeError):
            _suggest(d, "crie um painel de OEE")


def test_e09_no_slide_context_preserves_contract():
    """E09 — without playlistId/slideId no slide read happens and no
    visualEvidence is fabricated."""
    writes = _writes()
    d = _dispatch(writes)
    out = _suggest(d, "crie um painel de OEE", host={"playlistId": PID})
    writes.get_slide.assert_not_called()
    assert "visualEvidence" not in out


def test_e10_full_success_evidence_contract():
    """E10 — happy path: persisted slide read, URL minted, revision and
    structural audit present, rendered honestly gated by live editor."""
    writes = _writes()
    d = _dispatch(writes)
    out = _suggest(d, "crie um painel de OEE")
    ev = out.get("visualEvidence") or {}
    assert ev.get("status") == "available"
    assert isinstance(ev.get("previewUrl"), str) and ev["previewUrl"]
    assert ev.get("basisRevision") == "7"
    assert isinstance(ev.get("designAudit"), dict)
    rendered = ev.get("rendered") or {}
    assert rendered.get("status") in {"unavailable", "ready"}
    # persisted kpi block is reused (upsert keeps its id, no duplicate)
    kpi = next(
        op for op in out["ops"]
        if op.get("op") == "upsert_block"
        and str((op.get("block") or {}).get("type") or "") == "kpi_view"
    )
    assert kpi["block"].get("id") == "blk-kpi"


# ----------------------------------------------------------------------
# F2 — composition & reconciliation (C*)
# ----------------------------------------------------------------------


def _recipe_ops():
    ops = PresentationRecipeService.ops_for_recipe("TV_KPI_SERIES_TABLE")
    assert any(
        isinstance(o, dict)
        and str((o.get("block") or {}).get("type") or "") == "table_view"
        for o in ops
    ), "fixture requires the table_view scaffold"
    return [dict(o) for o in ops]


def _binding_blocks(*types):
    return [
        {"blockType": t, "state": "NEEDS_CONTEXT", "candidates": []}
        for t in types
    ]


def _enrich(message, existing, ops=None, blocks=None, request_goals=None):
    payload = {
        "ops": ops if ops is not None else _recipe_ops(),
        "interpretedGoals": [],
        "bindingPlan": {
            "state": "NEEDS_CONTEXT",
            "blocks": list(blocks if blocks is not None else []),
        },
    }
    GptActionsDispatchService._enrich_composition_ops(
        payload,
        list(blocks if blocks is not None else []),
        message,
        request_goals=request_goals or set(),
        existing_blocks=list(existing),
    )
    return payload["ops"]


def test_c01_explicit_redesign_removes_obsolete_persisted_table():
    """C01 — explicit redesign: a persisted table_view must leave via
    delete_block — including when the brief mentions the table only to
    remove it (§9 variant)."""
    ops = _enrich(
        "Redesenhe o slide atual como um dashboard de OEE realizado, "
        "tendência dos últimos 30 dias e meta oficial. Remova a tabela "
        "antiga que não faz parte desta composição.",
        existing=[{"id": "tbl-old", "type": "table_view", "frame": {}}],
        blocks=_binding_blocks("kpi_view", "chart_view", "table_view"),
    )
    assert {"op": "delete_block", "blockId": "tbl-old"} in ops
    assert not any(
        op.get("op") == "upsert_block"
        and str((op.get("block") or {}).get("type") or "") == "table_view"
        for op in ops
    )


def test_c02_create_briefing_never_deletes_persisted_blocks():
    """C02 — creation/additive vocabulary ('design' as a quality
    attribute, not a replace intent) preserves persisted blocks."""
    ops = _enrich(
        "Crie um dashboard com design moderno para acompanhar o OEE",
        existing=[{"id": "tbl-old", "type": "table_view", "frame": {}}],
        blocks=_binding_blocks("kpi_view", "chart_view", "table_view"),
    )
    assert not any(op.get("op") == "delete_block" for op in ops)


def test_c03_legitimate_5s_table_is_reused_not_deleted():
    """C03 — redesign of a 5S audit panel keeps the needed table via id
    reuse — legitimate tables are never swept."""
    ops = _enrich(
        "Redesenhe o painel de auditorias 5S e não conformidades",
        existing=[{"id": "tbl-old", "type": "table_view", "frame": {}}],
        blocks=_binding_blocks("kpi_view", "chart_view", "table_view"),
    )
    table = next(
        op for op in ops
        if op.get("op") == "upsert_block"
        and str((op.get("block") or {}).get("type") or "") == "table_view"
    )
    assert table["block"].get("id") == "tbl-old"
    assert not any(
        op.get("op") == "delete_block" and op.get("blockId") == "tbl-old"
        for op in ops
    )


def test_c05_c09_no_duplicate_and_idempotent_proposal():
    """C05/C09 — composition never duplicates a persisted block and a
    repeated proposal is stable."""
    existing = [{"id": "blk-kpi", "type": "kpi_view", "frame": {}}]
    blocks = _binding_blocks("kpi_view", "chart_view", "table_view")
    ops1 = _enrich("crie um painel de OEE", existing, blocks=blocks)
    ops2 = _enrich("crie um painel de OEE", existing, blocks=blocks)
    upserts1 = [
        (o.get("block") or {}).get("id")
        for o in ops1 if o.get("op") == "upsert_block"
    ]
    emitted_ids = [i for i in upserts1 if i]
    assert len(emitted_ids) == len(set(emitted_ids))
    assert ops1 == ops2


def test_c06_existing_block_ids_reused():
    """C06 — a persisted block of the same role is updated in place,
    never re-added under a fresh id."""
    ops = _enrich(
        "crie um painel de OEE",
        existing=[{"id": "blk-kpi", "type": "kpi_view", "frame": {}}],
        blocks=_binding_blocks("kpi_view"),
    )
    kpi = next(
        op for op in ops
        if op.get("op") == "upsert_block"
        and str((op.get("block") or {}).get("type") or "") == "kpi_view"
    )
    assert kpi["block"].get("id") == "blk-kpi"


def test_c11_source_ambiguity_never_forced_resolved():
    """C11 — genuinely ambiguous candidates keep the plan honest —
    enrich never fabricates RESOLVED."""
    blocks = [
        {
            "blockType": "kpi_view",
            "state": "NEEDS_SOURCE_SELECTION",
            "candidates": [
                {
                    "operationId": "get_a_metric",
                    "goals": ["oee"],
                    "metaShape": "scalar",
                    "score": 9.0,
                },
                {
                    "operationId": "get_b_metric",
                    "goals": ["oee"],
                    "metaShape": "scalar",
                    "score": 9.0,
                },
            ],
        }
    ]
    payload = {
        "ops": [
            {
                "op": "upsert_block",
                "block": {"type": "kpi_view", "frame": {}},
            }
        ],
        "interpretedGoals": [],
        "bindingPlan": {"state": "NEEDS_SOURCE_SELECTION",
                        "blocks": [dict(blocks[0])]},
    }
    GptActionsDispatchService._enrich_composition_ops(
        payload, [dict(blocks[0])], "crie um painel de OEE",
        request_goals={"oee"}, existing_blocks=[],
    )
    assert payload["bindingPlan"]["state"] == "NEEDS_SOURCE_SELECTION"


def test_c12_gibberish_never_triggers_redesign_sweep():
    """C12 — insufficient/gibberish input produces no destructive
    reconciliation."""
    ops = _enrich(
        "quero uma TV mostrando xyzzy foobar",
        existing=[{"id": "tbl-old", "type": "table_view", "frame": {}}],
        blocks=_binding_blocks("table_view"),
    )
    assert not any(op.get("op") == "delete_block" for op in ops)


def _enrich_kpi(candidates, request_goals):
    blocks = [
        {"blockType": "kpi_view", "state": "NEEDS_SOURCE_SELECTION",
         "candidates": candidates}
    ]
    payload = {
        "ops": [
            {"op": "upsert_block",
             "block": {"type": "kpi_view", "frame": {}}}
        ],
        "interpretedGoals": [],
        "bindingPlan": {"state": "NEEDS_SOURCE_SELECTION",
                        "blocks": [dict(blocks[0])]},
    }
    GptActionsDispatchService._enrich_composition_ops(
        payload, [dict(blocks[0])], "crie um painel de OEE",
        request_goals=request_goals, existing_blocks=[],
    )
    return payload["ops"]


def test_c04a_meta_source_never_binds_realized_kpi():
    """C04 — with only target-role candidates the realized KPI stays
    honestly unbound (meta nunca substitui realizado)."""
    ops = _enrich_kpi(
        [
            {"operationId": "get_si_indicator_production_oee_meta",
             "goals": ["meta"], "metaShape": "scalar", "score": 9.0},
            {"operationId": "get_si_indicator_production_costs_meta",
             "goals": ["meta"], "metaShape": "scalar", "score": 8.0},
        ],
        {"meta"},
    )
    realized_ds = [
        o for o in ops
        if o.get("op") == "upsert_data_source"
        and o.get("blockId") == "ds_kpi_view"
    ]
    assert realized_ds == []


def test_c04b_realized_candidate_wins_over_meta_for_realized_kpi():
    """C04 — when a realized-role source exists it binds the realized
    KPI; target-role sources only feed the dedicated meta KPI."""
    ops = _enrich_kpi(
        [
            {"operationId": "get_si_indicator_production_oee_realized",
             "goals": ["oee"], "metaShape": "scalar", "score": 9.0},
            {"operationId": "get_si_indicator_production_oee_meta",
             "goals": ["meta"], "metaShape": "scalar", "score": 9.0},
        ],
        {"oee", "meta"},
    )
    realized_ds = next(
        o for o in ops
        if o.get("op") == "upsert_data_source"
        and o.get("blockId") == "ds_kpi_view"
    )
    assert realized_ds["operationId"] == (
        "get_si_indicator_production_oee_realized"
    )
    meta_ds = next(
        o for o in ops
        if o.get("op") == "upsert_data_source"
        and o.get("blockId") == "ds_meta_view"
    )
    assert meta_ds["operationId"] == (
        "get_si_indicator_production_oee_meta"
    )


def test_c10_candidate_vs_persisted_preview_are_distinct():
    """C10 — the suggest visualEvidence carries basisRevision of the
    PERSISTED state; the candidate preview lives in the mutation
    PREPARE contract (separate field, separate revision basis)."""
    out = _suggest(_dispatch(_writes(blocks=[])), "crie um painel de OEE")
    ev = out.get("visualEvidence") or {}
    assert ev.get("basisRevision") == "7"
    assert "candidatePreview" not in ev
