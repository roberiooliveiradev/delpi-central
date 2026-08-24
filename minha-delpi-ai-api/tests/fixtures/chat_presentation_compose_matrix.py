"""Matriz compose — formato pedido × viewIntent × kinds (E4.S1)."""

from __future__ import annotations

from typing import Any

# Precedência: toolbar explicitSessionFormat > message hints > Automático.
COMPOSE_FORMAT_PRECEDENCE: tuple[str, ...] = (
    "explicitSessionFormat",
    "messageHints",
    "automatic",
)

COMPOSE_MATRIX_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "auto_stock_table_lead",
        "path": "/products/10090016/stock",
        "entity": "product_stock",
        "session_format": None,
        "expected_selected": "table",
        "forbid_selected": ("chart",),
        "chart_policy": "skip",
        "expect_table_slot": True,
        "expect_chart_slot": False,
    },
    {
        "id": "toolbar_text_stock",
        "path": "/products/10090016/stock",
        "entity": "product_stock",
        "session_format": "text",
        "expected_selected": "text",
        "forbid_selected": ("chart",),
        "chart_policy": "skip",
        "expect_chart_slot": False,
    },
    {
        "id": "toolbar_table_stock",
        "path": "/products/10090016/stock",
        "entity": "product_stock",
        "session_format": "table",
        "expected_selected": "table",
        "forbid_selected": ("chart",),
        "chart_policy": "skip",
        "expect_table_slot": True,
        "expect_chart_slot": False,
    },
    {
        "id": "toolbar_tree_stock",
        "path": "/products/10090016/stock",
        "entity": "product_stock",
        "session_format": "tree",
        "expected_selected": "tree",
        "forbid_selected": ("chart",),
        "chart_policy": "skip",
        "expect_chart_slot": False,
    },
    {
        "id": "toolbar_chart_stock_skip_policy",
        "path": "/products/10090016/stock",
        "entity": "product_stock",
        "session_format": "chart",
        # Preferência explícita pode pedir chart; bundle sem chart → fallback sem selected=chart
        # se o slot não existir. Fixture asserta ausência de chartPresentation.
        "expected_selected": None,
        "forbid_selected": (),
        "chart_policy": "skip",
        "expect_chart_slot": False,
        "explicit_chart_request": True,
    },
)
