"""Regressão: criar auditoria respeita a lista de auditores do formulário."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import body_json

_AUDIT = "app.interface.http.routes.quality.audit_5s_operational_router"


def _user_patch(user_id: str = "creator-1", name: str = "Criador"):
    return patch(
        f"{_AUDIT}.get_current_user",
        return_value=MagicMock(id=user_id, name=name),
    )


@_user_patch()
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_create_audit_keeps_selected_auditor_without_forcing_creator(mock_build, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        AuditorBody,
        CreateAuditBody,
        create_audit,
    )

    repo = MagicMock()
    repo.create_audit.return_value = {"id": "audit-1", "auditors": []}
    mock_build.return_value = repo

    response = create_audit(
        body=CreateAuditBody(
            branch_code="01",
            audit_date="2026-09-23",
            area_id="area-1",
            area_responsible="Responsável da área",
            shift="TURNO_1",
            auditors=[
                AuditorBody(user_id="auditor-real", display_name="Auditor Real"),
            ],
        )
    )

    assert response.status_code == 200
    assert body_json(response).get("success") is True
    kwargs = repo.create_audit.call_args.kwargs
    assert kwargs["created_by_user_id"] == "creator-1"
    assert kwargs["auditors"] == [
        {"user_id": "auditor-real", "display_name": "Auditor Real"},
    ]


@_user_patch()
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_create_audit_allows_creator_when_explicitly_selected(mock_build, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        AuditorBody,
        CreateAuditBody,
        create_audit,
    )

    repo = MagicMock()
    repo.create_audit.return_value = {"id": "audit-2"}
    mock_build.return_value = repo

    response = create_audit(
        body=CreateAuditBody(
            branch_code="02",
            audit_date="2026-09-23",
            area_id="area-2",
            area_responsible="Responsável",
            shift="TURNO_2",
            auditors=[
                AuditorBody(user_id="creator-1", display_name="Criador"),
                AuditorBody(user_id="auditor-2", display_name="Colega"),
            ],
        )
    )

    assert response.status_code == 200
    auditors = repo.create_audit.call_args.kwargs["auditors"]
    assert [item["user_id"] for item in auditors] == ["creator-1", "auditor-2"]


@_user_patch()
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_create_audit_rejects_empty_auditors(mock_build, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        CreateAuditBody,
        create_audit,
    )

    repo = MagicMock()
    mock_build.return_value = repo

    response = create_audit(
        body=CreateAuditBody(
            branch_code="01",
            audit_date="2026-09-23",
            area_id="area-1",
            area_responsible="Responsável",
            shift="TURNO_1",
            auditors=[],
        )
    )

    assert response.status_code == 400
    body = body_json(response)
    assert body.get("success") is False
    assert "auditor" in str(body.get("message", "")).lower()
    repo.create_audit.assert_not_called()
