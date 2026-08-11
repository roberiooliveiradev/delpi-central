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
