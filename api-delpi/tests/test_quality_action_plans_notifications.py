from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.services.pac_quality_portal_notification_service import (
    build_action_due_notification,
    pac_portal_notifications_enabled,
    send_pac_portal_notification,
)
from app.application.use_cases.quality_action_plans.dispatch_pac_quality_notifications_use_case import (
    DispatchPacQualityNotificationsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def test_pac_portal_notifications_enabled_requires_core_api() -> None:
    with patch("app.application.services.pac_quality_portal_notification_service.settings") as settings:
        settings.PAC_QUALITY_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"
        assert pac_portal_notifications_enabled() is True


def test_send_pac_portal_notification_posts_to_core_api() -> None:
    with patch("app.application.services.pac_quality_portal_notification_service.settings") as settings:
        settings.PAC_QUALITY_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"

        with patch("httpx.Client") as client_cls:
            client = client_cls.return_value.__enter__.return_value
            client.post.return_value.status_code = 201

            sent = send_pac_portal_notification(
                recipient_user_id="user-42",
                title="Ação PAC vencendo em breve",
                message="Plano PAC-2026-0001 vence amanhã.",
                action_target="/apps/quality-action-plans/plano/plan-1",
                dedupe_key="pac:action_due:act-1:2026-06-26",
                event_type="pac_action_due_soon",
            )

    assert sent is True
    payload = client.post.call_args.kwargs["json"]
    assert payload["userIds"] == ["user-42"]
    assert payload["sourceApp"] == "quality-action-plans"
    assert payload["category"] == "quality"


def test_build_action_due_notification_message() -> None:
    item = build_action_due_notification(
        action_id="act-1",
        plan_id="plan-1",
        plan_code="PAC-2026-0001",
        action_description="Revisar contenção",
        due_date="2026-06-26",
        recipient_user_id="user-42",
        dedupe_key="pac:action_due:act-1:2026-06-26",
    )
    assert "PAC-2026-0001" in item["message"]
    assert item["recipient_user_id"] == "user-42"


def test_list_actions_due_within_days_query() -> None:
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(return_value=[])

    repo.list_actions_due_within_days(days_ahead=2)

    query = repo.fetch_all.call_args[0][0]
    assert "quality_action_responsibles" in query
    assert repo.fetch_all.call_args[0][1] == (2, 2)


def test_dispatch_use_case_dry_run_counts_candidates() -> None:
    repo = MagicMock()
    repo.list_actions_due_within_days.return_value = [
        {
            "action_id": "act-1",
            "plan_id": "plan-1",
            "plan_code": "PAC-2026-0001",
            "description": "Ação X",
            "due_date": "2026-06-26",
            "responsible_user_id": "user-42",
        }
    ]
    repo.list_stalled_critical_plans.return_value = []
    repo.notification_already_sent.return_value = False

    with patch(
        "app.application.use_cases.quality_action_plans.dispatch_pac_quality_notifications_use_case.pac_portal_notifications_enabled",
        return_value=True,
    ):
        result = DispatchPacQualityNotificationsUseCase(repo).execute(dry_run=True)

    assert result.enabled is True
    assert result.dry_run is True
    assert result.candidates == 1
    assert result.sent == 1


def test_dispatch_use_case_skips_duplicate_keys() -> None:
    repo = MagicMock()
    repo.list_actions_due_within_days.return_value = [
        {
            "action_id": "act-1",
            "plan_id": "plan-1",
            "plan_code": "PAC-2026-0001",
            "description": "Ação X",
            "due_date": "2026-06-26",
            "responsible_user_id": "user-42",
        }
    ]
    repo.list_stalled_critical_plans.return_value = []
    repo.notification_already_sent.return_value = True

    with patch(
        "app.application.use_cases.quality_action_plans.dispatch_pac_quality_notifications_use_case.pac_portal_notifications_enabled",
        return_value=True,
    ), patch(
        "app.application.use_cases.quality_action_plans.dispatch_pac_quality_notifications_use_case.send_pac_portal_notification",
    ) as send_mock:
        result = DispatchPacQualityNotificationsUseCase(repo).execute(dry_run=False)

    assert result.skipped_duplicate == 1
    assert result.sent == 0
    send_mock.assert_not_called()


def test_record_notification_dispatch_uses_upsert_guard() -> None:
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.execute = MagicMock()

    repo.record_notification_dispatch(
        notification_key="pac:action_due:act-1:2026-06-26",
        event_type="pac_action_due_soon",
        recipient_user_id="user-42",
        entity_type="quality_action",
        entity_id="act-1",
    )

    query = repo.execute.call_args[0][0]
    assert "ON CONFLICT (notification_key) DO NOTHING" in query
