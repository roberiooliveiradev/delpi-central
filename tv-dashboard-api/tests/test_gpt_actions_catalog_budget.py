"""Regression gates for gpt_get_catalog Actions budget (ResponseTooLargeError).

Custom GPT may serialize with ensure_ascii escapes; envelope + Portuguese text
must stay under GPT_ACTIONS_RESPONSE_MAX_BYTES. Compact projection is allowed
to drop frames/examples, but must keep live directives and design authority.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
from tv_app.application.gpt_actions.capability_surface import build_capability_surface
from tv_app.application.gpt_actions.response_compact import (
    GPT_ACTIONS_RESPONSE_MAX_BYTES,
    actions_response_sizes,
    utf8_size,
)
from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    clear_vista_agent_intelligence_cache,
)
from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
    clear_presentation_recipes_cache,
)
from tv_app.main import app

# Catch slow drift before the hard ceiling fails in production.
_MIN_ASCII_ENVELOPE_HEADROOM = 2 * 1024


def _clear_caches() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_ops_content_cache()
    clear_presentation_recipes_cache()


def _catalog_document() -> dict:
    _clear_caches()
    doc = PresentationOpsContentService.capability_catalog_document()
    doc["capability_surface"] = build_capability_surface()
    return doc


async def _bypass_auth_middleware(request, call_next):
    return await call_next(request)


def _superadmin():
    return SimpleNamespace(is_superadmin=True, permissions=[], id="catalog-budget-tester")


def test_catalog_budget_unicode_ascii_and_envelope():
    doc = _catalog_document()
    sizes = actions_response_sizes(doc)
    for label, size in sizes.items():
        assert size <= GPT_ACTIONS_RESPONSE_MAX_BYTES, (
            f"gpt_get_catalog {label} is {size} bytes "
            f"(limit {GPT_ACTIONS_RESPONSE_MAX_BYTES})"
        )
    assert sizes["ascii"] >= sizes["unicode"]
    assert sizes["envelopeAscii"] >= sizes["ascii"]


def test_catalog_budget_keeps_ascii_envelope_headroom():
    """Sibling: leave free bytes so the next additive field does not land on the edge."""
    doc = _catalog_document()
    sizes = actions_response_sizes(doc)
    headroom = GPT_ACTIONS_RESPONSE_MAX_BYTES - sizes["envelopeAscii"]
    assert headroom >= _MIN_ASCII_ENVELOPE_HEADROOM, (
        f"ascii envelope headroom is only {headroom} bytes "
        f"(need ≥ {_MIN_ASCII_ENVELOPE_HEADROOM}); compact further before shipping."
    )


def test_actions_recipe_projection_omits_blueprint_frames():
    """Positive compact: Actions sees slots; negative: frames stay on full recipes."""
    _clear_caches()
    actions = PresentationRecipeService.catalog_projection_for_actions()
    full = PresentationRecipeService.catalog_projection()
    assert "TV_KPI_ROW_2" in actions["recipes"]
    blueprint = actions["recipes"]["TV_KPI_ROW_2"]["blueprint"]
    assert blueprint["slots"]
    assert all("frame" not in slot for slot in blueprint["slots"])
    assert all(slot.get("id") and slot.get("role") for slot in blueprint["slots"])

    full_bp = full["recipes"]["TV_KPI_ROW_2"]["blueprint"]
    assert any(
        isinstance(slot.get("frame"), dict) for slot in full_bp["slots"] if isinstance(slot, dict)
    )
    assert utf8_size(actions) < utf8_size(full)


def test_actions_tokens_stay_slim_without_losing_gates():
    _clear_caches()
    tokens = PresentationRecipeService.catalog_projection_for_actions()["designTokens"]
    assert tokens["safeMargin"] is not None
    assert "kpiHero" in tokens["typeScale"]
    assert tokens["typography"]["kpiHero"]["minTvSize"] == 64
    assert "recommendedMaxLines" not in tokens["typography"]["kpiHero"]
    assert "lineHeight" not in tokens["typography"]["kpiHero"]
    brand = tokens["brand"]
    assert brand.get("accent")
    assert "themes" not in brand
    hints = tokens["visualImpactHints"]
    assert hints["temporalChartDefault"] == "area"
    assert "composeWith" in hints


def test_design_intelligence_catalog_authority_survives_compaction():
    doc = _catalog_document()
    design = doc["capability_surface"]["designIntelligence"]
    assert design["authority"] == "design_intelligence.json"
    specs = design["componentSpecs"]
    assert "kpi_view" in specs
    assert "chart_view" in specs
    assert "avoidFor" in specs["chart_view"]
    # Actions projection must stay smaller than the raw content file payload.
    raw = DesignIntelligenceService.catalog_projection()
    assert utf8_size(design) <= utf8_size(raw) + 64


def test_catalog_keeps_eight_actions_and_core_mutation_ops():
    doc = _catalog_document()
    assert len(GPT_ACTIONS_OPERATION_IDS) == 8
    assert "re_layer_playlist_filters" in (doc.get("operations") or {})
    directives = doc["capability_surface"]["agent_directives"]
    assert directives["object_resolution"]["principle"] == "ALTER_EXISTING_BEFORE_CREATE"
    assert "TV_KPI_HERO" in directives["presentation_recipes"]["catalog"]["recipes"]
    assert "mcp_delia" in directives


def test_http_catalog_response_fits_actions_budget():
    """Wiring: the real HTTP JSON body must also fit the ascii-escaped ceiling."""
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.gpt_actions_routes.resolve_user",
            return_value=_superadmin(),
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.get("/gpt-actions/v1/catalog")
    assert response.status_code == 200
    body = response.json()
    sizes = actions_response_sizes(body.get("data") or {})
    assert sizes["envelopeAscii"] <= GPT_ACTIONS_RESPONSE_MAX_BYTES
    # Raw response bytes (framework encoding) must also stay under the ceiling.
    assert len(response.content) <= GPT_ACTIONS_RESPONSE_MAX_BYTES
