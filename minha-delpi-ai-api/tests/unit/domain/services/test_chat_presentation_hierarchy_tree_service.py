from app.domain.services.chat_presentation_hierarchy_tree_service import (
    ChatPresentationHierarchyTreeService,
)


def test_build_multi_level_groups_branch_and_warehouse() -> None:
    items = [
        {"branch": "01", "warehouse": "A", "available_quantity": 10},
        {"branch": "01", "warehouse": "B", "available_quantity": 5},
        {"branch": "02", "warehouse": "A", "available_quantity": 3},
    ]

    tree = ChatPresentationHierarchyTreeService.build_multi_level(
        title="Estoque",
        root_id="100",
        root_label="Produto 100",
        items=items,
        group_keys=["branch", "warehouse"],
    )

    assert tree is not None
    assert tree["type"] == "tree"
    root = tree["root"]
    assert root["label"] == "Produto 100"
    assert len(root.get("children") or []) == 2
