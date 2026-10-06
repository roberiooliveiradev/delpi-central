"""VISTA unified owner boundary — Actions + MCP over one canonical intelligence.

Proves the core task invariant: a single owner-side source feeds both
transports. Covers:

- MCP ``suggest_change`` (ANALYSIS) delegating to the same dispatch/materializer
  the Actions transport uses — no copied planner, no persistence, no AuthZ;
- capability_surface canonical model → derived per-transport projections
  (no gpt_* mechanics in the MCP projection, no bare MCP names in Actions);
- single-source parity_map driving Actions name projection;
- knowledge single-source: one intelligence document feeds both projections;
- quality fail-safes: gradient endpoints, image/unknown bg, all-or-nothing
  coordinated overlap relayout under subset scope.
"""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tv_app.application.gpt_actions.capability_surface import build_capability_surface
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
)
from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)
from tv_app.application.services.data.safe_auto_fix_service import SafeAutoFixService
from tv_app.application.services.data.slide_layout_quality_service import (
    CONTRAST_MIN_RATIO,
    _contrast_ratio,
    _slide_bg_colors,
    safe_contrast_color,
)
from tv_app.interface.mcp import tool_bridge


def _writer():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read", "tv-dashboard.write"],
        roles=[],
        groups=[],
        id="writer-1",
        email="writer@delpi.local",
    )


class _ctx:
    def __init__(self, user=None, authorization: str | None = "Bearer test"):
        self.user = user
        self.authorization = authorization
        self._u = None
        self._a = None

    def __enter__(self):
        if self.user is not None:
            self._u = set_current_user(self.user)
        self._a = set_request_authorization(self.authorization)
        return self

    def __exit__(self, *exc):
        if self._u is not None:
            reset_current_user(self._u)
        if self._a is not None:
            reset_request_authorization(self._a)


def _test_dispatch(**overrides) -> GptActionsDispatchService:
    kwargs = dict(repo=MagicMock(), writes=MagicMock(), commit=MagicMock())
    kwargs.update(overrides)
    return GptActionsDispatchService(**kwargs)


# ---------------------------------------------------------------------------
# MCP suggest_change — thin adapter over the shared materializer
# ---------------------------------------------------------------------------


def test_suggest_change_requires_auth():
    with _ctx(None, None):
        result = tool_bridge.tool_suggest_change(message="adicione um texto")
    assert result.is_error is True
    assert result.structured_content["httpStatus"] == 401


def test_suggest_change_delegates_with_host_context():
    seen = {}

    def _capture(*, user, message, host_context, authorization):
        seen.update(
            user=user,
            message=message,
            host_context=host_context,
            authorization=authorization,
        )
        return {"status": "ready", "ops": []}

    with _ctx(_writer(), "Bearer user-token"), patch.object(
        tool_bridge._dispatch, "suggest_change", side_effect=_capture
    ):
        result = tool_bridge.tool_suggest_change(
            message="adicione um texto 'x' neste slide",
            playlist_id="p1",
            slide_id="s1",
            selected_block_id="b1",
            host_context={"extra": "kept"},
        )
    assert result.is_error is False
    assert seen["message"].startswith("adicione")
    assert seen["host_context"]["playlistId"] == "p1"
    assert seen["host_context"]["slideId"] == "s1"
    assert seen["host_context"]["selectedBlockId"] == "b1"
    assert seen["host_context"]["extra"] == "kept"
    assert seen["authorization"] == "Bearer user-token"


def test_suggest_change_preserves_domain_error():
    with _ctx(_writer()), patch.object(
        tool_bridge._dispatch,
        "suggest_change",
        side_effect=GptActionsError("Inválido.", code="INVALID_CHANGE", status_code=422),
    ):
        result = tool_bridge.tool_suggest_change(message="x")
    assert result.is_error is True
    assert result.structured_content["code"] == "INVALID_CHANGE"


def test_suggest_change_requires_message():
    with _ctx(_writer()):
        result = tool_bridge.tool_suggest_change(message="   ")
    assert result.is_error is True
    assert result.structured_content["httpStatus"] == 422


