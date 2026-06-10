from app.application.services.chat_tool_context_format_service import (
    ChatToolContextFormatService,
)


def test_apply_format_override_builds_stock_tree_from_wrapped_payload():
    service = ChatToolContextFormatService()
    metadata = {
        "ok": True,
        "path": "/products/10080022/stock",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
            "availableViews": ["text", "table", "tree"],
        },
        "textPresentation": {"type": "markdown", "markdown": "Resumo"},
        "presentation": None,
    }
    tool_calls = [{"name": "execute_external_action", "metadata": metadata}]
    payload = {
        "stock": {
            "items": [
                {
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": 10,
                    "available_quantity": 8,
                    "committed_quantity": 2,
                },
            ]
        }
    }

    service.apply_format_override(tool_calls, "tree", payload)

    meta = tool_calls[0]["metadata"]

    assert meta["presentation"]["type"] == "tree"
    assert meta["presentationDecision"]["selected"] == "tree"
    assert meta.get("explicitSessionFormat") == "tree"


def test_apply_format_override_builds_structure_table_from_tree_primary():
    service = ChatToolContextFormatService()
    metadata = {
        "ok": True,
        "path": "/products/90269001/structure",
        "presentationDecision": {
            "selected": "tree",
            "layoutMode": "single",
            "availableViews": ["text", "table", "tree"],
        },
        "presentation": {"type": "tree", "title": "Estrutura", "root": {"id": "root"}},
        "textPresentation": {"type": "markdown", "markdown": "Resumo"},
    }
    tool_calls = [{"name": "execute_external_action", "metadata": metadata}]
    payload = {
        "root": {
            "code": "90269001",
            "description": "ITEM",
            "type": "PA",
            "unit": "UN",
            "quantity": 1,
        },
        "items": [
            {
                "code": "C1",
                "description": "COMP",
                "type": "PI",
                "unit": "UN",
                "quantity": 1.0,
            }
        ],
        "total": 1,
    }

    service.apply_format_override(tool_calls, "table", payload)

    meta = tool_calls[0]["metadata"]

    assert meta["presentation"]["type"] == "table"
    assert meta["presentationDecision"]["selected"] == "table"
    assert meta.get("explicitSessionFormat") == "table"
