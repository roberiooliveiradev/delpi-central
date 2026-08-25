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
                "label": "90260149",
                "badge": "PA",
                "children": [
                    {"label": "50231850", "badge": "PI", "children": [
                        {"label": "10080109", "badge": "MP"},
                        {"label": "10090014", "badge": "MP"},
                    ]},
                    {"label": "50231851", "badge": "PI", "children": [
                        {"label": "10080109", "badge": "MP"},
                    ]},
                ],
            },
        },
        "responsePreview": (
            '{"root":{"code":"90260149","type":"PA"},"items":['
            '{"code":"50231850","type":"PI","components":['
            '{"code":"10080109","type":"MP"},{"code":"10090014","type":"MP"}'
            "]},"
            '{"code":"50231851","type":"PI","components":['
            '{"code":"10080109","type":"MP"}'
            "]}]}"
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
    assert excerpt["rowCount"] == 2
    assert "50231850" in excerpt["topKeys"]
    assert excerpt["messageId"] == "msg-structure"
    assert excerpt.get("preview")
    typed = excerpt.get("keysByComponentType") or {}
    assert set(typed.get("PI") or []) == {"50231850", "50231851"}
    assert set(typed.get("MP") or []) == {"10080109", "10090014"}


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
    assert "stock" in str(excerpt.get("path") or "").lower() or excerpt.get("profileKey") == "stock"


def test_build_preserving_structure_types_keeps_mp_after_stock_turn():
    structure_msg = {
        "role": "assistant",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": _structure_tool_metadata(),
                }
            ]
        },
    }
    stock_calls = [
        {
            "name": "execute_external_action",
            "metadata": _stock_tool_metadata(),
        }
    ]

    excerpt = ChatLastResultExcerptService.build_preserving_structure_types(
        stock_calls,
        previous_messages=[structure_msg],
    )

    assert excerpt is not None
    typed = excerpt.get("keysByComponentType") or {}
    assert "10080109" in (typed.get("MP") or [])
    assert "10090014" in (typed.get("MP") or [])


def test_build_tree_only_nested_mp_without_response_preview():
    metadata = {
        "ok": True,
        "path": "/products/90260149/structure",
        "operationId": "get_product_structure",
        "apiDelpiResponseMeta": {"entity": "product_structure"},
        "treePresentation": {
            "type": "tree",
            "title": "Estrutura",
            "root": {
                "id": "90260149",
                "badge": "PA",
                "children": [
                    {
                        "id": "50230130",
                        "badge": "PI",
                        "children": [
                            {"id": "10080109", "badge": "MP"},
                            {"id": "10380050", "badge": "MP"},
                        ],
                    }
                ],
            },
        },
    }

    excerpt = ChatLastResultExcerptService.build(
        [{"name": "execute_external_action", "metadata": metadata}]
    )

    typed = (excerpt or {}).get("keysByComponentType") or {}
    assert typed.get("PI") == ["50230130"]
    assert set(typed.get("MP") or []) == {"10080109", "10380050"}
