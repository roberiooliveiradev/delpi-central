"""Owner quality loop — safe layout corrections inside the PREPARE candidate.

Covers:
- context-aware low_contrast correction (never hardcoded white);
- introduced-only correction (pre-existing issues never silently mutated);
- explicit ``apply_safe_layout_fixes`` op fixing all safeAutoFix issues;
- unsafe/unknown-context issues left untouched (fail-closed, no guessing);
- PREPARE purity: corrections never persist and never run a second ACT.
"""

from __future__ import annotations

from typing import Any

import pytest

from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.presentation_mutation_telemetry import (
    reset_presentation_mutation_telemetry,
)
from tv_app.application.services.data.presentation_recipe_service import (
    clear_presentation_recipes_cache,
)
from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.slide_layout_quality_service import (
    CONTRAST_MIN_RATIO,
    _contrast_ratio,
    safe_contrast_color,
)


SLIDE_ID = "11111111-1111-1111-1111-111111111111"
PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"


class _FakeCatalog:
    def get_route(self, operation_id: str):
        return None


class _FakeRepo:
    def __init__(self, native_config: dict[str, Any] | None = None) -> None:
        self.slides: dict[str, dict[str, Any]] = {
            SLIDE_ID: {
                "id": SLIDE_ID,
                "title": "Slide A",
                "durationSec": 30,
                "isActive": True,
                "sectionId": None,
                "nativeConfig": native_config
                if isinstance(native_config, dict)
                else {"version": 5, "blocks": []},
            }
        }
        self.updated: list[dict[str, Any]] = []

    def get_slide(self, slide_id, *, playlist_id=None):
        key = str(slide_id)
        if key not in self.slides:
            from tv_app.infrastructure.persistence.repositories.playlist_repository import (
                SlideNotFoundError,
            )

            raise SlideNotFoundError(key)
        return dict(self.slides[key])

    def get_by_id(self, playlist_id):
        return {"id": str(playlist_id), "dataDefaults": {}, "revision": 7}

    def get_revision(self, playlist_id):
        return 7

    def update_slide(self, playlist_id, slide_id, payload, *, actor_user_id, reason):
        self.updated.append({"slide_id": str(slide_id), "payload": payload})
        return dict(self.slides[str(slide_id)])


class _FakeResolution:
    def resolve_blocks(self, blocks, **kwargs):
        return [dict(b) for b in blocks]


@pytest.fixture(autouse=True)
def _reset_caches():
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()
    clear_presentation_recipes_cache()
    yield
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()
    clear_presentation_recipes_cache()


@pytest.fixture
def _light_sanitize(monkeypatch):
    def _sanitize(cfg, catalog=None):
        return dict(cfg or {})

    monkeypatch.setattr(
        "tv_app.application.services.data.presentation_mutation.patch_service.sanitize_and_hydrate_comunicado_config",
        _sanitize,
    )
    monkeypatch.setattr(
        "tv_app.application.services.data.presentation_mutation.patch_service.validate_comunicado_native_config",
        lambda cfg, user=None, catalog=None: None,
    )


def _service(repo: _FakeRepo) -> PresentationPatchService:
    return PresentationPatchService(
        catalog=_FakeCatalog(),
        repo=repo,
        resolution=_FakeResolution(),
    )


def _native(blocks: list[dict[str, Any]], *, bg: str = "#ffffff") -> dict[str, Any]:
    return {
        "version": 5,
        "background": {"type": "color", "value": bg},
        "blocks": blocks,
    }


def _text_block(block_id: str, color: str) -> dict[str, Any]:
    return {
        "id": block_id,
        "type": "text",
        "frame": {"x": 10, "y": 10, "w": 30, "h": 10},
        "style": {"color": color, "fontSize": 28},
        "content": "texto",
    }


def _audit_issue_ids(cfg: dict[str, Any]) -> set[str]:
    audit = DesignIntelligenceService.design_audit(cfg)
    return {
        str(issue.get("id") or "")
        for issue in (audit.get("issues") or [])
        if isinstance(issue, dict)
    }


# ---------------------------------------------------------------------------
# safe_contrast_color — context-aware owner decision
# ---------------------------------------------------------------------------


def test_safe_contrast_color_dark_bg_returns_light_fg():
    cfg = _native([], bg="#05070a")
    fg = safe_contrast_color(cfg)
    assert fg is not None
    ratio = _contrast_ratio(fg, "#05070a")
    assert ratio is not None and ratio >= CONTRAST_MIN_RATIO


def test_safe_contrast_color_white_bg_returns_dark_fg():
    cfg = _native([], bg="#ffffff")
    fg = safe_contrast_color(cfg)
    assert fg is not None
    ratio = _contrast_ratio(fg, "#ffffff")
    assert ratio is not None and ratio >= CONTRAST_MIN_RATIO
    assert fg.lower() != "#ffffff"


def test_safe_contrast_color_mid_bg_still_provably_safe():
    cfg = _native([], bg="#808080")
    fg = safe_contrast_color(cfg)
    assert fg is not None
    ratio = _contrast_ratio(fg, "#808080")
    assert ratio is not None and ratio >= CONTRAST_MIN_RATIO


def test_safe_contrast_color_unknown_bg_returns_none():
    cfg = {"version": 5, "blocks": []}
    assert safe_contrast_color(cfg) is None


def test_safe_contrast_color_unparseable_bg_returns_none():
    cfg = _native([], bg="not-a-color")
    assert safe_contrast_color(cfg) is None


def test_safe_contrast_color_no_pairs_returns_none():
    cfg = _native([], bg="#ffffff")
    assert safe_contrast_color(cfg, tokens={"minContrastPairs": []}) is None


