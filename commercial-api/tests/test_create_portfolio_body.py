from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from commercial_app.domain.entities.seller_portfolio import SellerPortfolio
from commercial_app.interface.http.routes import seller_portfolio_routes as routes
from commercial_app.interface.http.schemas.portfolio_schemas import CreatePortfolioBody


def test_create_portfolio_body_accepts_display_name_only() -> None:
    """Name-first (E9 / V013): MFE envia só display_name para carteira órfã."""
    body = CreatePortfolioBody.model_validate({"display_name": "Carteira Sul"})
    assert body.display_name == "Carteira Sul"
    assert body.user_id is None
    assert body.user_ids == []
    assert body.customers == []


def test_create_portfolio_body_accepts_user_ids() -> None:
    body = CreatePortfolioBody.model_validate(
        {
            "display_name": "Equipe",
            "user_ids": ["u1", "u2"],
            "owner_user_id": "u1",
        }
    )
    assert body.user_ids == ["u1", "u2"]
    assert body.owner_user_id == "u1"


class _User:
    def __init__(self, permissions: list[str], sub: str = "admin-1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request() -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/seller-portfolios",
        "raw_path": b"/seller-portfolios",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_create_seller_portfolio_route_name_only() -> None:
    created = SellerPortfolio(
        id="p-new",
        user_id=None,
        display_name="Nova",
        active=True,
        customers=(),
        members=(),
    )
    uc = MagicMock()
    uc.create_portfolio.return_value = created
    uc.serialize_portfolio.return_value = {
        "id": "p-new",
        "display_name": "Nova",
        "user_id": None,
    }
    request = _request()
    request.state.user = _User(["commercial.seller-portfolios.manage"])
    body = CreatePortfolioBody(display_name="Nova")

    with patch.object(routes, "_use_case", return_value=uc):
        response = routes.create_seller_portfolio(request, body)

    assert response.status_code == 201
    payload = json.loads(response.body)
    assert payload["success"] is True
    assert payload["data"]["id"] == "p-new"
    uc.create_portfolio.assert_called_once()
