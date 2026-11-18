"""GLPI #887: discover unique active direct managers within RH root scope."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.services.direct_report_manager_discovery_service import (
    DirectReportManagerDiscoveryService,
)


def _person(reg, *, mapped=None, active=True):
    return {
        "registration": reg,
        "fullName": "RH " + reg,
        "active": active,
        "identityStatus": "mapped" if mapped else "unmapped",
        "coreUserId": str(mapped) if mapped else None,
    }


def _discovery(team, users):
    provider = Mock()
    provider.get_team.return_value = team
    return DirectReportManagerDiscoveryService(provider, users), provider


def test_finds_all_direct_managers_inside_multilevel_subtree():
    root_id, mid_id = uuid4(), uuid4()
    team = {
        "manager": _person("20001", mapped=root_id),
        "members": [
            {**_person("20002", mapped=mid_id), "managerRegistration": "20001", "relationship": "direct"},
            {**_person("20003"), "managerRegistration": "20001", "relationship": "direct"},
            {**_person("20004"), "managerRegistration": "20002", "relationship": "indirect"},
            {**_person("20005"), "managerRegistration": "20002", "relationship": "indirect"},
        ],
    }
    users = Mock()
    lookup = {
        root_id: SimpleNamespace(active=True, email="Root@delpi.com.br"),
        mid_id: SimpleNamespace(active=True, email="MID@delpi.com.br"),
    }
    users.get_by_id.side_effect = lambda value: lookup.get(value)
    service, gateway = _discovery(team, users)
    data = service.preview("20001")

    assert data["rootRegistration"] == "20001"
    assert data["scopedToRoot"] is True
    assert data["managerCount"] == 2
    assert data["readyCount"] == 2
    assert {
        item["registration"]: item["directCount"]
        for item in data["candidates"]
    } == {"20001": 2, "20002": 2}
    assert data["candidates"][1]["email"] == "mid@delpi.com.br"
    gateway.get_team.assert_called_once_with(
        "20001", include_indirect=True, include_inactive=False,
    )


def test_unmapped_candidate_cannot_obtain_email_or_core_id():
    team = {
        "manager": _person("20001"),
        "members": [
            {**_person("20002"), "managerRegistration": "20001", "relationship": "direct"},
        ],
    }
    users = Mock()
    service, _ = _discovery(team, users)
    result = service.preview("20001")
    assert result["readyCount"] == 0
    assert result["candidates"][0]["status"] == "missing_mapping"
    assert result["candidates"][0]["userId"] is None
    assert result["candidates"][0]["email"] is None
    users.get_by_id.assert_not_called()


def test_verified_manager_without_valid_email_not_ready():
    uid = uuid4()
    team = {
        "manager": _person("20001", mapped=uid),
        "members": [
            {**_person("20002"), "managerRegistration": "20001", "relationship": "direct"},
        ],
    }
    users = Mock()
    users.get_by_id.return_value = SimpleNamespace(active=True, email="***@delpi.com.br")
    service, _ = _discovery(team, users)
    result = service.preview("20001")
    assert result["candidates"][0]["status"] == "missing_email"
    assert result["candidates"][0]["email"] is None
    assert result["candidates"][0]["userId"] is None


def test_outside_parent_rejected_no_guessing_organizational_tree():
    team = {
        "manager": _person("20001"),
        "members": [
            {**_person("20002"), "managerRegistration": "90000", "relationship": "indirect"},
        ],
    }
    service, _ = _discovery(team, Mock())
    with pytest.raises(ValueError, match="fora da subárvore"):
        service.preview("20001")
