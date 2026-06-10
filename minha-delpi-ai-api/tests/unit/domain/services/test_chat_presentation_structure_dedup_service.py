from app.domain.services.chat_presentation_structure_dedup_service import (
    ChatPresentationStructureDedupService,
)

STRUCTURE_TABLE = {
    "type": "table",
    "title": "Componentes da estrutura 90260149",
    "columns": [
        {"key": "parent_code", "label": "PI pai"},
        {"key": "component_code", "label": "Componente"},
    ],
    "rows": [{"parent_code": "A", "component_code": "B"}],
}

TREE = {
    "type": "tree",
    "title": "Estrutura do produto 90260149",
    "root": {"id": "90260149", "label": "90260149", "children": []},
}

PROFILE_TABLE = {
    "type": "table",
    "title": "Produto 90260149",
    "columns": [{"key": "campo", "label": "Campo"}, {"key": "valor", "label": "Valor"}],
    "rows": [{"campo": "Código", "valor": "90260149"}],
}


def test_dedupe_removes_structure_table_when_tree_present():
    metadata = {
        "presentation": TREE,
        "tablePresentation": STRUCTURE_TABLE,
        "tablePresentations": [PROFILE_TABLE, STRUCTURE_TABLE],
        "availableFormats": ["text", "table", "tree"],
        "preferredFormat": "tree",
    }

    ChatPresentationStructureDedupService.dedupe_metadata(metadata)

    assert metadata["presentation"]["type"] == "tree"
    assert metadata["tablePresentation"] is None
    assert len(metadata["tablePresentations"]) == 1
    assert metadata["tablePresentations"][0]["title"].startswith("Produto ")
    assert "table" in metadata["availableFormats"]


def test_dedupe_removes_tree_when_table_preferred_for_structure():
    metadata = {
        "presentation": TREE,
        "tablePresentation": STRUCTURE_TABLE,
        "availableFormats": ["text", "table", "tree"],
        "preferredFormat": "table",
    }

    ChatPresentationStructureDedupService.dedupe_metadata(metadata)

    assert metadata["presentation"] == STRUCTURE_TABLE
    assert metadata["tablePresentation"] is None
    assert "tree" not in metadata["availableFormats"]


def test_dedupe_keeps_tree_when_rich_stack_narrative_and_table_preferred():
    metadata = {
        "path": "/products/90269002/factory-status",
        "presentation": STRUCTURE_TABLE,
        "treePresentation": TREE,
        "tablePresentations": [PROFILE_TABLE, STRUCTURE_TABLE],
        "textPresentation": {"markdown": "Status fabril consolidado do produto."},
        "kpiPresentation": {"type": "kpi", "cards": [{"label": "MP", "value": 1}]},
        "availableFormats": ["text", "table", "tree", "kpi"],
        "preferredFormat": "table",
    }

    ChatPresentationStructureDedupService.dedupe_metadata(metadata)

    assert metadata["treePresentation"]["type"] == "tree"
    assert STRUCTURE_TABLE not in (metadata.get("tablePresentations") or [])


def test_prune_available_views_drops_table_without_auxiliary_tables():
    metadata = {
        "presentation": TREE,
        "availableFormats": ["text", "table", "tree"],
    }

    views = ChatPresentationStructureDedupService.prune_available_views(
        ["text", "table", "tree"],
        metadata,
    )

    assert views == ["text", "tree"]


EXCLUSIVITY_TABLE = {
    "type": "table",
    "title": "Componentes com exclusividade",
    "columns": [
        {"key": "level", "label": "Nível"},
        {"key": "component_code", "label": "Código"},
        {"key": "component_type", "label": "Tipo"},
        {"key": "exclusive_raw_material_label", "label": "MP exclusiva?"},
    ],
    "rows": [
        {
            "level": 1,
            "component_code": "50222613",
            "component_type": "PI",
            "exclusive_raw_material_label": "Não",
        }
    ],
}


def test_dedupe_removes_exclusivity_table_when_tree_present():
    metadata = {
        "presentation": TREE,
        "treePresentation": TREE,
        "tablePresentation": EXCLUSIVITY_TABLE,
        "tablePresentations": [PROFILE_TABLE, EXCLUSIVITY_TABLE],
        "availableFormats": ["text", "table", "tree"],
        "preferredFormat": "tree",
    }

    ChatPresentationStructureDedupService.dedupe_metadata(metadata)

    assert metadata["presentation"]["type"] == "tree"
    assert metadata["tablePresentation"] is None
    assert len(metadata["tablePresentations"]) == 1
