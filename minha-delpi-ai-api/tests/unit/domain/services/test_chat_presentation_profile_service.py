import pytest

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_route_policy_service import (
    ChatPresentationRoutePolicyService,
)
from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)


@pytest.mark.parametrize(
    ("path", "expected_key"),
    [
        ("/products/90260144/structure", "tree_hierarchy"),
        ("/products/90260144/stock", "stock"),
        ("/products/90260144/analyser", "analyser"),
        ("/products/90260144/guide", "table_list"),
        ("/supplies/cpv", "generic"),
        ("/system/tables/search", "system"),
        ("/data/sql", "sql"),
    ],
)
def test_resolve_profile_key_by_path(path: str, expected_key: str) -> None:
    assert ChatPresentationProfileService.resolve_profile_key(path) == expected_key


def test_entity_profile_precedes_path_rules() -> None:
    key = ChatPresentationProfileService.resolve_profile_key(
        "/commercial/closing-rate",
        "product_stock",
    )

    assert key == "stock"


def test_resolve_default_preferred_format_stock_table() -> None:
    preferred = ChatPresentationProfileService.resolve_default_preferred_format(
        path="/products/90260144/stock",
        has_table=True,
        has_chart=True,
        has_text=True,
    )

    assert preferred == "table"


def test_resolve_default_preferred_format_structure_tree() -> None:
    preferred = ChatPresentationProfileService.resolve_default_preferred_format(
        path="/products/90260144/structure",
        has_tree=True,
        has_table=True,
        has_text=True,
    )

    assert preferred == "tree"


def test_route_policy_delegates_to_profile_service() -> None:
    assert ChatPresentationRoutePolicyService.is_stock_route("/products/1/stock")
    assert ChatPresentationRoutePolicyService.is_analyser_route("/products/1/analyser")
    assert ChatPresentationRoutePolicyService.is_tree_route("/products/1/structure")

    preferred = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
        path="/products/90260144/guide",
        has_table=True,
        has_text=True,
    )

    assert preferred == "table"


def test_apply_visual_order_uses_profile_priority() -> None:
    decision = {"availableViews": ["chart", "table", "text"]}

    ChatPresentationProfileService.apply_visual_order(
        decision,
        path="/products/90260144/stock",
    )

    assert decision["visualOrder"][:3] == ["text", "table", "chart"]
    assert decision["presentationProfileKey"] == "stock"


def test_stack_plan_reads_profile_config() -> None:
    metadata = {
        "path": "/products/90260149/analyser",
        "textPresentation": {
            "markdown": "### Título\n\n**Destaques**\n\n- Um.\n\n",
        },
        "presentationDecision": {"visualOrder": ["text", "table", "tree"]},
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["tableRoleOrder"] == ["profile", "guide", "inspection", "other"]
    assert plan["presentationProfileKey"] == "analyser"


def test_stack_plan_stock_path_uses_stock_roles() -> None:
    metadata = {
        "path": "/products/90260149/stock",
        "textPresentation": {"markdown": "**Destaques**\n\n- Saldo."},
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["tableRoleOrder"] == ["profile", "stock", "other"]
    assert plan["presentationProfileKey"] == "stock"
