"""Unit — agenda next_run_at e motor de run (Delpi Reports Fase 3)."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from app.application.use_cases.reports.run_report_definition_use_case import (
    RunReportDefinitionUseCase,
)
from app.domain.services.reports.report_schedule_next_run_service import (
    build_cron_expression,
    compute_next_run_at,
    parse_schedule_fields,
)
from app.domain.services.reports.report_types import EmailPayload, ReportDataset
from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
)


def test_build_cron_daily_and_weekly() -> None:
    assert build_cron_expression(schedule_kind="daily", hour=8, minute=30) == (
        "30 8 * * *"
    )
    assert build_cron_expression(
        schedule_kind="weekly", hour=7, minute=0, weekday=0
    ) == "0 7 * * 1"
    assert build_cron_expression(
        schedule_kind="weekly", hour=7, minute=0, weekday=6
    ) == "0 7 * * 0"
    assert build_cron_expression(
        schedule_kind="weekdays", hour=8, minute=0
    ) == "0 8 * * 1-5"


def test_parse_schedule_fields_roundtrip() -> None:
    cron = build_cron_expression(
        schedule_kind="weekly", hour=9, minute=15, weekday=2
    )
    fields = parse_schedule_fields(schedule_kind="weekly", cron_expression=cron)
    assert fields == {"hour": 9, "minute": 15, "weekday": 2}

    weekdays_cron = build_cron_expression(
        schedule_kind="weekdays", hour=8, minute=30
    )
    weekdays_fields = parse_schedule_fields(
        schedule_kind="weekdays", cron_expression=weekdays_cron
    )
    assert weekdays_fields == {"hour": 8, "minute": 30, "weekday": None}


def test_compute_next_run_daily_rolls_forward() -> None:
    tz = ZoneInfo("America/Sao_Paulo")
    after = datetime(2026, 7, 21, 10, 0, tzinfo=tz)
    next_at = compute_next_run_at(
        schedule_kind="daily",
        hour=8,
        minute=0,
        timezone_name="America/Sao_Paulo",
        after=after,
    )
    assert next_at == datetime(2026, 7, 22, 8, 0, tzinfo=tz)


def test_compute_next_run_weekdays_skips_weekend() -> None:
    tz = ZoneInfo("America/Sao_Paulo")
    # Friday 2026-07-24 10:00 → próximo útil é segunda 08:00
    after = datetime(2026, 7, 24, 10, 0, tzinfo=tz)
    next_at = compute_next_run_at(
        schedule_kind="weekdays",
        hour=8,
        minute=0,
        timezone_name="America/Sao_Paulo",
        after=after,
    )
    assert next_at.weekday() == 0
    assert next_at == datetime(2026, 7, 27, 8, 0, tzinfo=tz)


def test_compute_next_run_weekdays_from_saturday() -> None:
    tz = ZoneInfo("America/Sao_Paulo")
    after = datetime(2026, 7, 25, 7, 0, tzinfo=tz)  # Saturday
    next_at = compute_next_run_at(
        schedule_kind="weekdays",
        hour=8,
        minute=0,
        timezone_name="America/Sao_Paulo",
        after=after,
    )
    assert next_at == datetime(2026, 7, 27, 8, 0, tzinfo=tz)


def test_compute_next_run_weekdays_same_weekday_before_hour() -> None:
    tz = ZoneInfo("America/Sao_Paulo")
    # Monday before schedule hour → same day
    after = datetime(2026, 7, 27, 7, 0, tzinfo=tz)
    next_at = compute_next_run_at(
        schedule_kind="weekdays",
        hour=8,
        minute=0,
        timezone_name="America/Sao_Paulo",
        after=after,
    )
    assert next_at == datetime(2026, 7, 27, 8, 0, tzinfo=tz)


def test_compute_next_run_weekly() -> None:
    tz = ZoneInfo("America/Sao_Paulo")
    # Tuesday 2026-07-21
    after = datetime(2026, 7, 21, 7, 0, tzinfo=tz)
    next_at = compute_next_run_at(
        schedule_kind="weekly",
        hour=8,
        minute=0,
        weekday=0,  # Monday
        timezone_name="America/Sao_Paulo",
        after=after,
    )
    assert next_at.weekday() == 0
    assert next_at == datetime(2026, 7, 27, 8, 0, tzinfo=tz)


def _artifacts() -> MagicMock:
    storage = MagicMock()
    storage.save_html.return_value = "/tmp/reports-runs/run-1.html"
    return storage


def test_run_report_fails_without_recipients() -> None:
    repo = MagicMock()
    repo.get_definition.return_value = {
        "id": "d1",
        "providerKey": "safety_stock_shortage_30d",
        "params": {"branch": "01"},
        "active": True,
    }
    repo.list_active_recipients.return_value = []
    use_case = RunReportDefinitionUseCase(
        repo, MagicMock(), MagicMock(), artifact_storage=_artifacts()
    )
    with pytest.raises(ValueError, match="destinatário"):
        use_case.execute(definition_id="d1")


def test_run_report_success_sends_mail_and_deliveries() -> None:
    repo = MagicMock()
    repo.get_definition.return_value = {
        "id": "d1",
        "providerKey": "safety_stock_shortage_30d",
        "params": {"branch": "01"},
        "active": True,
    }
    repo.list_active_recipients.return_value = [
        {"email": "a@delpi.com.br"},
        {"email": "b@delpi.com.br"},
    ]
    repo.create_run.return_value = {"id": "run-1", "status": "running"}
    repo.create_delivery.side_effect = [
        {"id": "del-1"},
        {"id": "del-2"},
    ]
    repo.finish_run.return_value = {"id": "run-1", "status": "succeeded"}
    repo.list_deliveries_for_run.return_value = [
        {"id": "del-1", "status": "sent"},
        {"id": "del-2", "status": "sent"},
    ]

    provider = MagicMock()
    provider.collect.return_value = ReportDataset(
        provider_key="safety_stock_shortage_30d",
        title="Rupturas",
        columns=("product_code",),
        rows=({"product_code": "X"},),
    )
    provider.render_email.return_value = EmailPayload(
        subject="Assunto",
        html_body="<p>ok</p>",
    )
    registry = MagicMock()
    registry.require.return_value = provider
    mail = MagicMock()

    use_case = RunReportDefinitionUseCase(
        repo, registry, mail, artifact_storage=_artifacts()
    )
    result = use_case.execute(definition_id="d1", trigger="manual")

    mail.send_mail_to.assert_called_once()
    assert mail.send_mail_to.call_args.kwargs["to_addresses"] == [
        "a@delpi.com.br",
        "b@delpi.com.br",
    ]
    assert result["status"] == "succeeded"
    assert len(result["deliveries"]) == 2
    repo.finish_run.assert_called_once()
    assert repo.finish_run.call_args.kwargs["status"] == "succeeded"
    assert (
        repo.finish_run.call_args.kwargs["summary"]["artifactHtmlPath"]
        == "/tmp/reports-runs/run-1.html"
    )


def test_run_report_batches_recipients() -> None:
    repo = MagicMock()
    repo.get_definition.return_value = {
        "id": "d1",
        "providerKey": "safety_stock_shortage_30d",
        "params": {"branch": "01"},
        "active": True,
    }
    repo.list_active_recipients.return_value = [
        {"email": f"u{i}@delpi.com.br"} for i in range(3)
    ]
    repo.create_run.return_value = {"id": "run-1", "status": "running"}
    repo.create_delivery.side_effect = [{"id": f"del-{i}"} for i in range(3)]
    repo.finish_run.return_value = {"id": "run-1", "status": "succeeded"}
    repo.list_deliveries_for_run.return_value = []

    provider = MagicMock()
    provider.collect.return_value = ReportDataset(
        provider_key="safety_stock_shortage_30d",
        title="Rupturas",
        columns=("product_code",),
        rows=(),
    )
    provider.render_email.return_value = EmailPayload(
        subject="Assunto", html_body="<p>ok</p>"
    )
    registry = MagicMock()
    registry.require.return_value = provider
    mail = MagicMock()

    use_case = RunReportDefinitionUseCase(
        repo,
        registry,
        mail,
        artifact_storage=_artifacts(),
        mail_batch_size=2,
    )
    use_case.execute(definition_id="d1")

    assert mail.send_mail_to.call_count == 2
    assert len(mail.send_mail_to.call_args_list[0].kwargs["to_addresses"]) == 2
    assert len(mail.send_mail_to.call_args_list[1].kwargs["to_addresses"]) == 1
    summary = repo.finish_run.call_args.kwargs["summary"]
    assert summary["batchCount"] == 2
    assert summary["sentCount"] == 3


def test_run_report_graph_failure_sanitized() -> None:
    repo = MagicMock()
    repo.get_definition.return_value = {
        "id": "d1",
        "providerKey": "safety_stock_shortage_30d",
        "params": {"branch": "01"},
        "active": True,
    }
    repo.list_active_recipients.return_value = [{"email": "a@delpi.com.br"}]
    repo.create_run.return_value = {"id": "run-1", "status": "running"}
    repo.create_delivery.return_value = {"id": "del-1"}
    repo.finish_run.return_value = {"id": "run-1", "status": "failed"}
    repo.list_deliveries_for_run.return_value = []

    provider = MagicMock()
    provider.collect.return_value = ReportDataset(
        provider_key="safety_stock_shortage_30d",
        title="Rupturas",
        columns=("product_code",),
        rows=(),
    )
    provider.render_email.return_value = EmailPayload(
        subject="Assunto",
        html_body="<p>ok</p>",
    )
    registry = MagicMock()
    registry.require.return_value = provider
    mail = MagicMock()
    mail.send_mail_to.side_effect = GraphMailError(
        "client_secret leaked in message"
    )

    use_case = RunReportDefinitionUseCase(
        repo, registry, mail, artifact_storage=_artifacts()
    )
    result = use_case.execute(definition_id="d1")

    assert result["status"] == "failed"
    error = repo.finish_run.call_args.kwargs["error"]
    assert "client_secret" not in error.lower()
    assert repo.finish_delivery.call_args.kwargs["status"] == "failed"


def test_process_due_uses_claim_without_double_advance() -> None:
    from app.application.use_cases.reports.process_due_report_schedules_use_case import (
        ProcessDueReportSchedulesUseCase,
    )

    repo = MagicMock()
    repo.claim_due_schedules.return_value = [
        {
            "id": "sch-1",
            "definitionId": "d1",
            "nextRunAt": "2026-07-22T11:00:00+00:00",
        }
    ]
    run_uc = MagicMock()
    run_uc.execute.return_value = {"id": "run-1", "status": "succeeded"}

    result = ProcessDueReportSchedulesUseCase(repo, run_uc).execute(limit=5)

    repo.claim_due_schedules.assert_called_once_with(limit=5)
    run_uc.execute.assert_called_once_with(definition_id="d1", trigger="schedule")
    assert not hasattr(repo, "update_schedule_next_run") or not repo.update_schedule_next_run.called
    assert result["processedCount"] == 1
    assert result["processed"][0]["runId"] == "run-1"


def test_run_report_accepts_event_trigger() -> None:
    repo = MagicMock()
    repo.get_definition.return_value = {
        "id": "d1",
        "providerKey": "safety_stock_shortage_30d",
        "params": {"branch": "01"},
        "active": True,
    }
    repo.list_active_recipients.return_value = [{"email": "a@delpi.com.br"}]
    repo.create_run.return_value = {"id": "run-1", "status": "running"}
    repo.create_delivery.return_value = {"id": "del-1"}
    repo.finish_run.return_value = {"id": "run-1", "status": "succeeded"}
    repo.list_deliveries_for_run.return_value = []

    provider = MagicMock()
    provider.collect.return_value = ReportDataset(
        provider_key="safety_stock_shortage_30d",
        title="Rupturas",
        columns=("product_code",),
        rows=(),
    )
    provider.render_email.return_value = EmailPayload(
        subject="Assunto", html_body="<p>ok</p>"
    )
    registry = MagicMock()
    registry.require.return_value = provider

    use_case = RunReportDefinitionUseCase(
        repo, registry, MagicMock(), artifact_storage=_artifacts()
    )
    use_case.execute(definition_id="d1", trigger="event")
    assert repo.create_run.call_args.kwargs["trigger"] == "event"


def test_replace_recipients_rejects_masked_directory_email() -> None:
    from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
        ReplaceReportRecipientsUseCase,
    )

    repo = MagicMock()
    repo.get_definition.return_value = {"id": "d1"}

    use_case = ReplaceReportRecipientsUseCase(repo)
    with pytest.raises(ValueError, match="mascarado"):
        use_case.execute(
            definition_id="d1",
            items=[{"userId": "u1", "email": "t***@delpi.com.br"}],
        )
    repo.replace_recipients.assert_not_called()


def test_replace_recipients_accepts_real_email() -> None:
    from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
        ReplaceReportRecipientsUseCase,
    )

    repo = MagicMock()
    repo.get_definition.return_value = {"id": "d1"}
    repo.replace_recipients.return_value = [
        {"userId": "u1", "email": "ti@delpi.com.br"}
    ]

    use_case = ReplaceReportRecipientsUseCase(repo)
    result = use_case.execute(
        definition_id="d1",
        items=[{"userId": "u1", "email": "ti@delpi.com.br"}],
    )

    assert result["total"] == 1
    repo.replace_recipients.assert_called_once_with(
        definition_id="d1",
        items=[{"userId": "u1", "email": "ti@delpi.com.br"}],
    )
