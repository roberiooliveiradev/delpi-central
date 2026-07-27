"""Smoke Nível A — NCs LMP (/engineering/lmps/nonconformities)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

from app.interface.http.routes.engineering.lmp_nonconformity_router import (
    LmpNonconformityBody,
    create_lmp_nonconformity,
    delete_lmp_nonconformity,
    get_lmp_nonconformity,
    get_lmp_nonconformity_streak,
    list_lmp_nonconformities,
    list_lmp_nonconformity_history,
    list_lmp_problem_tags,
    update_lmp_nonconformity,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_NC_ID = UUID("22222222-2222-2222-2222-222222222222")

_RECORD = {
    "id": str(_NC_ID),
    "registered_at": "2026-07-27T10:00:00+00:00",
    "sale_number": "123456",
    "customer_name": "Cliente Exemplo",
    "launch_date": "2026-01-10",
    "last_revision_date": "2026-06-01",
    "executed_by": "Eng. A",
    "released_by": "Eng. B",
    "status": "open",
    "defect_description": "Folga fora da tolerância no terminal X",
    "problem_tags": ["Medida", "Terminal"],
    "corrective_actions": "Ação",
    "technical_opinion": "Parecer",
    "products": [
        {"product_code": "90001234", "product_description": "Produto X"},
    ],
    "product_codes": ["90001234"],
    "created_by": "user@delpi",
    "updated_by": "user@delpi",
    "created_at": "2026-07-27T10:00:00+00:00",
    "updated_at": "2026-07-27T10:00:00+00:00",
}

_ROUTER = "app.interface.http.routes.engineering.lmp_nonconformity_router"


@patch(f"{_ROUTER}.build_list_lmp_nonconformities_use_case")
def test_list_lmp_nonconformities_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 50,
    }
    mock_build.return_value = use_case

    response = list_lmp_nonconformities()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_lmp_nonconformities",
        shape="paged_list",
    )


@patch(f"{_ROUTER}.build_list_lmp_problem_tags_use_case")
def test_list_lmp_problem_tags_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [{"id": "1", "label": "Medida", "usage_count": 2}],
        "total": 1,
    }
    mock_build.return_value = use_case

    response = list_lmp_problem_tags()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_lmp_problem_tags",
        shape="list",
    )


@patch(f"{_ROUTER}.build_get_lmp_nonconformity_streak_use_case")
def test_get_lmp_nonconformity_streak_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "current_days_without_nc": 1,
        "record_days_without_nc": 55,
        "last_nc_date": "2026-07-26",
        "as_of_date": "2026-07-27",
        "nc_count": 2,
    }
    mock_build.return_value = use_case

    response = get_lmp_nonconformity_streak()
    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="get_lmp_nonconformity_streak",
        shape="scalar",
    )
    assert body["data"]["current_days_without_nc"] == 1
    assert body["data"]["record_days_without_nc"] == 55
    assert body["meta"]["entity"] == "lmp_nonconformity_streak"


@patch(f"{_ROUTER}.build_get_lmp_nonconformity_use_case")
def test_get_lmp_nonconformity_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _RECORD
    mock_build.return_value = use_case

    response = get_lmp_nonconformity(record_id=_NC_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_lmp_nonconformity",
        shape="scalar",
    )


@patch(f"{_ROUTER}.build_list_lmp_nonconformity_history_use_case")
def test_list_lmp_nonconformity_history_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "nonconformity_id": str(_NC_ID),
                "event_type": "updated",
                "changes": {
                    "fields": [
                        {
                            "field": "status",
                            "label": "Status",
                            "old": "open",
                            "new": "done",
                        }
                    ]
                },
                "actor_user_id": "user-1",
                "actor_email": "user@delpi.com.br",
                "actor_name": "Usuário Teste",
                "created_at": "2026-07-27T11:00:00+00:00",
            }
        ],
        "total": 1,
    }
    mock_build.return_value = use_case

    response = list_lmp_nonconformity_history(record_id=_NC_ID)
    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="list_lmp_nonconformity_history",
        shape="list",
    )
    assert body["meta"]["entity"] == "lmp_nonconformity_history"
    assert body["data"]["items"][0]["actor_email"] == "user@delpi.com.br"
    assert body["data"]["items"][0]["actor_name"] == "Usuário Teste"
    assert body["data"]["items"][0]["actor_user_id"] == "user-1"


@patch(f"{_ROUTER}.build_create_lmp_nonconformity_use_case")
def test_create_lmp_nonconformity_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _RECORD
    mock_build.return_value = use_case

    response = create_lmp_nonconformity(
        body=LmpNonconformityBody(
            status="open",
            sale_number="123456",
            customer_name="Cliente Exemplo",
            defect_description="Folga no terminal",
            problem_tags=["Medida", "Terminal"],
            products=[
                {"product_code": "90001234", "product_description": "Produto X"},
            ],
        )
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_lmp_nonconformity",
        shape="scalar",
    )
    use_case.execute.assert_called_once()
    kwargs = use_case.execute.call_args.kwargs
    assert "registered_at" not in kwargs
    assert kwargs["sale_number"] == "123456"
    assert kwargs["problem_tags"] == ["Medida", "Terminal"]
    assert kwargs["defect_description"] == "Folga no terminal"
    assert kwargs["products"][0]["product_code"] == "90001234"
    assert "actor_user_id" in kwargs
    assert "actor_email" in kwargs
    assert "actor_name" in kwargs


@patch(f"{_ROUTER}.build_update_lmp_nonconformity_use_case")
def test_update_lmp_nonconformity_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _RECORD
    mock_build.return_value = use_case

    response = update_lmp_nonconformity(
        record_id=_NC_ID,
        body=LmpNonconformityBody(
            status="in_progress",
            executed_by="Eng. A",
            problem_tags=["Desenho"],
        ),
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_lmp_nonconformity",
        shape="scalar",
    )
    assert use_case.execute.call_args.kwargs["problem_tags"] == ["Desenho"]
    assert "actor_user_id" in use_case.execute.call_args.kwargs

@patch(f"{_ROUTER}.build_delete_lmp_nonconformity_use_case")
def test_delete_lmp_nonconformity_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = True
    mock_build.return_value = use_case

    response = delete_lmp_nonconformity(record_id=_NC_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="delete_lmp_nonconformity",
        shape="scalar",
    )
