"""GLPI #887: schedule is Monday-only and sends cannot escape manager inbox."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
    UpsertReportScheduleUseCase,
)
from app.application.use_cases.reports.run_report_definition_use_case import (
    RunReportDefinitionUseCase,
)
from app.application.use_cases.reports import (
    report_recipients_schedule_use_cases as schedules_module,
    run_report_definition_use_case as runs_module,
)
from app.domain.services.reports.report_types import EmailPayload, ReportDataset

PROVIDER_KEY = "team_direct_app_opens_weekly"
MANAGER_ID = str(uuid4())


def test_direct_schedule_only_monday_and_disabled_until_gate(monkeypatch):
    repository = MagicMock()
    repository.get_definition.return_value = {"providerKey": PROVIDER_KEY}
    repository.upsert_schedule_for_definition.return_value = {"enabled": False}
    use_case = UpsertReportScheduleUseCase(repository)

    monkeypatch.setattr(
        schedules_module.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", False,
    )
    def schedule(**kwargs):
        return use_case.execute(
            definition_id="one-manager",
            hour=8,
            minute=0,
            **kwargs,
        )

    with pytest.raises(ValueError, match="segundas-feiras"):
        schedule(schedule_kind="weekly", weekday=1, enabled=False)
    with pytest.raises(ValueError, match="segundas-feiras"):
        schedule(schedule_kind="daily", weekday=None, enabled=False)
    with pytest.raises(ValueError, match="autorização de envio"):
        schedule(schedule_kind="weekly", weekday=0, enabled=True)
    assert repository.upsert_schedule_for_definition.call_count == 0

    schedule(schedule_kind="weekly", weekday=0, enabled=False)
    payload = repository.upsert_schedule_for_definition.call_args.kwargs
    assert payload["schedule_kind"] == "weekly"
    assert payload["enabled"] is False

    monkeypatch.setattr(
        schedules_module.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", True,
    )
    schedule(schedule_kind="weekly", weekday=0, enabled=True)
    assert repository.upsert_schedule_for_definition.call_args.kwargs["enabled"] is True


def _dataset():
    return ReportDataset(
        provider_key=PROVIDER_KEY,
        title="Equipe direta",
        columns=("collaborator",),
        rows=({"collaborator": "ANA"},),
        meta={
            "directOnly": True,
            "managerRegistration": "20001",
            "managerCoreUserId": MANAGER_ID,
            "managerEmail": "gestor@delpi.com.br",
        },
    )


def _run(recipients, monkeypatch):
    monkeypatch.setattr(
        runs_module.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", True,
    )
    repo = MagicMock()
    repo.get_definition.return_value = {
        "active": True,
        "providerKey": PROVIDER_KEY,
        "params": {"managerRegistration": "20001"},
    }
    repo.list_active_recipients.return_value = recipients
    repo.create_run.return_value = {"id": "run-id"}
    repo.finish_run.side_effect = lambda **kwargs: {"id": "run-id", "status": kwargs["status"]}
    repo.create_delivery.return_value = {"id": "delivery-id"}
    repo.list_deliveries_for_run.return_value = []

    registry = MagicMock()
    registry.require.return_value.collect.return_value = _dataset()
    registry.require.return_value.render_email.return_value = EmailPayload(
        subject="Teste", html_body="<p>Segredo da equipe</p>",
    )
    mail = MagicMock()
    artifacts = MagicMock()
    use_case = RunReportDefinitionUseCase(
        repo, registry, mail, artifact_storage=artifacts,
    )
    return use_case.execute(definition_id="definition-id"), repo, mail, artifacts


def test_wrong_recipient_never_receives_email_or_artifact(monkeypatch):
    result, repo, mail, artifacts = _run(
        [{"userId": str(uuid4()), "email": "outro@delpi.com.br"}],
        monkeypatch,
    )
    assert result["status"] == "failed"
    assert repo.finish_run.call_args.kwargs["status"] == "failed"
    mail.send_mail_to.assert_not_called()
    artifacts.save_html.assert_not_called()


def test_multiple_recipients_never_receive_group_report(monkeypatch):
    result, repo, mail, artifacts = _run(
        [
            {"userId": MANAGER_ID, "email": "gestor@delpi.com.br"},
            {"userId": str(uuid4()), "email": "outro@delpi.com.br"},
        ],
        monkeypatch,
    )
    assert repo.finish_run.call_args.kwargs["status"] == "failed"
    mail.send_mail_to.assert_not_called()
    artifacts.save_html.assert_not_called()


def test_manager_only_delivery_sends_once(monkeypatch):
    result, repo, mail, artifacts = _run(
        [{"userId": MANAGER_ID, "email": "gestor@delpi.com.br"}],
        monkeypatch,
    )
    mail.send_mail_to.assert_called_once()
    assert mail.send_mail_to.call_args.kwargs["to_addresses"] == [
        "gestor@delpi.com.br"
    ]
    assert repo.finish_run.call_args.kwargs["status"] == "succeeded"
    artifacts.save_html.assert_not_called()


def test_scheduled_direct_report_rejects_pinned_historical_week(monkeypatch):
    monkeypatch.setattr(
        runs_module.settings, "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED", True,
    )
    repo = MagicMock()
    repo.get_definition.return_value = {
        "active": True,
        "providerKey": PROVIDER_KEY,
        "params": {
            "managerRegistration": "20001",
            "weekStart": "2026-11-09",
        },
    }
    repo.list_active_recipients.return_value = [
        {"userId": MANAGER_ID, "email": "gestor@delpi.com.br"}
    ]
    mail = MagicMock()
    use_case = RunReportDefinitionUseCase(repo, MagicMock(), mail)
    with pytest.raises(ValueError, match="última semana concluída"):
        use_case.execute(definition_id="def", trigger="schedule")
    repo.create_run.assert_not_called()
    mail.send_mail_to.assert_not_called()
