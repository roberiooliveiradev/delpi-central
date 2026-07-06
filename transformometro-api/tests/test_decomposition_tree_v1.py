from __future__ import annotations

import pytest

from tm_app.domain.decomposition.decomposition_tree_v1 import (
    DecompositionValidationError,
    empty_tree,
    validate_decomposition_tree_v1,
)


def _sample_tree():
    return {
        "format": "decomposition_tree_v1",
        "format_version": 1,
        "nodes": [
            {
                "id": "pk_crm",
                "level": "processo_chave",
                "ordem": 1,
                "label": "Recebimento CRM",
                "parent_id": None,
            },
            {
                "id": "st_notificacao",
                "level": "sub_tarefa",
                "ordem": 1,
                "label": "Receber notificação",
                "parent_id": "pk_crm",
            },
            {
                "id": "pk_bom",
                "level": "processo_chave",
                "ordem": 2,
                "label": "Montagem BOM",
                "parent_id": None,
            },
        ],
    }


def test_validate_sample_tree():
    doc = validate_decomposition_tree_v1(_sample_tree())
    assert len(doc["nodes"]) == 3


def test_reject_duplicate_node_id():
    tree = _sample_tree()
    tree["nodes"].append(
        {
            "id": "pk_crm",
            "level": "processo_chave",
            "ordem": 3,
            "label": "Duplicado",
            "parent_id": None,
        }
    )
    with pytest.raises(DecompositionValidationError, match="duplicado"):
        validate_decomposition_tree_v1(tree)


def test_reject_processo_chave_with_parent():
    tree = _sample_tree()
    tree["nodes"][0]["parent_id"] = "pk_bom"
    with pytest.raises(DecompositionValidationError, match="parent_id"):
        validate_decomposition_tree_v1(tree)


def test_empty_tree_valid():
    doc = validate_decomposition_tree_v1(empty_tree())
    assert doc["nodes"] == []