def test_safe_contrast_color_brand_theme_resolves():
    cfg = {"version": 5, "brandThemeKey": "delpi-dark", "blocks": []}
    fg = safe_contrast_color(cfg)
    assert fg is not None
    ratio = _contrast_ratio(fg, "#05070a")
    assert ratio is not None and ratio >= CONTRAST_MIN_RATIO


# ---------------------------------------------------------------------------
# PREPARE candidate quality loop
# ---------------------------------------------------------------------------


def test_introduced_low_contrast_corrected_inside_candidate(_light_sanitize):
    """White text created on a white slide: owner fixes inside the PREPARE
    candidate — the corrected color is what ACT would commit."""
    repo = _FakeRepo(_native([]))
    svc = _service(repo)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": _text_block("txt-new", "#ffffff"),
                }
            ],
        },
        user={"id": "u1"},
        include_fingerprint=False,
    )
    fixes = (result.get("sideEffects") or {}).get("safeFixesApplied") or []
    assert any(f.get("blockId") == "txt-new" for f in fixes)
    candidate = result["nativeConfig"]
    block = next(b for b in candidate["blocks"] if b.get("id") == "txt-new")
    new_color = str(block["style"]["color"]).lower()
    assert new_color != "#ffffff"
    ratio = _contrast_ratio(new_color, "#ffffff")
    assert ratio is not None and ratio >= CONTRAST_MIN_RATIO
    # Candidate re-audit: the introduced issue is gone.
    assert not any(
        i.startswith("low_contrast:txt-new") for i in _audit_issue_ids(candidate)
    )
    # PREPARE purity: nothing persisted.
    assert repo.updated == []


def test_preexisting_issue_never_silently_fixed(_light_sanitize):
    """A pre-existing low_contrast issue on another block is NOT silently
    corrected when the plan did not introduce it."""
    repo = _FakeRepo(_native([_text_block("txt-old", "#ffffff")]))
    svc = _service(repo)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": _text_block("txt-new", "#0f172a"),
                }
            ],
        },
        user={"id": "u1"},
        include_fingerprint=False,
    )
    fixes = (result.get("sideEffects") or {}).get("safeFixesApplied") or []
    assert not any(f.get("blockId") == "txt-old" for f in fixes)
    candidate = result["nativeConfig"]
    old = next(b for b in candidate["blocks"] if b.get("id") == "txt-old")
    assert str(old["style"]["color"]).lower() == "#ffffff"
    # The pre-existing issue remains visible in the audit — truthful evidence.
    assert any(
        i.startswith("low_contrast:txt-old") for i in _audit_issue_ids(candidate)
    )


def test_apply_safe_layout_fixes_repairs_preexisting_issues(_light_sanitize):
    """Explicit apply_safe_layout_fixes op: every safeAutoFix issue is
    corrected, including pre-existing ones the plan did not create."""
    repo = _FakeRepo(_native([_text_block("txt-old", "#ffffff")]))
    svc = _service(repo)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [{"op": "apply_safe_layout_fixes"}],
        },
        user={"id": "u1"},
        include_fingerprint=False,
    )
    fixes = (result.get("sideEffects") or {}).get("safeFixesApplied") or []
    assert any(f.get("blockId") == "txt-old" for f in fixes)
    candidate = result["nativeConfig"]
    old = next(b for b in candidate["blocks"] if b.get("id") == "txt-old")
    new_color = str(old["style"]["color"]).lower()
    assert new_color != "#ffffff"
    ratio = _contrast_ratio(new_color, "#ffffff")
    assert ratio is not None and ratio >= CONTRAST_MIN_RATIO


def test_no_safe_fix_when_context_not_provable(
    _light_sanitize, monkeypatch
):
    """Owner never guesses: if no provably-safe color exists, the issue
    stays in the audit instead of a hardcoded correction."""
    from tv_app.application.services.data.slide_layout_quality_service import (
        SlideLayoutQualityService,
    )

    monkeypatch.setattr(
        SlideLayoutQualityService,
        "design_tokens",
        classmethod(lambda cls: {}),
    )
    repo = _FakeRepo(_native([]))
    svc = _service(repo)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": _text_block("txt-new", "#ffffff"),
                },
                {"op": "apply_safe_layout_fixes"},
            ],
        },
        user={"id": "u1"},
        include_fingerprint=False,
    )
    candidate = result["nativeConfig"]
    block = next(b for b in candidate["blocks"] if b.get("id") == "txt-new")
    # No unsafe correction applied — the audit still reports the issue.
    assert str(block["style"]["color"]).lower() == "#ffffff"
    assert any(
        i.startswith("low_contrast:txt-new") for i in _audit_issue_ids(candidate)
    )


def test_apply_safe_layout_fixes_is_catalog_vocabulary():
    """The op is canonical catalog vocabulary — a provider-neutral consumer
    discovers it via get_catalog, not via central routing."""
    spec = PresentationOpsContentService.operation_spec("apply_safe_layout_fixes")
    assert isinstance(spec, dict)
    assert "apply_safe_layout_fixes" in PresentationOpsContentService.native_config_ops()
    schema = spec.get("inputSchema") or {}
    assert "op" in (schema.get("required") or [])


def test_unknown_op_still_fails_closed(_light_sanitize):
    repo = _FakeRepo(_native([]))
    svc = _service(repo)
    with pytest.raises(PresentationPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "apply_safe_layout_fixes_v2_bypass"}],
            },
            user={"id": "u1"},
            include_fingerprint=False,
        )
