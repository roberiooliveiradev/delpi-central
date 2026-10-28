"""BFF proposal-documents: search/pagination são encaminhadas à api-delpi (sem filtro local)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from starlette.requests import Request

import commercial_app.interface.http.routes.proposal_documents_routes as routes


def _authorized_request() -> Request:
    request = Request(
        {"type": "http", "method": "GET", "path": "/proposal-documents/", "headers": []}
    )
    request.state.user = SimpleNamespace(is_superadmin=True)
    return request


def test_list_proposal_documents_forwards_search_and_pagination() -> None:
    gateway = MagicMock()
    gateway.get_commercial_proposal_document.return_value = {
        "success": True,
        "data": {"items": [], "total": 183, "page": 3, "page_size": 20},
    }

    with patch.object(routes, "build_delpi_commercial_gateway", return_value=gateway):
        routes.list_proposal_documents(
            _authorized_request(),
            limit=100,
            search="OV000116",
            page=3,
            page_size=20,
        )

    gateway.get_commercial_proposal_document.assert_called_once_with(
        "",
        params={"limit": 100, "page": 3, "search": "OV000116", "page_size": 20},
    )


def test_list_proposal_documents_omits_empty_search_and_page_size() -> None:
    gateway = MagicMock()
    gateway.get_commercial_proposal_document.return_value = {
        "success": True,
        "data": {"items": [], "total": 3374},
    }

    with patch.object(routes, "build_delpi_commercial_gateway", return_value=gateway):
        routes.list_proposal_documents(
            _authorized_request(), limit=100, search="   ", page=1, page_size=None
        )

    gateway.get_commercial_proposal_document.assert_called_once_with(
        "", params={"limit": 100, "page": 1}
    )


def test_list_proposal_documents_forwards_server_sort() -> None:
    gateway = MagicMock()
    gateway.get_commercial_proposal_document.return_value = {
        "success": True,
        "data": {"items": [], "total": 10},
    }
    with patch.object(routes, "build_delpi_commercial_gateway", return_value=gateway):
        routes.list_proposal_documents(
            _authorized_request(),
            limit=100,
            search="OV000116",
            page=2,
            page_size=20,
            sort_by="itens",
            sort_dir="desc",
        )
    gateway.get_commercial_proposal_document.assert_called_once_with(
        "",
        params={
            "limit": 100, "page": 2, "search": "OV000116", "page_size": 20,
            "sort_by": "itens", "sort_dir": "desc",
        },
    )
