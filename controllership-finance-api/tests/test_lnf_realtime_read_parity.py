"""Paridade socket × leitura HTTP. O socket não pode ser mais largo."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from delpi_auth.request_context import reset_current_user, set_current_user

from controllership_finance_app.application.invoice_posting.permissions import (
    LANCAMENTO_NOTAS_FISCAIS_ACCESS,
    LANCAMENTO_NOTAS_FISCAIS_CREATE,
    LANCAMENTO_NOTAS_FISCAIS_MANAGE,
    LANCAMENTO_NOTAS_FISCAIS_PROCESS,
    LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS,
    LANCAMENTO_NOTAS_FISCAIS_VIEW,
    LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01,
    LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_02,
)
from controllership_finance_app.application.invoice_posting.use_cases import (
    GetInvoicePostingRequestUseCase,
    InvoicePostingForbiddenError,
    InvoicePostingNotFoundError,
    ListInvoicePostingRequestsUseCase,
    subscriber_sees_event,
)
from controllership_finance_app.interface.http.routes.invoice_posting.branch_access import (
    branch_view_allowed,
)
from controllership_finance_app.interface.http.routes.invoice_posting.realtime_routes import (
    room_error,
)
from controllership_finance_app.interface.http.routes.invoice_posting.router import _actor

ROUTE = "controllership_finance_app.interface.http.routes.invoice_posting.realtime_routes"

PERSONAS = (
    ("P0", [], False),
    ("P1", [LANCAMENTO_NOTAS_FISCAIS_ACCESS], False),
    ("P2", [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01], False),
    ("P3", [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_02], False),
    ("P4", [LANCAMENTO_NOTAS_FISCAIS_VIEW], False),
    ("P5", [LANCAMENTO_NOTAS_FISCAIS_CREATE], False),
    ("P6", [LANCAMENTO_NOTAS_FISCAIS_PROCESS], False),
    ("P7", [LANCAMENTO_NOTAS_FISCAIS_MANAGE], False),
    ("P8", [LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS], False),
    ("P9", [], True),
    ("P10", [], False),
    (
        "P11",
        [LANCAMENTO_NOTAS_FISCAIS_CREATE, LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01],
        False,
    ),
    (
        "P12",
        [LANCAMENTO_NOTAS_FISCAIS_CREATE, LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_02],
        False,
    ),
)


class _Rows:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def list_requests(self, *, filters, created_by_user_id, page, page_size):
        items = []
        for row in self.rows:
            if filters.get("branch") and row["branch_code"] != filters["branch"]:
                continue
            if created_by_user_id and row["created_by_user_id"] != created_by_user_id:
                continue
            items.append(row)
        return {"items": items, "total": len(items), "total_pages": 1}

    def get_request(self, request_id: str):
        for row in self.rows:
            if row["id"] == request_id:
                return row
        return None

    def list_history(self, _request_id: str):
        return []

    def list_comments(self, _request_id: str):
        return []


def _rows() -> list[dict]:
    return [
        {"id": "00000000-0000-4000-8000-000000000001", "branch_code": "01", "created_by_user_id": "user-1", "status": "pending"},
        {"id": "00000000-0000-4000-8000-000000000002", "branch_code": "01", "created_by_user_id": "other", "status": "pending"},
        {"id": "00000000-0000-4000-8000-000000000003", "branch_code": "02", "created_by_user_id": "user-1", "status": "pending"},
        {"id": "00000000-0000-4000-8000-000000000004", "branch_code": "02", "created_by_user_id": "other", "status": "pending"},
    ]


def _list_visible(actor, repo: _Rows, branch: str) -> set[str] | None:
    if not branch_view_allowed(branch):
        return None
    try:
        data = ListInvoicePostingRequestsUseCase(repo).execute(
            actor=actor, filters={"branch": branch}, page=1, page_size=20
        )
    except InvoicePostingForbiddenError:
        return None
    return {item["id"] for item in data["items"]}


def _detail_ok(actor, repo: _Rows, row: dict) -> bool:
    try:
        GetInvoicePostingRequestUseCase(repo).execute(row["id"], actor)
    except (InvoicePostingForbiddenError, InvoicePostingNotFoundError):
        return False
    return bool(branch_view_allowed(row["branch_code"]))


@pytest.mark.parametrize(("profile", "permissions", "superadmin"), PERSONAS)
def test_socket_matches_http_read(profile: str, permissions: list[str], superadmin: bool) -> None:
    repo = _Rows(_rows())
    user = SimpleNamespace(
        id="user-1",
        name="Usuário",
        email="user@example.com",
        permissions=permissions,
        is_superadmin=superadmin,
        roles=[],
        groups=[],
    )
    token = set_current_user(user)
    try:
        actor = _actor()
        by_id = {row["id"]: row for row in repo.rows}

        def lookup(request_id: str):
            return by_id.get(request_id)

        with patch(f"{ROUTE}.lookup_request_row", lookup):
            for branch in ("01", "02"):
                visible = _list_visible(actor, repo, branch)
                subscribed = room_error(f"lnf:branch:{branch}") is None
                assert subscribed is (visible is not None), profile
                if visible is None:
                    continue
                for row in repo.rows:
                    if row["branch_code"] != branch:
                        continue
                    sees = subscriber_sees_event(
                        can_view_all=actor.can_view_all,
                        has_create=actor.has_create,
                        user_id=actor.user_id,
                        can_list_unmapped=False,
                        kind="request",
                        created_by_user_id=row["created_by_user_id"],
                    )
                    assert sees is (row["id"] in visible), profile
            for row in repo.rows:
                allowed = room_error(f"lnf:request:{row['id']}") is None
                assert allowed is _detail_ok(actor, repo, row), profile
            missing = room_error("lnf:request:00000000-0000-4000-8000-000000000099")
            assert missing == "forbidden_room"
        unmapped = room_error("lnf:unmapped-products") is None
        review = superadmin or (
            LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS in permissions
        )
        assert unmapped is review, profile
    finally:
        reset_current_user(token)
