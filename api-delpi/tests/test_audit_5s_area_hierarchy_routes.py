"""Rotas e regras de hierarquia de áreas 5S (filial 02)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.domain.services.audit_5s.audit_5s_area_hierarchy_service import mean_of_means
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_AUDIT = "app.interface.http.routes.quality.audit_5s_operational_router"


def _user_patch(*, is_superadmin: bool = True):
    return patch(
        f"{_AUDIT}.get_current_user",
        return_value=MagicMock(id="u1", name="Admin", is_superadmin=is_superadmin),
    )


@_user_patch()
@patch(f"{_AUDIT}.branch_audit_allowed", return_value=True)
@patch(f"{_AUDIT}.branch_admin_allowed", return_value=True)
@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_update_audit_5s_area_returns_meta(
    mock_build, _access, _admin, _audit, _user
) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        UpdateAreaBody,
        update_area,
    )

    repo = MagicMock()
    repo.get_area.return_value = {
        "id": "area-1",
        "branch_code": "02",
        "name": "Montagem",
        "active": True,
        "children_count": 0,
        "is_aggregator": False,
        "is_sub_area": False,
    }
    repo.update_area.return_value = {
        "id": "area-1",
        "branch_code": "02",
        "name": "Montagem ES",
        "active": True,
        "children_count": 0,
        "is_aggregator": False,
        "is_sub_area": False,
    }
    mock_build.return_value = repo
    response = update_area(
        area_id="area-1",
        body=UpdateAreaBody(name="Montagem ES"),
    )
    assert_envelope_meta(body_json(response), operation_id="update_audit_5s_area")


@_user_patch()
@patch(f"{_AUDIT}.branch_admin_allowed", return_value=True)
@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_set_audit_5s_area_children_returns_meta(mock_build, _access, _admin, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        SetAreaChildrenBody,
        set_area_children,
    )

    repo = MagicMock()
    repo.get_area.return_value = {
        "id": "parent-1",
        "branch_code": "02",
        "name": "Agregadora",
        "active": True,
        "children_count": 0,
        "is_aggregator": False,
        "is_sub_area": False,
    }
    repo.set_area_children.return_value = {
        "id": "parent-1",
        "branch_code": "02",
        "name": "Agregadora",
        "is_aggregator": True,
        "children_count": 2,
        "children": [{"id": "c1"}, {"id": "c2"}],
    }
    mock_build.return_value = repo
    response = set_area_children(
        area_id="parent-1",
        body=SetAreaChildrenBody(child_ids=["c1", "c2"]),
    )
    assert_envelope_meta(body_json(response), operation_id="set_audit_5s_area_children")
    repo.set_area_children.assert_called_once_with(
        parent_area_id="parent-1",
        child_ids=["c1", "c2"],
    )


@_user_patch()
@patch(f"{_AUDIT}.branch_admin_allowed", return_value=True)
@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_set_area_children_rejects_branch_01(mock_build, _access, _admin, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        SetAreaChildrenBody,
        set_area_children,
    )

    repo = MagicMock()
    repo.get_area.return_value = {
        "id": "parent-1",
        "branch_code": "01",
        "name": "Agregadora",
        "active": True,
        "children_count": 0,
        "is_aggregator": False,
        "is_sub_area": False,
    }
    mock_build.return_value = repo
    response = set_area_children(
        area_id="parent-1",
        body=SetAreaChildrenBody(child_ids=["c1"]),
    )
    body = body_json(response)
    assert body.get("success") is False
    assert response.status_code == 422
    repo.set_area_children.assert_not_called()


@_user_patch()
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_create_audit_rejects_aggregator_area(mock_build, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        CreateAuditBody,
        create_audit,
    )

    repo = MagicMock()
    repo.create_audit.side_effect = PluginsRepositoryError(
        "Área agregadora não pode receber auditoria. Selecione uma subárea ou área folha."
    )
    mock_build.return_value = repo
    response = create_audit(
        body=CreateAuditBody(
            branch_code="02",
            audit_date="2026-09-01",
            area_id="parent-1",
            area_responsible="Responsável",
            shift="TURNO_1",
        )
    )
    body = body_json(response)
    assert body.get("success") is False
    assert response.status_code == 422


def test_mean_of_means_dashboard_formula():
    assert mean_of_means([80.0, 60.0]) == 70.0


def test_route_contracts_include_area_hierarchy_operations() -> None:
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    assert "update_audit_5s_area" in ROUTE_CONTRACTS
    assert "set_audit_5s_area_children" in ROUTE_CONTRACTS
