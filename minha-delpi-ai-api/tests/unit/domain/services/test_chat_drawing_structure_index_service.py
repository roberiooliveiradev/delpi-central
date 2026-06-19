from app.domain.services.chat_drawing_structure_index_service import (
    ChatDrawingStructureIndexService,
)


def _nested_structure_payload() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50230969",
                    "description": "PI PAI",
                    "type": "PI",
                    "components": [
                        {
                            "code": "50212870",
                            "description": "PI FILHO 70",
                            "type": "PI",
                            "components": [],
                        },
                        {
                            "code": "50212871",
                            "description": "PI FILHO 71",
                            "type": "PI",
                            "components": [],
                        },
                    ],
                },
                {
                    "code": "10081867",
                    "description": "MP",
                    "type": "MP",
                    "components": [],
                },
            ]
        }
    }


def test_flatten_items_walks_nested_components_with_depth():
    rows = ChatDrawingStructureIndexService.flatten_items(
        _nested_structure_payload()["structure"]
    )

    by_code = {row.code: row for row in rows}

    assert by_code["50230969"].depth == 1
    assert by_code["50230969"].parent_code is None
    assert by_code["50212870"].depth == 2
    assert by_code["50212870"].parent_code == "50230969"
    assert by_code["50212871"].path == ("50230969", "50212871")


def test_collect_bom_line_codes_includes_nested_pi_excludes_mp_under_pi():
    root = _nested_structure_payload()

    codes = ChatDrawingStructureIndexService.collect_bom_line_codes(root, "90262834")

    assert "50230969" in codes
    assert "50212870" in codes
    assert "50212871" in codes
    assert "10081867" in codes


def test_expected_bom_level_uses_structure_depth():
    root = _nested_structure_payload()

    assert (
        ChatDrawingStructureIndexService.expected_bom_level(
            "90262834",
            product_code="90262834",
            root=root,
        )
        == 0
    )
    assert (
        ChatDrawingStructureIndexService.expected_bom_level(
            "50230969",
            product_code="90262834",
            root=root,
        )
        == 1
    )
    assert (
        ChatDrawingStructureIndexService.expected_bom_level(
            "50212870",
            product_code="90262834",
            root=root,
        )
        == 2
    )


def test_collect_guide_expected_codes_includes_nested_pi():
    root = _nested_structure_payload()

    codes = ChatDrawingStructureIndexService.collect_guide_expected_codes(
        root,
        "90262834",
    )

    assert "90262834" in codes
    assert "50230969" in codes
    assert "50212870" in codes
    assert "50212871" in codes
    assert "10081867" not in codes


def test_collect_child_cable_parent_map_is_recursive():
    root = _nested_structure_payload()

    mapping = ChatDrawingStructureIndexService.collect_child_cable_parent_map(root)

    assert mapping["50212870"] == {"50230969"}
    assert mapping["50212871"] == {"50230969"}
