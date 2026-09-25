"""RIBBON-TEXT-001 — text typography mutation authority."""

from __future__ import annotations

from tv_app.application.services.data.text_typography_service import (
    bump_font_size,
    clamp_indent_level,
    transform_content_runs_case,
    transform_text_case,
)


def test_transform_text_case_matrix():
    assert transform_text_case("olá mundo", "upper") == "OLÁ MUNDO"
    assert transform_text_case("OLÁ", "lower") == "olá"
    assert transform_text_case("olá mundo", "title").startswith("Olá")
    assert transform_text_case("olá", "toggle") == "OLÁ"
    assert transform_text_case("olá mundo", "sentence").startswith("Olá")


def test_transform_content_runs_preserves_data_ref():
    runs = [
        {"text": "meta "},
        {"text": "…", "dataRef": {"field": "filter.end_date"}},
        {"text": " fim"},
    ]
    next_runs = transform_content_runs_case(runs, "upper")
    assert next_runs[0]["text"] == "META "
    assert next_runs[1]["dataRef"]["field"] == "filter.end_date"
    assert next_runs[2]["text"] == " FIM"


def test_bump_font_size_and_indent():
    assert bump_font_size(28, 1) == 30
    assert bump_font_size(28, -1) == 26
    assert clamp_indent_level(99) == 8
    assert clamp_indent_level(-1) == 0


def test_patch_ops_transform_case_and_bump_font():
    from tv_app.application.services.data.presentation_mutation.patch_service import (
        PresentationPatchService,
    )

    svc = PresentationPatchService()
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "blk_t",
                "type": "text",
                "content": "olá mundo",
                "style": {"fontSize": 28},
            }
        ],
    }
    svc._op_transform_text_case(
        cfg, {"op": "transform_text_case", "blockId": "blk_t", "mode": "upper"}
    )
    assert cfg["blocks"][0]["content"] == "OLÁ MUNDO"
    svc._op_bump_font_size(
        cfg, {"op": "bump_font_size", "blockId": "blk_t", "deltaSteps": 1}
    )
    assert cfg["blocks"][0]["style"]["fontSize"] == 30


def test_upsert_normalizes_baseline_indent_spacing():
    from tv_app.application.services.data.presentation_mutation.patch_service import (
        PresentationPatchService,
    )
    from tv_app.application.services.data.text_typography_service import (
        normalize_block_text_style,
    )

    style = normalize_block_text_style(
        {
            "baselineShift": "super",
            "indentLevel": 99,
            "paragraphSpacingBefore": 12,
            "paragraphSpacingAfter": -1,
        }
    )
    assert style["baselineShift"] == "super"
    assert style["indentLevel"] == 8
    assert style["paragraphSpacingBefore"] == 12
    assert "paragraphSpacingAfter" not in style
    # smoke: service still importable for upsert path
    assert PresentationPatchService is not None
