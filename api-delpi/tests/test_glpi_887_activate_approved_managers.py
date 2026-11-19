"""GLPI #887: selective weekly activation must never include two excluded managers."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.scripts import glpi_887_activate_approved_managers as activation


def _setup():
    identifiers = {reg: str(uuid4()) for reg in activation.EXPECTED}
    candidates = [
        {
            "registration": reg,
            "fullName": reg,
            "directCount": 1,
            "status": "ready",
            "userId": identifiers[reg],
            "email": reg.replace(" ", "").lower() + "@example.com",
        }
        for reg in sorted(activation.EXPECTED)
    ]
    definitions = [
        {
            "id": "def-" + reg,
            "active": True,
            "providerKey": activation.PROVIDER,
            "params": {"managerRegistration": reg},
        }
        for reg in sorted(activation.EXPECTED)
    ]
    schedules = {
        "def-" + reg: {
            "enabled": False,
            "scheduleKind": "weekly",
            "weekday": 0,
            "hour": 8,
            "minute": 0,
            "timezone": "America/Sao_Paulo",
            "nextRunAt": (
                datetime.now(timezone.utc) + timedelta(days=3)
            ).isoformat(),
        }
        for reg in activation.EXPECTED
    }
    repo = Mock()
    repo.get_schedule_for_definition.side_effect = lambda definition_id: schedules[definition_id]
    repo.list_recipients.side_effect = lambda definition_id: [
        {
            "userId": identifiers[definition_id[4:]],
            "email": definition_id[4:].replace(" ", "").lower() + "@example.com",
            "active": True,
        }
    ]
    repo.list_active_recipients.side_effect = repo.list_recipients.side_effect
    repo.get_definition.side_effect = lambda definition_id: next(
        d for d in definitions if d["id"] == definition_id
    )
    repo.upsert_schedule_for_definition.side_effect = lambda **kwargs: schedules[
        kwargs["definition_id"]
    ].update({
        "enabled": kwargs["enabled"],
        "hour": int(kwargs["cron_expression"].split()[1]),
        "nextRunAt": kwargs["next_run_at"].isoformat(),
    }) or schedules[kwargs["definition_id"]]
    provider = Mock()
    provider.collect.side_effect = lambda params: SimpleNamespace(
        provider_key=activation.PROVIDER,
        row_count=1,
        meta={
            "directOnly": True,
            "managerRegistration": params["managerRegistration"],
            "managerEmail": params["managerRegistration"].replace(" ", "").lower() + "@example.com",
            "managerCoreUserId": identifiers[params["managerRegistration"]],
        },
    )
    return candidates, definitions, repo, provider, schedules


def _plan(data):
    candidates, definitions, repo, provider, _ = data
    return activation.build_plan(
        candidates=candidates,
        definitions=definitions,
        repository=repo,
        provider=provider,
    )


def test_plan_has_exactly_ten_approved_and_both_exclusions():
    data = _setup()
    plan = _plan(data)
    assert len(plan) == 12
    assert sum(item["desiredEnabled"] for item in plan) == 10
    assert {
        item["registration"] for item in plan if not item["desiredEnabled"]
    } == {"20057", "20077"}
    assert activation._summary(plan)["stillToEnable"] == 10
    data[2].upsert_schedule_for_definition.assert_not_called()


def test_apply_requires_global_gate_even_with_confirmed_scope(monkeypatch):
    plan = _plan(_setup())
    monkeypatch.setattr(
        activation.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", False
    )
    with pytest.raises(ValueError, match="Gate global"):
        activation.apply_plan(plan, Mock())


def test_apply_only_ten_and_never_excluded(monkeypatch):
    data = _setup()
    monkeypatch.setattr(
        activation.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", True
    )
    plan = _plan(data)
    activation.apply_plan(plan, data[2])
    calls = data[2].upsert_schedule_for_definition.call_args_list
    assert len(calls) == 10
    ids = {call.kwargs["definition_id"] for call in calls}
    assert ids == {"def-" + reg for reg in activation.APPROVED}
    assert "def-20057" not in ids
    assert "def-20077" not in ids
    assert all(call.kwargs["enabled"] is True for call in calls)
    assert data[4]["def-20057"]["enabled"] is False
    assert data[4]["def-20077"]["enabled"] is False
    assert all(call.kwargs["cron_expression"] == "0 9 * * 1" for call in calls)
    assert activation._summary(_plan(data))["stillToEnable"] == 0
    assert activation._summary(_plan(data))["readyAtNine"] == 10

    # Idempotent: no new writes on a second activation.
    data[2].upsert_schedule_for_definition.reset_mock()
    activation.apply_plan(_plan(data), data[2])
    data[2].upsert_schedule_for_definition.assert_not_called()


def test_rejects_missing_manager_or_new_unreviewed_manager():
    data = _setup()
    data[0].pop()
    with pytest.raises(ValueError, match="hierarquia RH mudou"):
        _plan(data)


def test_rejects_unverified_ceo():
    data = _setup()
    next(c for c in data[0] if c["registration"] == "10257")["status"] = "missing_mapping"
    with pytest.raises(ValueError, match="sem conta Core"):
        _plan(data)


def test_rejects_excluded_manager_already_enabled():
    data = _setup()
    data[4]["def-20057"]["enabled"] = True
    with pytest.raises(ValueError, match="excluída"):
        _plan(data)


def test_rejects_unexpected_enabled_schedule_outside_ceo_tree():
    data = _setup()
    data[1].append({
        "id": "extra",
        "providerKey": activation.PROVIDER,
        "params": {"managerRegistration": "90000"},
        "active": True,
    })
    original = data[2].get_schedule_for_definition.side_effect
    data[2].get_schedule_for_definition.side_effect = (
        lambda definition_id: {"enabled": True}
        if definition_id == "extra" else original(definition_id)
    )
    with pytest.raises(ValueError, match="fora da lista"):
        _plan(data)


def test_rejects_extra_recipient():
    data = _setup()
    old = data[2].list_recipients.side_effect
    def double(definition_id):
        rows = old(definition_id)
        return rows + [dict(rows[0])]
    data[2].list_recipients.side_effect = double
    with pytest.raises(ValueError, match="Destinatário único"):
        _plan(data)


def test_apply_requires_explicit_confirmation(monkeypatch):
    with pytest.raises(SystemExit):
        activation.main(["--apply"])


def test_preview_main_never_writes(monkeypatch, capsys):
    data = _setup()
    monkeypatch.setattr(
        activation.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", False
    )
    monkeypatch.setattr(activation, "fetch_candidates", lambda *args, **kwargs: data[0])
    data[2].list_definitions.return_value = data[1]
    monkeypatch.setattr(activation, "build_reports_repository", lambda: data[2])
    with patch.object(activation, "DirectTeamUsageWeeklyProvider", return_value=data[3]):
        code = activation.main([])
    assert code == 0
    assert '"stillToEnable": 10' in capsys.readouterr().out
    data[2].upsert_schedule_for_definition.assert_not_called()


def test_existing_enabled_eight_am_is_rescheduled_to_nine_without_extra_email(monkeypatch):
    data = _setup()
    data[4]["def-20001"]["enabled"] = True
    data[4]["def-20001"]["hour"] = 8
    monkeypatch.setattr(
        activation.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", True
    )
    plan = _plan(data)
    assert activation._summary(plan)["stillToEnable"] == 10
    activation.apply_plan(plan, data[2])
    assert data[4]["def-20001"]["enabled"] is True
    assert data[4]["def-20001"]["hour"] == 9
    assert data[4]["def-20057"]["enabled"] is False
    assert data[4]["def-20077"]["enabled"] is False
    assert activation._summary(_plan(data))["readyAtNine"] == 10


def test_already_enabled_at_nine_is_not_reset(monkeypatch):
    data = _setup()
    for reg in activation.APPROVED:
        data[4]["def-" + reg]["enabled"] = True
        data[4]["def-" + reg]["hour"] = 9
    monkeypatch.setattr(
        activation.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", True
    )
    activation.apply_plan(_plan(data), data[2])
    data[2].upsert_schedule_for_definition.assert_not_called()
    assert activation._summary(_plan(data))["readyAtNine"] == 10
