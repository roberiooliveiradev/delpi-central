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


def test_build_multi_level_humanizes_branch_and_warehouse_labels() -> None:
    items = [
        {"branch": "01", "warehouse": "50", "available_quantity": 10},
        {"branch": "02", "warehouse": "01", "available_quantity": 3},
    ]

    tree = ChatPresentationHierarchyTreeService.build_multi_level(
        title="Estoque",
        root_id="100",
        root_label="Produto 100",
        items=items,
        group_keys=["branch", "warehouse"],
    )

    assert tree is not None

    branch = tree["root"]["children"][0]
    assert branch["label"] == "Filial 01"
    assert branch.get("badge") in {None, ""}

    warehouse = branch["children"][0]
    assert warehouse["label"] == "Armazém 50"
    assert warehouse.get("badge") in {None, ""}


def test_build_flat_bom_tree_nests_pa_pi_mp() -> None:
    items = [
        {
            "level": 1,
            "parent_code": "90261805",
            "component_code": "50222613",
            "component_description": "INTERMEDIARIO",
            "component_type": "PI",
            "accumulated_quantity": "1",
        },
        {
            "level": 2,
            "parent_code": "50222613",
            "component_code": "10020053",
            "component_description": "CABO",
            "component_type": "MP",
            "accumulated_quantity": "300",
            "component_unit": "MT",
            "exclusive_raw_material_label": "Não",
            "total_valid_finished_products_using_mp": 10,
        },
        {
            "level": 2,
            "parent_code": "50222613",
            "component_code": "10080185",
            "component_description": "TERMINAL",
            "component_type": "MP",
            "accumulated_quantity": "2000",
            "component_unit": "PC",
            "exclusive_raw_material_label": "Não",
            "total_valid_finished_products_using_mp": 24,
        },
    ]

    tree = ChatPresentationHierarchyTreeService.build_flat_bom_tree(
        title="Estrutura 90261805",
        root_id="90261805",
        root_label="Produto 90261805",
        root_subtitle="CHICOTE DE LIGACAO",
        items=items,
    )

    assert tree is not None
    assert tree["type"] == "tree"

    root = tree["root"]
    assert root["label"] == "Produto 90261805"
    assert len(root.get("children") or []) == 1

    pi = root["children"][0]
    assert pi["label"] == "50222613 (PI)"
    assert len(pi.get("children") or []) == 2

    mp_codes = {child["label"].split()[0] for child in pi["children"]}
    assert mp_codes == {"10020053", "10080185"}
