"""GLPI #887: no-op preview and disabled-only idempotent bulk report setup."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.scripts import glpi_887_prepare_manager_reports as bootstrap


def _candidate(reg="20001", status="ready"):
    prepared = status == "ready"
    return {
        "registration": reg,
        "fullName": "Gestor de teste",
        "status": status,
        "directCount": 3,
        "userId": str(uuid4()) if prepared else None,
        "email": "gestor@delpi.com.br" if prepared else None,
    }


def _response(root, candidates):
    return {
        "rootRegistration": root,
        "scopedToRoot": True,
        "readOnly": True,
        "managerCount": len(candidates),
        "candidates": candidates,
    }


def test_fetch_collects_multiple_roots_and_deduplicates_overlap():
    item = _candidate()
    second = _candidate(reg="30005")
    sess = Mock()
    sess.get.side_effect = [
        SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: _response("20001", [item]),
        ),
        SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: _response("30000", [item, second]),
        ),
    ]
    result = bootstrap.fetch_candidates(
        ["20001", "30000"],
        core_base_url="http://core-api:8000",
        token="secret",
        session=sess,
    )
    assert [x["registration"] for x in result] == ["20001", "30005"]
    assert sess.get.call_count == 2
    for call in sess.get.call_args_list:
        assert call.kwargs["allow_redirects"] is False
        assert call.kwargs["headers"]["X-Delpi-Service-Token"] == "secret"


def test_plan_marks_existing_and_unmapped_without_creating_duplicate():
    candidates = [_candidate(), _candidate("30005"), _candidate("90001", "missing_mapping")]
    definitions = [{
        "providerKey": bootstrap.PROVIDER,
        "params": {"managerRegistration": "30005"},
        "id": "old",
    }]
    plan = bootstrap.make_plan(candidates, definitions)
    assert [row["operation"] for row in plan] == [
        "prepare_disabled", "already_exists", "missing_mapping",
    ]
    assert plan[2]["recipient"] is None


def test_repeated_definitions_are_detected_not_overwritten():
    existing = [
        {"providerKey": bootstrap.PROVIDER, "params": {"managerRegistration": "20001"}},
        {"providerKey": bootstrap.PROVIDER, "params": {"managerRegistration": "20001"}},
    ]
    plan = bootstrap.make_plan([_candidate()], existing)
    assert plan[0]["operation"] == "duplicate_definitions"


def test_apply_creates_solo_manager_recipient_and_disabled_monday_schedule():
    repo = Mock()
    definition_id = str(uuid4())
    repo.create_definition.return_value = {"id": definition_id}
    repo.get_definition.return_value = {"providerKey": bootstrap.PROVIDER}
    repo.replace_recipients.return_value = [{
        "userId": "id",
        "email": "gestor@delpi.com.br",
    }]
    repo.upsert_schedule_for_definition.return_value = {"enabled": False}
    plan = bootstrap.make_plan([_candidate()], [])
    result = bootstrap.apply_plan(plan, repo)
    assert result["prepared"] == 1
    repo.create_definition.assert_called_once()
    create_args = repo.create_definition.call_args.kwargs
    assert create_args["provider_key"] == bootstrap.PROVIDER
    assert create_args["params"] == {"managerRegistration": "20001"}
    assert repo.replace_recipients.call_count == 1
    assert len(repo.replace_recipients.call_args.kwargs["items"]) == 1
    schedule = repo.upsert_schedule_for_definition.call_args.kwargs
    assert schedule["schedule_kind"] == "weekly"
    assert schedule["enabled"] is False
    assert schedule["timezone"] == "America/Sao_Paulo"


def test_preview_main_does_not_write(monkeypatch, capsys):
    monkeypatch.setattr(bootstrap.settings, "CORE_API_BASE_URL", "http://core-api:8000")
    monkeypatch.setattr(bootstrap.settings, "CORE_REPORTS_DIRECT_USAGE_SERVICE_TOKEN", "token")
    monkeypatch.setattr(bootstrap.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", False)
    repo = Mock()
    repo.list_definitions.return_value = []
    monkeypatch.setattr(bootstrap, "build_reports_repository", lambda: repo)
    monkeypatch.setattr(bootstrap, "fetch_candidates", lambda *args, **kwargs: [_candidate()])
    code = bootstrap.main(["--root", "20001"])
    assert code == 0
    assert '"changesApplied": false' in capsys.readouterr().out
    repo.create_definition.assert_not_called()
    repo.replace_recipients.assert_not_called()
    repo.upsert_schedule_for_definition.assert_not_called()


def test_apply_requires_explicit_confirmation_even_if_no_send(monkeypatch):
    with pytest.raises(SystemExit):
        bootstrap.main(["--root", "20001", "--apply"])


def test_apply_rejected_if_delivery_gate_enabled(monkeypatch):
    monkeypatch.setattr(bootstrap.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", True)
    with pytest.raises(SystemExit):
        bootstrap.main(["--root", "20001", "--apply", "--confirm", "PREPARAR"])


def test_conflicting_root_data_fails_before_any_database_write():
    person = _candidate()
    conflict = {**person, "directCount": 8}
    sess = Mock()
    sess.get.side_effect = [
        SimpleNamespace(raise_for_status=lambda: None, json=lambda: _response("20001", [person])),
        SimpleNamespace(raise_for_status=lambda: None, json=lambda: _response("30000", [conflict])),
    ]
    with pytest.raises(ValueError, match="divergentes"):
        bootstrap.fetch_candidates(
            ["20001", "30000"],
            core_base_url="http://core-api:8000",
            token="token",
            session=sess,
        )
