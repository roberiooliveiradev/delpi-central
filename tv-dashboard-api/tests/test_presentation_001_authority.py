"""PRESENTATION-001 — defaults materialization + layout ops."""

from __future__ import annotations

from tv_app.application.services.data.block_layout_service import (
    align_blocks,
    duplicate_blocks,
    reorder_block_z,
)
from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchService,
    _with_block_defaults,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)


def setup_function() -> None:
    clear_presentation_ops_content_cache()


def test_block_defaults_cover_icon_canvas_input_metric() -> None:
    for btype in ("icon", "canvas_table", "input", "data_metric", "chart_view"):
        defaults = PresentationOpsContentService.block_defaults(btype)
        assert isinstance(defaults.get("frame"), dict)
        assert "w" in defaults["frame"]


def test_with_block_defaults_materializes_chart_options_and_kpi_parts() -> None:
    chart = _with_block_defaults({"type": "chart_view", "id": "blk_c"})
    assert chart["frame"]["y"] == 28
    assert chart["frame"]["w"] == 80
    assert isinstance(chart.get("chartOptions"), dict)
    kpi = _with_block_defaults({"type": "kpi_view", "id": "blk_k"})
    assert isinstance(kpi.get("kpiParts"), dict)
    assert "value" in kpi["kpiParts"]


def test_create_block_op_applies_defaults() -> None:
    svc = PresentationPatchService()
    cfg = {"version": 5, "blocks": []}
    block_id, _ = svc._op_create_block(
        cfg,
        {
            "op": "create_block",
            "type": "chart_view",
            "chartType": "line",
            "blockId": "blk_chart_1",
        },
    )
    assert block_id == "blk_chart_1"
    block = next(b for b in cfg["blocks"] if b["id"] == "blk_chart_1")
    assert block["type"] == "chart_view"
    assert block["chartType"] == "line"
    assert block["frame"]["w"] == 80
    assert isinstance(block.get("chartOptions"), dict)


def test_create_all_registered_default_types() -> None:
    svc = PresentationPatchService()
    types = [
        "text",
        "heading",
        "shape",
        "image",
        "video",
        "icon",
        "chart_view",
        "table_view",
        "kpi_view",
        "canvas_table",
        "input",
        "data_source",
        "data_metric",
    ]
    cfg = {"version": 5, "blocks": []}
    for i, btype in enumerate(types):
        op = {"op": "create_block", "type": btype, "blockId": f"blk_{i}"}
        if btype == "shape":
            op["shape"] = "rectangle"
        if btype == "icon":
            op["iconName"] = "Star"
        if btype == "chart_view":
            op["chartType"] = "line"
        if btype == "data_source":
            # create via upsert path needs binding — skip detailed binding here
            op = {
                "op": "upsert_block",
                "createIfMissing": True,
                "block": {
                    "id": f"blk_{i}",
                    "type": "data_source",
                    "dataBinding": {"operationId": "get_overall_equipment_effectiveness_pct"},
                },
            }
            svc._op_upsert_block(cfg, op)
            continue
        svc._op_create_block(cfg, op)
    assert len(cfg["blocks"]) == len(types)
    for block in cfg["blocks"]:
        assert isinstance(block.get("frame"), dict)
        assert block["frame"].get("w") is not None


def test_align_blocks_left() -> None:
    blocks = [
        {"id": "a", "frame": {"x": 10, "y": 10, "w": 20, "h": 10}, "style": {"zIndex": 1}},
        {"id": "b", "frame": {"x": 40, "y": 20, "w": 10, "h": 10}, "style": {"zIndex": 2}},
    ]
    changed = align_blocks(blocks, ["a", "b"], "align-left")
    assert set(changed) == {"b"}
    assert blocks[1]["frame"]["x"] == 10


def test_distribute_h_requires_three() -> None:
    blocks = [
        {"id": "a", "frame": {"x": 0, "y": 0, "w": 10, "h": 10}},
        {"id": "b", "frame": {"x": 20, "y": 0, "w": 10, "h": 10}},
    ]
    assert align_blocks(blocks, ["a", "b"], "distribute-h") == []


def test_reorder_z_bring_to_front() -> None:
    blocks = [
        {"id": "a", "style": {"zIndex": 1}, "frame": {"x": 0, "y": 0, "w": 1, "h": 1}},
        {"id": "b", "style": {"zIndex": 5}, "frame": {"x": 0, "y": 0, "w": 1, "h": 1}},
    ]
    reorder_block_z(blocks, ["a"], "bring-to-front")
    assert blocks[0]["style"]["zIndex"] == 6


def test_duplicate_blocks_new_ids() -> None:
    blocks = [
        {
            "id": "src",
            "type": "text",
            "frame": {"x": 5, "y": 5, "w": 10, "h": 10},
            "resolved": {"should": "drop"},
            "serverDisplayApplied": True,
        }
    ]
    clones = duplicate_blocks(blocks, ["src"], new_id_fn=lambda: "clone_1")
    assert len(clones) == 1
    assert clones[0]["id"] == "clone_1"
    assert "resolved" not in clones[0]
    assert clones[0]["frame"]["x"] == 7


def test_align_and_duplicate_ops_on_patch_service() -> None:
    svc = PresentationPatchService()
    cfg = {
        "version": 5,
        "blocks": [
            {"id": "a", "type": "shape", "frame": {"x": 5, "y": 5, "w": 10, "h": 10}},
            {"id": "b", "type": "shape", "frame": {"x": 30, "y": 8, "w": 10, "h": 10}},
        ],
    }
    svc._op_align_blocks(
        cfg,
        {"op": "align_blocks", "blockIds": ["a", "b"], "command": "align-top"},
    )
    ys = {b["id"]: b["frame"]["y"] for b in cfg["blocks"]}
    assert ys["a"] == ys["b"] == 5
    before = len(cfg["blocks"])
    svc._op_duplicate_blocks(cfg, {"op": "duplicate_blocks", "blockIds": ["a"]})
    assert len(cfg["blocks"]) == before + 1


def test_catalog_version_presentation_authority() -> None:
    assert "presentation-authority" in PresentationOpsContentService.catalog_version()
    assert "create_block" in PresentationOpsContentService.allowed_ops()
    assert "align_blocks" in PresentationOpsContentService.allowed_ops()
    assert "reorder_block_z" in PresentationOpsContentService.allowed_ops()
    assert "duplicate_blocks" in PresentationOpsContentService.allowed_ops()
