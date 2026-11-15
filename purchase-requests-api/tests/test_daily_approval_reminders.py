from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from purchase_requests_app.application.services.purchase_requests_portal_notification_service import (
    PortalNotifyOutcome,
    PurchaseRequestsPortalNotificationService,
)
from purchase_requests_app.application.use_cases.dispatch_daily_approval_reminders_use_case import (
    DispatchDailyApprovalRemindersUseCase,
)
from purchase_requests_app.domain.services.purchase_request_pending_notification_content_service import (
    build_pending_notification,
)
from purchase_requests_app.infrastructure.gateways.delpi_purchase_requests_gateway import (
    DelpiPurchaseRequestsGateway,
)


def document(**overrides):
    return {
        "branch": "02",
        "request_number": "012345",
        "requester_protheus_user_id": "000123",
        "pending_approvers": [
            {
                "code": "000005",
                "name": "Aprovador A",
                "protheus_user_id": "000456",
                "level": "01",
            },
            {
                "code": "000006",
                "name": "Aprovador B",
                "protheus_user_id": "000789",
                "level": "01",
            },
        ],
        "products": [{"code": "CAB01", "description": "Cabo de força"}],
        **overrides,
    }


class Ledger:
    def __init__(self):
        self.keys = {}
        self.completed = {}
        self.prune = Mock()

    def claim(self, **key):
        identity = tuple(sorted(key.items()))
        if identity in self.keys:
            return None
        token = str(len(self.keys))
        self.keys[identity] = token
        return token

    def complete(self, *, claim_token, result):
        self.completed[claim_token] = result


def make_use_case(*, ledger=None, records=None, now=None, outcome=None):
    ledger = ledger or Ledger()
    gateway = Mock()
    gateway.list_pending_approvals.return_value = {
        "items": records if records is not None else [document()],
        "next_cursor": None,
    }
    identities = Mock()
    identities.portal_users_for_mapped_requester.side_effect = lambda code: [
        "portal-" + code
    ]
    notifications = Mock()
    notifications.send.return_value = (
        outcome if outcome is not None else PortalNotifyOutcome.sent()
    )
    clock = Mock(return_value=now or datetime(2026, 11, 15, 12, tzinfo=timezone.utc))
    use_case = DispatchDailyApprovalRemindersUseCase(
        gateway=gateway,
        repository=ledger,
        identities=identities,
        notifications=notifications,
        clock=clock,
    )
    return use_case, gateway, identities, notifications, clock, ledger


def test_sends_separate_requester_and_only_current_approvers_with_details():
    job, _, _, notifications, _, ledger = make_use_case()
    assert job.execute()["dispatched"] == 3
    payloads = [call.kwargs for call in notifications.send.call_args_list]
    assert payloads[0]["user_ids"] == ["portal-000123"]
    assert payloads[0]["category"] == "purchase_request_pending_requester"
    assert [p["user_ids"] for p in payloads[1:]] == [
        ["portal-000456"],
        ["portal-000789"],
    ]
    assert all(
        p["category"] == "purchase_request_pending_approver" for p in payloads[1:]
    )
    for payload in payloads:
        assert "012345" in payload["title"]
        assert "CAB01" in payload["html_content"]
        assert "Cabo de força" in payload["html_content"]
        assert "Aprovador A" in payload["html_content"]
        assert "Aprovador B" in payload["html_content"]
        assert "request=02%3A012345" in payload["action_target"]
    assert set(ledger.completed.values()) == {"delivered"}


def test_same_day_restart_and_next_business_day():
    job, _, _, notifications, clock, ledger = make_use_case()
    job.execute()
    job.execute()
    restarted, _, _, restarted_notifications, _, _ = make_use_case(ledger=ledger)
    assert restarted.execute()["dispatched"] == 0
    restarted_notifications.send.assert_not_called()
    # UTC 02:59 is still the preceding date in Brazil.
    clock.return_value = datetime(2026, 11, 16, 2, 59, tzinfo=timezone.utc)
    assert job.execute()["dispatched"] == 0
    clock.return_value = datetime(2026, 11, 16, 3, 0, tzinfo=timezone.utc)
    assert job.execute()["dispatched"] == 3
    assert notifications.send.call_count == 6


def test_empty_feed_stops_reminders_and_does_not_resend_old_pending_payload():
    job, gateway, _, notifications, _, _ = make_use_case()
    job.execute()
    gateway.list_pending_approvals.return_value = {"items": [], "next_cursor": None}
    assert job.execute()["dispatched"] == 0
    assert notifications.send.call_count == 3


def test_unmapped_recipient_recovered_same_day_and_duplicate_scr_groups():
    item = document()
    item["pending_approvers"].append(dict(item["pending_approvers"][0]))
    job, _, identities, notifications, _, _ = make_use_case(records=[item])
    identities.portal_users_for_mapped_requester.side_effect = lambda code: (
        [] if code == "000123" else ["p-" + code]
    )
    assert job.execute()["dispatched"] == 2
    identities.portal_users_for_mapped_requester.side_effect = lambda code: [
        "p-" + code
    ]
    assert job.execute()["dispatched"] == 1
    assert notifications.send.call_count == 3


