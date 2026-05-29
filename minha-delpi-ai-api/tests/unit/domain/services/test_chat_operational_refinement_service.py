from types import SimpleNamespace

from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)


def _stock_assistant_message(product_code: str = "10080022"):
    return SimpleNamespace(
        role="assistant",
        content=f"Estoque do produto {product_code}",
        metadata={
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": f"/products/{product_code}/stock",
                        "actionId": "get_product_stock",
                    },
                }
            ]
        },
    )


def test_detect_stock_refinement_with_branch_from_history():
    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        _stock_assistant_message(),
    ]

    refinement = ChatOperationalRefinementService.detect(
        "filtre filial 02",
        previous_messages=history,
    )

    assert refinement is not None
    assert refinement.kind == "stock_refinement"
    assert refinement.product_code == "10080022"
    assert refinement.branch == "02"


def test_detect_stock_refinement_with_unresolved_path_template():
    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "content": "Estoque do produto 10080022",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "get_product_stock",
                            "parameters": {"code": "10080022", "page": 1, "page_size": 50},
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/{code}/stock",
                            "actionId": "get_product_stock",
                        },
                    }
                ]
            },
        },
    ]

    refinement = ChatOperationalRefinementService.detect(
        "filtre filial 02",
        previous_messages=history,
    )

    assert refinement is not None
    assert refinement.kind == "stock_refinement"
    assert refinement.product_code == "10080022"
    assert refinement.branch == "02"


def test_detect_ignores_refinement_without_stock_context():
    refinement = ChatOperationalRefinementService.detect(
        "filtre filial 02",
        previous_messages=[{"role": "user", "content": "olá"}],
    )

    assert refinement is None


def test_plan_stock_follow_ups_for_multiple_products():
    history = [
        {"role": "user", "content": "estoque dos produtos 10080047 e 10080055"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/stock",
                        },
                    },
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080055/stock",
                        },
                    },
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_stock_follow_ups(
        "filtre filial 01",
        previous_messages=history,
    )

    assert len(planned) == 2
    assert {item.product_code for item in planned} == {"10080047", "10080055"}
    assert all(item.branch == "01" for item in planned)


def test_plan_stock_reset_for_multiple_products():
    history = [
        {"role": "user", "content": "estoque dos produtos 10080047 e 10080055"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/stock",
                        },
                    },
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080055/stock",
                            "branch": "01",
                        },
                    },
                ]
            },
        },
        {"role": "user", "content": "filtre filial 01"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/stock",
                        },
                    },
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080055/stock",
                        },
                    },
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_stock_follow_ups(
        "completo de novo",
        previous_messages=history,
    )

    assert len(planned) == 2
    assert all(item.kind == "stock_reset" for item in planned)
    assert all(item.branch is None for item in planned)


def test_plan_metric_follow_up_after_cpv():
    history = [
        {"role": "user", "content": "qual o cpv"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/supplies/cpv"},
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_metric_follow_ups(
        "filtre filial 02",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "metric_refinement"
    assert planned[0].metric_kind == "supplies"
    assert planned[0].branch == "02"


def test_is_operational_follow_up_enables_fast_path():
    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        _stock_assistant_message(),
    ]

    assert ChatOperationalRefinementService.is_operational_follow_up(
        "filtre filial 02",
        previous_messages=history,
    )


def test_plan_metric_follow_up_after_commercial_kpi():
    history = [
        {"role": "user", "content": "faturamento comercial"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/commercial/billing",
                        },
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_metric_follow_ups(
        "filtre filial 02",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "metric_refinement"
    assert planned[0].metric_kind == "department_kpi"
    assert planned[0].branch == "02"


def test_plan_product_route_follow_up_after_structure():
    """Follow-up operacional reutiliza lote recente de sub-rota produto."""
    history = [
        {"role": "user", "content": "estrutura do produto 10080047"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/structure",
                        },
                    }
                ]
            },
        },
    ]

    assert ChatOperationalRefinementService.is_operational_follow_up(
        "e os pais desse produto",
        previous_messages=history,
    )
