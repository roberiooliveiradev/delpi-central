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


def test_detect_ignores_refinement_without_stock_context():
    refinement = ChatOperationalRefinementService.detect(
        "filtre filial 02",
        previous_messages=[{"role": "user", "content": "olá"}],
    )

    assert refinement is None


def test_is_operational_follow_up_enables_fast_path():
    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        _stock_assistant_message(),
    ]

    assert ChatOperationalRefinementService.is_operational_follow_up(
        "filtre filial 02",
        previous_messages=history,
    )
