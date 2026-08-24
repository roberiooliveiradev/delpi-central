from app.domain.services.chat_last_result_excerpt_service import (
    ChatLastResultExcerptService,
)


def _structure_tool_metadata() -> dict:
    return {
        "ok": True,
        "path": "/products/90260149/structure",
        "actionId": "product-structure",
        "operationId": "get_product_structure",
        "apiDelpiResponseMeta": {"entity": "product_structure", "shape": "hierarchy"},
        "presentation": {"type": "tree", "title": "Estrutura do produto 90260149"},
        "treePresentation": {
            "type": "tree",
            "title": "Estrutura do produto 90260149",
            "root": {
                "id": "90260149",
                "children": [
                    {"code": "10380044"},
                    {"code": "10380045"},
                    {"code": "10380046"},
                ],
            },
        },
        "responsePreview": (
            '{"root":{"code":"90260149"},"items":['
            '{"code":"10380044"},{"code":"10380045"},{"code":"10380046"}'
            "]}"
        ),
    }


def _stock_tool_metadata() -> dict:
    return {
        "ok": True,
        "path": "/products/10080047/stock",
        "actionId": "product-stock",
        "operationId": "get_product_stock",
        "apiDelpiResponseMeta": {"entity": "product_stock", "shape": "playbook_report"},
        "presentation": {"type": "table", "title": "Estoque do produto 10080047"},
        "dataAnswer": {"profileKey": "stock"},
        "summary": {"totalCount": 3},
        "humanizedSummary": {
            "titulo": "Estoque do produto 10080047",
            "linhas": ["- Saldo consolidado: 120 PC"],
        },
        "responsePreview": '{"items":[{"code":"10080047","quantity":120}]}',
    }


def test_build_structure_excerpt_with_top_keys():
    excerpt = ChatLastResultExcerptService.build(
        [
            {
                "name": "execute_external_action",
                "metadata": _structure_tool_metadata(),
            }
        ],
        message_id="msg-structure",
    )

    assert excerpt is not None
    assert excerpt.get("profileKey") is None or excerpt["entity"] == "product_structure"
    assert excerpt["presentationType"] == "tree"
    assert excerpt["rowCount"] == 3
    assert excerpt["topKeys"][:3] == ["10380044", "10380045", "10380046"]
    assert excerpt["messageId"] == "msg-structure"
    assert excerpt.get("preview")


def test_build_stock_excerpt_with_profile_and_preview():
    excerpt = ChatLastResultExcerptService.build(
        [
            {
                "name": "execute_external_action",
                "metadata": _stock_tool_metadata(),
            }
        ],
    )

    assert excerpt is not None
    assert excerpt["profileKey"] == "stock"
    assert excerpt["presentationType"] == "table"
    assert excerpt["rowCount"] == 3
    assert "10080047" in excerpt["topKeys"]
    assert "Estoque" in str(excerpt.get("preview") or "")


def test_build_prefers_primary_over_enrichment():
    excerpt = ChatLastResultExcerptService.build(
        [
            {
                "name": "execute_external_action",
                "metadata": {
                    **_stock_tool_metadata(),
                    "compositionRole": "primary",
                },
            },
            {
                "name": "execute_external_action",
                "metadata": {
                    **_structure_tool_metadata(),
                    "compositionRole": "enrichment",
                },
            },
        ],
    )

    assert excerpt is not None
    assert excerpt["profileKey"] == "stock"