@pytest.mark.parametrize(
    "outcome,result",
    [
        (PortalNotifyOutcome.retry_later(), None),
        (PortalNotifyOutcome.skip(), "skipped"),
    ],
)
def test_retry_remains_uncompleted_and_permanent_rejection_is_recorded(outcome, result):
    job, _, _, _, _, ledger = make_use_case(outcome=outcome)
    job.execute()
    if result:
        assert set(ledger.completed.values()) == {result}
    else:
        assert not ledger.completed


def test_keyset_pages_continue_across_cycles_and_reset_at_end():
    job, gateway, _, _, _, _ = make_use_case(records=[])
    cursor = {"after_branch": "01", "after_request_number": "100000"}
    gateway.list_pending_approvals.side_effect = [
        {"items": [], "next_cursor": cursor},
        {"items": [], "next_cursor": None},
        {"items": [], "next_cursor": None},
    ]
    for _ in range(3):
        job.execute()
    assert gateway.list_pending_approvals.call_args_list[1].kwargs == {
        **cursor,
        "limit": 100,
    }
    assert gateway.list_pending_approvals.call_args_list[2].kwargs == {"limit": 100}


def test_new_active_approver_receives_same_day_without_repeating_requester():
    job, gateway, _, notifications, _, _ = make_use_case()
    job.execute()
    item = document(
        pending_approvers=[{"name": "Próxima alçada", "protheus_user_id": "000999"}]
    )
    gateway.list_pending_approvals.return_value = {"items": [item], "next_cursor": None}
    assert job.execute()["dispatched"] == 1
    assert notifications.send.call_args.kwargs["user_ids"] == ["portal-000999"]


def test_large_details_fit_preview_and_escape_erp_content_without_losing_products():
    item = document(
        products=[
            {"code": str(i), "description": '<script>alert("x")</script>' + "a" * 100}
            for i in range(30)
        ]
    )
    content = build_pending_notification(item, recipient_role="requester")
    assert len(content["message"]) <= 500
    assert "<script>" not in content["html_content"]
    assert "&lt;script&gt;" in content["html_content"]
    assert content["html_content"].count("<li>") == 32


def test_gateway_service_feed_and_portal_html_transport():
    client = Mock()
    DelpiPurchaseRequestsGateway(client=client).list_pending_approvals(
        after_branch="01", after_request_number="123456"
    )
    assert client.get_path.call_args.args == (
        "/supplies/purchase-requests/pending-approvals",
    )
    post = Mock(return_value=SimpleNamespace(status_code=200))
    service = PurchaseRequestsPortalNotificationService(
        service_token="test-token", enabled=True, http_post=post
    )
    content = build_pending_notification(document(), recipient_role="approver")
    assert service.send(
        user_ids=["recipient"],
        dedupe_key="key",
        event_type=content["category"],
        **content,
    ).delivered
    payload = post.call_args.kwargs["json"]
    assert payload["presentation"] == "html"
    assert "CAB01" in payload["htmlContent"]


def test_old_request_deep_link_carries_issue_date_for_detail_filters():
    content = build_pending_notification(
        document(request_issue_date="2024-01-10"), recipient_role="requester"
    )
    assert "date_from=2024-01-10" in content["action_target"]


def test_lifespan_starts_daily_poller_and_master_gate_disables_it(monkeypatch):
    import asyncio
    from unittest.mock import patch
    from purchase_requests_app import main

    async def scenario(enabled):
        started = set()

        def loop(name):
            async def run():
                started.add(name)
                await asyncio.Event().wait()

            return run

        modules = {
            "daily_approval_reminder_job": "run_daily_approval_reminder_loop",
            "purchase_order_linked_notification_job": "run_purchase_order_linked_notification_loop",
            "purchase_receipt_recorded_notification_job": "run_purchase_receipt_recorded_notification_loop",
            "purchase_request_approval_notification_job": "run_purchase_request_approval_notification_loop",
        }
        from contextlib import ExitStack

        with ExitStack() as stack:
            stack.enter_context(patch.object(main, "check_credentials"))
            stack.enter_context(patch.object(main, "run_migrations_on_startup"))
            for module, method in modules.items():
                stack.enter_context(
                    patch(
                        f"purchase_requests_app.startup.{module}.{method}", loop(module)
                    )
                )
            monkeypatch.setattr(
                main.settings, "PURCHASE_REQUESTS_PO_NOTIFICATIONS_ENABLED", enabled
            )
            async with main.lifespan(main.app):
                await asyncio.sleep(0)
                assert started == (set(modules) if enabled else set())

    asyncio.run(scenario(True))
    asyncio.run(scenario(False))
