"""Unit tests — PresentationTreeCompilerService."""

from __future__ import annotations

from app.domain.entities.presentation_spec import PresentationSpec, PresentationTreeSpec
from app.domain.services.presentation_compilers.presentation_tree_compiler_service import (
    PresentationTreeCompilerService,
)
from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)


def _hierarchy_rows():
    return [
        {"region": "South", "branch": "SC", "product_code": "P1", "planned_qty": 10},
        {"region": "South", "branch": "SC", "product_code": "P2", "planned_qty": 20},
        {"region": "South", "branch": "ES", "product_code": "P3", "planned_qty": 15},
        {"region": "North", "branch": "SP", "product_code": "P4", "planned_qty": 8},
    ]


def test_tree_compiler_builds_two_level_hierarchy():
    rows = _hierarchy_rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="tree",
        tree=PresentationTreeSpec(
            level_fields=("region", "branch", "product_code"),
            label_field="product_code",
            default_expanded_depth=2,
        ),
        labels={"region": "Região", "branch": "Filial", "product_code": "Produto"},
    )
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": key} for key in ("region", "branch", "product_code", "planned_qty")],
            "rows": rows,
        }
    }
    PresentationTreeCompilerService.apply(
        metadata,
        spec=spec,
        profile=profile,
        labels=spec.labels,
    )

    tree = metadata["treePresentation"]
    assert tree["type"] == "tree"
    assert tree["defaultExpandedDepth"] == 2
    root = tree["root"]
    assert root["label"] == "Estrutura"
    assert len(root["children"]) == 2
    south = next(child for child in root["children"] if child["id"] == "region:South")
    assert len(south["children"]) == 2
    sc = next(child for child in south["children"] if child["id"] == "branch:SC")
    assert len(sc["children"]) == 2


def test_tree_compiler_builds_three_level_leaf_nodes():
    rows = _hierarchy_rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="tree",
        tree=PresentationTreeSpec(level_fields=("region", "branch", "product_code")),
    )
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": "region"}, {"key": "branch"}, {"key": "product_code"}],
            "rows": rows,
        }
    }
    PresentationTreeCompilerService.apply(
        metadata,
        spec=spec,
        profile=profile,
        labels={},
    )
    root = metadata["treePresentation"]["root"]
    south = next(child for child in root["children"] if child["id"] == "region:South")
    sc = next(child for child in south["children"] if child["id"] == "branch:SC")
    leaf = next(child for child in sc["children"] if child["id"] == "product_code:P1")
    assert leaf["label"] == "P1"


def test_tree_compiler_sets_unmet_intent_when_levels_not_hierarchical():
    rows = [{"planned_qty": 10}, {"planned_qty": 20}]
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="tree",
        tree=PresentationTreeSpec(level_fields=("planned_qty",)),
    )
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": "planned_qty"}],
            "rows": rows,
        },
        "presentationDecision": {},
    }
    PresentationTreeCompilerService.apply(
        metadata,
        spec=spec,
        profile=profile,
        labels={},
    )
    assert metadata.get("treePresentation") is None
    assert metadata["presentationDecision"]["unmetIntent"] == "tree_not_materializable"
