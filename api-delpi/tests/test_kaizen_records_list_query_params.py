"""Regressão: filtros multi-seleção (repeated query params) da listagem Kaizômetro.

Bug: `Query(pattern=...)` em parâmetro `list[str]` quebrava o request parsing
do FastAPI (TypeError → 500) ao enviar `?status=a&status=b`.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.interface.http.routes.quality.kaizen_records_router import router

_MOD = "app.interface.http.routes.quality.kaizen_records_router"
_BRANCH_MOD = "app.interface.http.routes.quality.kaizen_branch_access"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _superadmin():
    user = MagicMock()
    user.is_superadmin = True
    return patch(f"{_BRANCH_MOD}.get_current_user", return_value=user)


def _repo_stub() -> MagicMock:
    repo = MagicMock()
    repo.list_records.return_value = {
        "items": [],
        "pagination": {"page": 1, "page_size": 200, "total": 0, "total_pages": 1},
    }
    return repo


def test_list_accepts_repeated_status_and_savings_type_params() -> None:
    repo = _repo_stub()
    with _superadmin(), patch(f"{_MOD}.build_kaizen_repository", return_value=repo):
        response = _client().get(
            "/kaizens/records",
            params=[
                ("status", "aprovado"),
                ("status", "implantado"),
                ("savings_type", "material"),
                ("savings_type", "financeiro"),
            ],
        )

    assert response.status_code == 200
    kwargs = repo.list_records.call_args.kwargs
    assert kwargs["status"] == ["aprovado", "implantado"]
    assert kwargs["savings_type"] == ["material", "financeiro"]


def test_list_accepts_single_status_value_backwards_compatible() -> None:
    repo = _repo_stub()
    with _superadmin(), patch(f"{_MOD}.build_kaizen_repository", return_value=repo):
        response = _client().get("/kaizens/records", params={"status": "recebido"})

    assert response.status_code == 200
    assert repo.list_records.call_args.kwargs["status"] == ["recebido"]


def test_list_rejects_invalid_status_value() -> None:
    with _superadmin():
        response = _client().get("/kaizens/records", params={"status": "bogus"})

    assert response.status_code == 422


def test_list_rejects_invalid_savings_type_value() -> None:
    with _superadmin():
        response = _client().get("/kaizens/records", params={"savings_type": "bogus"})

    assert response.status_code == 422
