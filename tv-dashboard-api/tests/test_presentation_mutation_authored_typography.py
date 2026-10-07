"""Authored typography survives PresentationMutation post-processing (part chrome)."""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)

_GROUP = "grp_goal_card"
_USER = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")


def _goal_card_config(*, goal_font: int = 65, label_font: int = 28) -> dict[str, Any]:
    """Composed group: primary 76 + projected value sibling at the 0.85 floor (65)."""
    return {
        "version": 5,
        "blocks": [
            {
                "id": "blk-primary",
                "type": "text",
                "groupId": _GROUP,
                "content": "95,0%",
                "style": {"fontSize": 76},
                "frame": {"x": 6, "y": 10, "w": 40, "h": 16},
            },
            {
                "id": "blk-label",
                "type": "text",
                "groupId": _GROUP,
                "content": "Meta",
                "style": {"fontSize": label_font},
                "frame": {"x": 6, "y": 28, "w": 20, "h": 8},
            },
            {
                "id": "blk-goal",
                "type": "text",
                "groupId": _GROUP,
                "content": "",
                "textProjection": {"field": "reference_goal", "format": "percent"},
                "style": {"fontSize": goal_font},
                "frame": {"x": 28, "y": 28, "w": 18, "h": 10},
            },
            {
                "id": "blk-footer",
                "type": "text",
                "content": "Atualizado diariamente",
                "style": {"fontSize": 24},
                "frame": {"x": 6, "y": 86, "w": 60, "h": 6},
            },
        ],
    }


def _preview(native_config: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    persisted = copy.deepcopy(native_config)

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "revision": 1, "dataDefaults": {}}

        def get_slide(self, sid, playlist_id=None):
            return {"id": str(sid), "nativeConfig": copy.deepcopy(persisted)}

    return PresentationPatchService(repo=_Repo()).preview(
        {
            "target": {"playlistId": str(uuid4()), "slideId": str(uuid4())},
            "ops": ops,
            "catalogVersion": PresentationOpsContentService.catalog_version(),
        },
        user=_USER,
    )


def _font(native_config: dict[str, Any], block_id: str) -> Any:
    block = next(b for b in native_config["blocks"] if b.get("id") == block_id)
    return block["style"].get("fontSize")


def _bump(block_id: str, delta: int) -> dict[str, Any]:
    return {"op": "bump_font_size", "blockId": block_id, "deltaSteps": delta}


def test_baseline_group_at_floor_is_stable():
    result = _preview(_goal_card_config(), [_bump("blk-footer", 1)])
    assert _font(result["nativeConfig"], "blk-goal") == 65
    assert _font(result["nativeConfig"], "blk-primary") == 76


def test_original_grouped_projected_value_decrease_persists_in_candidate():
    result = _preview(_goal_card_config(), [_bump("blk-goal", -1)])
    assert result["appliedOps"] == ["bump_font_size"]
    assert _font(result["nativeConfig"], "blk-goal") == 63


def test_explicit_absolute_font_size_below_group_ratio_is_kept():
    result = _preview(
        _goal_card_config(),
        [
            {
                "op": "upsert_block",
                "block": {"id": "blk-goal", "type": "text", "style": {"fontSize": 40}},
            }
        ],
    )
    assert _font(result["nativeConfig"], "blk-goal") == 40


def test_persisted_authored_size_survives_later_unrelated_mutation():
    result = _preview(_goal_card_config(goal_font=63), [_bump("blk-footer", 1)])
    cfg = result["nativeConfig"]
    assert _font(cfg, "blk-footer") == 26
    assert _font(cfg, "blk-goal") == 63


def test_decrease_then_unrelated_mutation_keeps_authored_value_end_to_end():
    first = _preview(_goal_card_config(), [_bump("blk-goal", -1)])
    assert _font(first["nativeConfig"], "blk-goal") == 63
    second = _preview(first["nativeConfig"], [_bump("blk-footer", 1)])
    assert _font(second["nativeConfig"], "blk-goal") == 63
    third = _preview(second["nativeConfig"], [_bump("blk-primary", 1)])
    assert _font(third["nativeConfig"], "blk-goal") == 63
    assert _font(third["nativeConfig"], "blk-primary") == 78


def test_multiple_authored_group_sizes_survive_unrelated_mutation():
    result = _preview(
        _goal_card_config(goal_font=50, label_font=18),
        [_bump("blk-footer", -1)],
    )
    cfg = result["nativeConfig"]
    assert _font(cfg, "blk-goal") == 50
    assert _font(cfg, "blk-label") == 18


def test_increase_in_group_still_applies():
    result = _preview(_goal_card_config(), [_bump("blk-goal", 1)])
    assert _font(result["nativeConfig"], "blk-goal") == 67


def test_non_projected_group_label_decrease_still_applies():
    result = _preview(_goal_card_config(), [_bump("blk-label", -1)])
    assert _font(result["nativeConfig"], "blk-label") == 26


def test_negative_ungrouped_value_decrease_unchanged():
    cfg = _goal_card_config()
    for block in cfg["blocks"]:
        block.pop("groupId", None)
    result = _preview(cfg, [_bump("blk-goal", -1)])
    assert _font(result["nativeConfig"], "blk-goal") == 63


def test_legibility_minimum_still_enforced_on_authored_size():
    result = _preview(
        _goal_card_config(),
        [
            {
                "op": "upsert_block",
                "block": {"id": "blk-goal", "type": "text", "style": {"fontSize": 10}},
            }
        ],
    )
    assert _font(result["nativeConfig"], "blk-goal") == 16


def test_composed_recipe_creation_still_gets_initial_proportional_typography():
    ops = PresentationRecipeService.ops_for_recipe("TV_COMPOSED_DATA_CARD")
    result = _preview({"version": 5, "blocks": []}, ops)
    group = [
        b for b in result["nativeConfig"]["blocks"] if b.get("groupId") == "grp_composed_data_card"
    ]
    by_type = {b["type"]: b for b in group}
    value_font = by_type["text"]["style"]["fontSize"]
    assert value_font == 56
    # Shape typography was not authored by the recipe → group default applies.
    assert by_type["shape"]["style"]["fontSize"] >= round(value_font * 0.85)
    # Heading size authored by the recipe is kept above the legibility minimum.
    assert by_type["heading"]["style"]["fontSize"] >= 16
