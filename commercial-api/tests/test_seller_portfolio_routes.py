from pathlib import Path


ROUTES = (
    Path(__file__).resolve().parents[1]
    / "commercial_app"
    / "interface"
    / "http"
    / "routes"
    / "seller_portfolio_routes.py"
).read_text(encoding="utf-8")


def test_purge_seller_portfolio_operation_id_is_registered() -> None:
    assert 'operation_id="purge_seller_portfolio"' in ROUTES
    assert 'operation_id="deactivate_seller_portfolio"' in ROUTES


def test_purge_route_is_permanent_suffix() -> None:
    assert '"/{portfolio_id}/permanent"' in ROUTES
    assert "def purge_seller_portfolio(" in ROUTES


def test_member_management_operation_ids_are_registered() -> None:
    assert 'operation_id="replace_seller_portfolio_members"' in ROUTES
    assert 'operation_id="add_seller_portfolio_member"' in ROUTES
    assert 'operation_id="remove_seller_portfolio_member"' in ROUTES
    assert 'operation_id="set_seller_portfolio_owner"' in ROUTES


def test_member_routes_paths_exist() -> None:
    assert '"/{portfolio_id}/members"' in ROUTES
    assert '"/{portfolio_id}/members/{user_id}"' in ROUTES
    assert '"/{portfolio_id}/owner"' in ROUTES
    assert '"portfolios"' in ROUTES or "'portfolios'" in ROUTES


def test_member_owner_deactivate_pass_actor_user_id() -> None:
    assert "actor_user_id=_current_user_id(request)" in ROUTES
    assert "def add_seller_portfolio_member(" in ROUTES
    assert "def remove_seller_portfolio_member(" in ROUTES
    assert "def replace_seller_portfolio_members(" in ROUTES
    assert "def set_seller_portfolio_owner(" in ROUTES
    assert "def deactivate_seller_portfolio(" in ROUTES
    assert "def update_seller_portfolio(" in ROUTES
