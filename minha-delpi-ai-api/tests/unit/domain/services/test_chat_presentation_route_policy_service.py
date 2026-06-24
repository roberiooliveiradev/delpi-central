from app.domain.services.chat_presentation_route_policy_service import (
    ChatPresentationRoutePolicyService,
)


def test_tree_routes_default_to_tree():
    preferred = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
        path="/products/90260144/structure",
        has_tree=True,
        has_table=True,
        has_text=True,
    )

    assert preferred == "tree"


def test_stock_route_defaults_to_table_when_prose_available():
    preferred = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
        path="/products/90260144/stock",
        has_table=True,
        has_chart=True,
        has_text=True,
    )

    assert preferred == "table"


def test_stock_route_defaults_to_table_without_prose():
    preferred = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
        path="/products/90260144/stock",
        has_table=True,
        has_chart=True,
        has_text=False,
    )

    assert preferred == "table"


def test_stock_route_honors_session_chart():
    preferred = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
        path="/products/90260144/stock",
        session_format="chart",
        has_table=True,
        has_chart=True,
    )

    assert preferred == "chart"


def test_guide_route_defaults_to_table():
    preferred = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
        path="/products/90260144/guide",
        has_table=True,
        has_text=True,
    )

    assert preferred == "table"