def test_mcp_domain_materialization_no_persist_no_authz():
    """Representative intent through MCP: same canonical materializer,
    candidate ops only — nothing persisted, no permission granted."""
    dispatch = _test_dispatch()
    with _ctx(_writer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_suggest_change(
            message="adicione um texto 'delia deu certo' neste slide",
            host_context={"playlistId": "p1", "slideId": "s1"},
        )
    assert result.is_error is False
    data = result.structured_content["data"]
    assert data["status"] == "ready"
    assert any(op.get("op") == "upsert_block" for op in data["ops"])
    # ANALYSIS purity: persistence ports never touched.
    assert dispatch._repo.method_calls == []
    assert dispatch._writes.method_calls == []
    assert dispatch._commit.method_calls == []


def test_actions_materialization_same_application_service():
    """Actions dispatch and MCP bridge produce semantically equivalent output
    because both call the same owner materializer."""
    dispatch = _test_dispatch()
    actions_payload = dispatch.suggest_change(
        user=_writer(),
        message="adicione um texto 'delia deu certo' neste slide",
        host_context={"playlistId": "p1", "slideId": "s1"},
        authorization=None,
    )
    with _ctx(_writer()), patch.object(tool_bridge, "_dispatch", dispatch):
        mcp = tool_bridge.tool_suggest_change(
            message="adicione um texto 'delia deu certo' neste slide",
            host_context={"playlistId": "p1", "slideId": "s1"},
        )
    data = mcp.structured_content["data"]
    assert data["status"] == actions_payload["status"] == "ready"
    assert data["matchedCapabilityKeys"] == actions_payload["matchedCapabilityKeys"]
    assert data["ops"][0]["op"] == actions_payload["ops"][0]["op"] == "upsert_block"
    assert data["ops"][0]["block"]["content"] == "delia deu certo"
    assert data["confirmationPolicy"] == actions_payload["confirmationPolicy"]


def test_fuzzy_intent_same_recognition():
    """Accent/typo-tolerant recognition reaches MCP through the same service."""
    dispatch = _test_dispatch()
    with _ctx(_writer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_suggest_change(
            message="adicone um txto",
            host_context={"playlistId": "p1", "slideId": "s1"},
        )
    data = result.structured_content["data"]
    assert data["status"] == "ready"
    assert data["ops"][0]["op"] == "upsert_block"


def test_selected_object_resolution_via_context():
    """Caller-provided context resolves references — context is not AuthZ."""
    dispatch = _test_dispatch()
    with _ctx(_writer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_suggest_change(
            message="remova este bloco",
            host_context={
                "playlistId": "p1",
                "slideId": "s1",
                "selectedBlockId": "blk_target",
            },
        )
    data = result.structured_content["data"]
    assert data["status"] in {"ready", "clarification", "selection_pending"}
    blob = json.dumps(data, ensure_ascii=False)
    if data["status"] == "ready":
        assert "blk_target" in blob


# ---------------------------------------------------------------------------
# Capability surface — canonical model, derived projections
# ---------------------------------------------------------------------------


def _blob(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def test_mcp_projection_has_no_actions_mechanics():
    surface = build_capability_surface(transport="mcp")
    # Exclude agent_directives: it carries the labeled parity_map registry
    # (gpt_* -> mcp) which is the compatibility index itself.
    core = {k: v for k, v in surface.items() if k != "agent_directives"}
    blob = _blob(core)
    assert "gpt_" not in blob
    assert "commit_now" not in blob
    assert "additive_single_shot" not in blob


def test_actions_projection_uses_actions_names():
    surface = build_capability_surface(transport="actions")
    wf = surface["workflows"][0]
    assert "gpt_suggest_change" in wf["write_operations"]
    assert "gpt_preview_change" in wf["write_operations"]
    assert "gpt_commit_change" in wf["write_operations"]
    policy = wf["prepare_act_policy"]
    assert policy["prepare"] == "gpt_preview_change"
    assert policy["commit"] == "gpt_commit_change"
    assert policy["additive_single_shot"]["operation"] == "gpt_preview_change"
    assert policy["additive_single_shot"]["commit_now"] is True
    # No bare MCP names survive the projection.
    blob = _blob({k: v for k, v in surface.items() if k != "agent_directives"})
    for bare in ('"prepare_change"', '"commit_proposal"', '"get_catalog"'):
        assert bare not in blob


def test_one_parity_map_change_flows_to_both_projections(monkeypatch):
    """§51: change one canonical transport-mapping entry — the Actions
    projection follows automatically; MCP keeps the neutral name."""
    doc = copy.deepcopy(VistaAgentIntelligenceService.document())
    parity = doc["surface_parity"]["parity_map"]
    parity["gpt_routes_renamed"] = parity.pop("gpt_search_data_routes")
    monkeypatch.setattr(
        VistaAgentIntelligenceService,
        "document",
        classmethod(lambda cls: doc),
    )
    actions = build_capability_surface(transport="actions")
    mcp = build_capability_surface(transport="mcp")
    search = next(a for a in actions["analyses"] if a["id"] == "data_route_search")
    assert search["read_operations"] == ["gpt_routes_renamed"]
    search_mcp = next(a for a in mcp["analyses"] if a["id"] == "data_route_search")
    assert search_mcp["read_operations"] == ["search_data_routes"]


def test_new_capability_policy_derives_both_projections(monkeypatch):
    """§52: a semantic fact added to the canonical ops catalog reaches both
    projections — no separate lists to update."""
    ops = dict(PresentationOpsContentService.operations())
    ops["fixture_delete_everything"] = {"confirmationPolicy": "confirm"}
    monkeypatch.setattr(
        PresentationOpsContentService,
        "operations",
        classmethod(lambda cls: ops),
    )
    for transport in ("actions", "mcp"):
        surface = build_capability_surface(transport=transport)
        wf = surface["workflows"][0]
        assert "fixture_delete_everything" in wf["destructive_typed_ops"]
        assert wf["typed_ops_count"] == len(ops)


def test_knowledge_single_source_both_transports(monkeypatch):
    """§53: shared intelligence sections come from one canonical document —
    a change once appears in both transport projections."""
    doc = copy.deepcopy(VistaAgentIntelligenceService.document())
    doc.setdefault("object_resolution", {})["marker_fixture"] = "SINGLE_SOURCE_PROOF"
    monkeypatch.setattr(
        VistaAgentIntelligenceService,
        "document",
        classmethod(lambda cls: doc),
    )
    for transport in ("actions", "mcp"):
        directives = VistaAgentIntelligenceService.agent_directives(
            transport=transport
        )
        assert directives["object_resolution"]["marker_fixture"] == "SINGLE_SOURCE_PROOF"


def test_mcp_directives_drop_actions_write_mechanics():
    """The Actions write_flow variant must not ship its callable mechanics
    (gpt_* / commit_now / confirmation.confirmed) to the MCP projection."""
    directives = VistaAgentIntelligenceService.agent_directives(transport="mcp")
    write_flow = directives.get("write_flow") or {}
    assert "additive" not in write_flow
    assert "destructive" not in write_flow
    # Neutral guidance survives.
    assert "forbidden_handles" in write_flow
    wf_blob = _blob(write_flow)
    assert "commit_now" not in wf_blob
    assert "gpt_" not in wf_blob


def test_mcp_projection_has_no_actions_names_or_envelope_mechanics():
    """GPT_TOOL_NAMES_IN_MCP_CALLABLE_CONTRACT = 0 and
    COMMIT_NOW_IN_MCP_PREPARE = 0: the whole MCP catalog must not carry
    gpt_* tokens or Actions-envelope mechanics anywhere except the
    ``surface_parity`` registry (whose gpt_* keys ARE the canonical
    Actions-name record, non-callable metadata by definition)."""
    catalog = build_capability_surface(transport="mcp")
    agent_directives = catalog.get("agent_directives") or {}
    parity_registry = agent_directives.pop("surface_parity", None)
    assert parity_registry  # canonical parity record still shipped
    blob = _blob(catalog)
    assert "gpt_" not in blob
    assert "commit_now" not in blob
    assert "additive_single_shot" not in blob
    assert "action_surface_budget" not in blob
    assert "confirmation.confirmed" not in blob
    # Neutral semantics survive the neutralization.
    compound = " ".join(
        (catalog.get("agent_directives") or {}).get("compound_slide", {}).get("pipeline", [])
    )
    assert "dateRangePreset" in compound
    assert "commit_proposal" in compound


# ---------------------------------------------------------------------------
# Quality fail-safes — gradient endpoints / unknown bg / coordinated overlap
# ---------------------------------------------------------------------------


def _gradient_cfg(from_color: str, to_color: str, blocks: list) -> dict:
    return {
        "version": 5,
        "background": {"type": "gradient", "from": from_color, "to": to_color},
        "blocks": blocks,
    }


def test_gradient_bg_yields_all_endpoints():
    cfg = _gradient_cfg("#05070a", "#e2e8f0", [])
    assert _slide_bg_colors(cfg) == ["#05070a", "#e2e8f0"]


def test_low_contrast_detected_against_worst_gradient_endpoint():
    """fg that passes the dark endpoint but fails the light one is still a
    low_contrast issue — the single-endpoint check would have missed it."""
    fg = "#94a3b8"
    assert _contrast_ratio(fg, "#05070a") >= CONTRAST_MIN_RATIO
    assert _contrast_ratio(fg, "#e2e8f0") < CONTRAST_MIN_RATIO
    cfg = _gradient_cfg(
        "#05070a",
        "#e2e8f0",
        [
            {
                "id": "txt-1",
                "type": "text",
                "frame": {"x": 10, "y": 10, "w": 30, "h": 10},
                "style": {"color": fg},
                "content": "x",
            }
        ],
    )
    audit = DesignIntelligenceService.design_audit(cfg)
    assert any(
        str(i.get("id") or "").startswith("low_contrast:txt-1")
        for i in audit.get("issues") or []
    )


def test_safe_contrast_color_must_pass_every_gradient_endpoint():
    """A correction is only emitted when the chosen fg is provably safe vs
    ALL endpoints — never a partial proof."""
    cfg = _gradient_cfg("#05070a", "#e2e8f0", [])
    fg = safe_contrast_color(cfg)
    if fg is not None:
        for bg in ("#05070a", "#e2e8f0"):
            ratio = _contrast_ratio(fg, bg)
            assert ratio is not None and ratio >= CONTRAST_MIN_RATIO


def test_safe_contrast_color_gradient_pair_failing_one_endpoint_fails_closed():
    """A pair whose fg satisfies only one endpoint is rejected: the owner
    never ships a correction proven safe against half a gradient."""
    cfg = _gradient_cfg("#000000", "#ffffff", [])
    tokens = {"minContrastPairs": [{"fg": "#ffffff", "bg": "#000000"}]}
    assert safe_contrast_color(cfg, tokens=tokens) is None


def test_image_background_fail_closed():
    cfg = {
        "version": 5,
        "background": {"type": "image", "value": "media/x.png"},
        "blocks": [
            {
                "id": "txt-1",
                "type": "text",
                "frame": {"x": 10, "y": 10, "w": 30, "h": 10},
                "style": {"color": "#ffffff"},
                "content": "x",
            }
        ],
    }
    assert _slide_bg_colors(cfg) == []
    assert safe_contrast_color(cfg) is None


def test_theme_bg_colors_come_from_canonical_recipes():
    """Theme backgrounds resolve from designTokens.brand.modes — the Python
    module holds only the key→mode alias, never colors."""
    dark = _slide_bg_colors({"brandThemeKey": "delpi-dark"})
    light = _slide_bg_colors({"brandThemeKey": "delpi-light"})
    assert dark and light
    assert "#05070a" in dark and "#0d2840" in dark
    assert "#f8fafc" in light
    assert _slide_bg_colors({"brandThemeKey": "nonexistent-theme"}) == []


def test_overlap_relayout_all_or_nothing_under_subset_scope():
    """Coordinated relayout touching an out-of-scope block must be dropped
    entirely — never a half-applied multi-block fix."""
    cfg = {
        "version": 5,
        "blocks": [
            {"id": "k1", "type": "kpi_view", "frame": {"x": 10, "y": 10, "w": 20, "h": 10}},
            {"id": "k2", "type": "kpi_view", "frame": {"x": 10, "y": 10, "w": 20, "h": 10}},
            {"id": "k3", "type": "kpi_view", "frame": {"x": 10, "y": 40, "w": 20, "h": 10}},
        ],
    }
    audit = DesignIntelligenceService.design_audit(cfg)
    overlap_ids = {
        str(i.get("id"))
        for i in audit.get("issues") or []
        if str(i.get("id") or "").startswith("block_overlap")
    }
    assert overlap_ids, "fixture must produce a block_overlap issue"
    # The overlap issue names only the colliding pair; the relayout would
    # also move k3 (out of scope) → the whole coordinated fix is dropped.
    ops = SafeAutoFixService.ops_for(cfg, issue_ids=overlap_ids)
    assert ops == []


def test_overlap_relayout_applies_when_fully_in_scope():
    cfg = {
        "version": 5,
        "blocks": [
            {"id": "k1", "type": "kpi_view", "frame": {"x": 10, "y": 10, "w": 20, "h": 10}},
            {"id": "k2", "type": "kpi_view", "frame": {"x": 10, "y": 10, "w": 20, "h": 10}},
        ],
    }
    ops = SafeAutoFixService.ops_for(cfg)
    moved = {str(op["block"].get("id")) for op in ops}
    assert moved == {"k1", "k2"}
