from __future__ import annotations

from types import SimpleNamespace

from purchase_requests_app.application.services.purchase_request_notification_preference_service import (
    PurchaseRequestNotificationPreferenceService,
)
from purchase_requests_app.application.services.purchase_requests_portal_notification_service import (
    PurchaseRequestsPortalNotificationService,
)
from purchase_requests_app.application.use_cases.dispatch_purchase_request_approval_notifications_use_case import (
    DispatchPurchaseRequestApprovalNotificationsUseCase,
    JOB_KEY_PURCHASE_REQUEST_APPROVAL,
)
from purchase_requests_app.domain.services.purchase_request_approval_state_service import (
    aggregate_request_approval_states,
)
from purchase_requests_app.domain.services.purchase_request_approval_notification_content_service import (
    PurchaseRequestApprovedNotificationContentService,
    PurchaseRequestRejectedNotificationContentService,
)


def _item(**overrides) -> dict:
    item = {
        "branch": "01",
        "request_number": "164708",
        "request_item": "0001",
        "requester_protheus_user_id": "000234",
        "approval_raw": "B",
        "approval_status": "blocked",
        "approver_name": None,
        "request_issue_date": "2026-08-27",
    }
    item.update(overrides)
    return item


class _FakeGateway:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def list_approval_states(self, *, date_from=None, date_to=None, limit=500) -> dict:
        self.calls.append({"date_from": date_from, "limit": limit})
        return self.payload


class _FakeCursorRepo:
    def __init__(self, initial: int | None = None) -> None:
        self.values: dict[str, int] = {}
        if initial is not None:
            self.values[JOB_KEY_PURCHASE_REQUEST_APPROVAL] = initial

    def get_last_recno(self, job_key: str) -> int | None:
        return self.values.get(job_key)

    def upsert_last_recno(self, job_key: str, last_recno: int) -> dict:
        self.values[job_key] = int(last_recno)
        return {"job_key": job_key, "last_recno": int(last_recno)}


class _FakeStateRepo:
    """In-memory equivalent of the atomic claim semantics in Postgres."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict] = {}

    def insert_baseline(self, states) -> int:
        inserted = 0
        for state in states:
            key = (state["branch"], state["request_number"])
            if key in self.rows:
                continue
            self.rows[key] = dict(state) | {"notify_pending": False}
            inserted += 1
        return inserted

    def observe_and_claim(
        self,
        *,
        branch,
        request_number,
        approval_status,
        requester_protheus_user_id,
        approver_name,
        notifiable,
        claim_stale_seconds=300,
    ):
        key = (branch, request_number)
        row = self.rows.get(key)
        if row is None:
            row = {
                "branch": branch,
                "request_number": request_number,
                "approval_status": approval_status,
                "requester_protheus_user_id": requester_protheus_user_id,
                "approver_name": approver_name,
                "notify_pending": notifiable,
                "stale": False,
            }
            self.rows[key] = row
            return dict(row) if notifiable else None
        if notifiable and (row["approval_status"] != approval_status or (row["notify_pending"] and row.get("stale"))):
            row.update(
                {
                    "approval_status": approval_status,
                    "requester_protheus_user_id": requester_protheus_user_id,
                    "approver_name": approver_name,
                    "notify_pending": True,
                    "stale": False,
                }
            )
            return dict(row)
        if row["approval_status"] != approval_status:
            row["approval_status"] = approval_status
            row["requester_protheus_user_id"] = requester_protheus_user_id
            row["approver_name"] = approver_name
            row["notify_pending"] = False
        return None

    def mark_delivered(self, *, branch, request_number, approval_status) -> None:
        row = self.rows[(branch, request_number)]
        if row["notify_pending"] and row["approval_status"] == approval_status:
            row["notify_pending"] = False
            row["dispatch_result"] = "delivered"

    def mark_skipped(self, *, branch, request_number, approval_status, result="skipped") -> None:
        row = self.rows[(branch, request_number)]
        if row["notify_pending"] and row["approval_status"] == approval_status:
            row["notify_pending"] = False
            row["dispatch_result"] = result

    def touch_dispatch_error(self, *, branch, request_number) -> None:
        row = self.rows[(branch, request_number)]
        row["dispatch_result"] = "retry_pending"
        row["stale"] = True  # next cycle re-claims (stale claim)


class _FakeMappingRepo:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = list(rows or [])

    def list_mappings(self) -> list[dict]:
        return list(self.rows)

    def get_mapping_by_protheus_user_id(self, protheus_user_id: str) -> dict | None:
        normalized = (protheus_user_id or "").strip()
        for row in self.rows:
            if (row.get("protheus_user_id") or "").strip() == normalized:
                return dict(row)
        return None


def _notifier(posts: list[dict], status_code: int = 201, text: str = ""):
    def fake_post(url, **kwargs):
        posts.append({"url": url, **kwargs})
        return SimpleNamespace(status_code=status_code, text=text)

    return PurchaseRequestsPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="token",
        enabled=True,
        http_post=fake_post,
    )


def _use_case(
    *,
    gateway: _FakeGateway,
    states: _FakeStateRepo,
    cursor: _FakeCursorRepo,
    notifier,
    mapped: bool = True,
) -> DispatchPurchaseRequestApprovalNotificationsUseCase:
    mappings = (
        [{"user_id": "portal-1", "protheus_user_id": "000234", "mapping_status": "mapped"}]
        if mapped
        else []
    )
    return DispatchPurchaseRequestApprovalNotificationsUseCase(
        gateway=gateway,
        state_repository=states,
        cursor_repository=cursor,
        preference_service=PurchaseRequestNotificationPreferenceService(
            mapping_repository=_FakeMappingRepo(mappings),
        ),
        notification_service=notifier,
    )


def test_first_run_builds_baseline_without_notifications() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    cursor = _FakeCursorRepo(initial=None)
    result = _use_case(
        gateway=_FakeGateway({"items": [_item(), _item(request_item="0002")]}),
        states=states,
        cursor=cursor,
        notifier=_notifier(posts),
    ).execute()
    assert result["first_run"] is True
    assert result["baseline"] == 1  # aggregated to SC level
    assert result["dispatched"] == 0
    assert posts == []
    assert cursor.values[JOB_KEY_PURCHASE_REQUEST_APPROVAL] == 1
    assert ("01", "164708") in states.rows


def test_first_run_does_not_notify_already_approved_requests() -> None:
    posts: list[dict] = []
    result = _use_case(
        gateway=_FakeGateway({"items": [_item(approval_raw="L", approval_status="approved")]}),
        states=_FakeStateRepo(),
        cursor=_FakeCursorRepo(initial=None),
        notifier=_notifier(posts),
    ).execute()
    assert result["first_run"] is True
    assert posts == []


def test_blocked_to_approved_dispatches_once() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    use_case = _use_case(
        gateway=_FakeGateway(
            {"items": [_item(approval_raw="L", approval_status="approved",
                             approver_name="JOÃO SILVA")]}
        ),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    )
    result = use_case.execute()
    assert result["first_run"] is False
    assert result["dispatched"] == 1
    assert result["approved"] == 1
    assert len(posts) == 1
    body = posts[0]["json"]
    assert body["userIds"] == ["portal-1"]
    assert body["type"] == "success"
    assert body["category"] == "purchase_request_approved"
    assert body["metadata"]["event"] == "purchase_request_approved"
    assert body["metadata"]["approvalStatus"] == "approved"
    assert body["metadata"]["approverName"] == "JOÃO SILVA"
    assert body["metadata"]["dedupeKey"] == (
        "purchase-requests:purchase_request_approved:01:164708:approved"
    )
    assert body["action"]["target"] == (
        "/apps/purchase-requests?branch=01&request_number=164708"
    )
    assert "164708" in body["title"]
    assert "aprovada" in body["title"]
    assert "JOÃO SILVA" in body["message"]

    replay = use_case.execute()
    assert replay["dispatched"] == 0
    assert len(posts) == 1


def test_blocked_to_rejected_dispatches_once() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    result = _use_case(
        gateway=_FakeGateway(
            {"items": [_item(approval_raw="R", approval_status="rejected",
                             approver_name="MARIA SOUZA")]}
        ),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    ).execute()
    assert result["dispatched"] == 1
    assert result["rejected"] == 1
    body = posts[0]["json"]
    assert body["type"] == "warning"
    assert body["category"] == "purchase_request_rejected"
    assert body["metadata"]["event"] == "purchase_request_rejected"
    assert "rejeitada" in body["title"]
    assert "MARIA SOUZA" in body["message"]


def test_approved_to_approved_sends_nothing() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "approved",
          "requester_protheus_user_id": "000234", "approver_name": "JOÃO"}]
    )
    result = _use_case(
        gateway=_FakeGateway({"items": [_item(approval_raw="L", approval_status="approved")]}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    ).execute()
    assert result["claimed"] == 0
    assert result["dispatched"] == 0
    assert posts == []


def test_rejected_to_rejected_sends_nothing() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "rejected",
          "requester_protheus_user_id": "000234", "approver_name": "MARIA"}]
    )
    result = _use_case(
        gateway=_FakeGateway({"items": [_item(approval_raw="R", approval_status="rejected")]}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    ).execute()
    assert result["dispatched"] == 0
    assert posts == []


def test_approved_blocked_approved_notifies_again() -> None:
    posts: list[dict] = []
    notifier = _notifier(posts)
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    use_case = _use_case(
        gateway=_FakeGateway({"items": []}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=notifier,
    )
    use_case._gateway = _FakeGateway({"items": [_item(approval_raw="L", approval_status="approved")]})
    assert use_case.execute()["dispatched"] == 1

    use_case._gateway = _FakeGateway({"items": [_item(approval_raw="B", approval_status="blocked")]})
    assert use_case.execute()["dispatched"] == 0

    use_case._gateway = _FakeGateway({"items": [_item(approval_raw="L", approval_status="approved")]})
    assert use_case.execute()["dispatched"] == 1
    assert len(posts) == 2


def test_core_outage_keeps_transition_pending_and_retries() -> None:
    posts: list[dict] = []
    notifier = _notifier(posts, status_code=503, text="unavailable")
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    use_case = _use_case(
        gateway=_FakeGateway({"items": [_item(approval_raw="L", approval_status="approved")]}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=notifier,
    )
    result = use_case.execute()
    assert result["dispatched"] == 0
    assert result["retry"] == 1
    assert states.rows[("01", "164708")]["notify_pending"] is True

    # Core volta: o claim pendente (stale) é reivindicado e entregue.
    posts.clear()
    use_case._notifications = _notifier(posts)
    result = use_case.execute()
    assert result["dispatched"] == 1
    assert len(posts) == 1


def test_unmapped_requester_skips_without_breaking() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    result = _use_case(
        gateway=_FakeGateway({"items": [_item(approval_raw="L", approval_status="approved")]}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
        mapped=False,
    ).execute()
    assert result["dispatched"] == 0
    assert result["unmapped"] == 1
    assert posts == []
    assert states.rows[("01", "164708")]["notify_pending"] is False


def test_mapped_requester_dispatches_without_subscription() -> None:
    """Sem linha de subscription o usuário mapeado recebe — a preferência é da Core."""
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    result = _use_case(
        gateway=_FakeGateway({"items": [_item(approval_raw="L", approval_status="approved")]}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    ).execute()
    assert result["dispatched"] == 1
    assert result["unmapped"] == 0
    assert len(posts) == 1


def test_missing_approver_name_keeps_message_natural() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    _use_case(
        gateway=_FakeGateway({"items": [_item(approval_raw="L", approval_status="approved",
                                             approver_name=None)]}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    ).execute()
    message = posts[0]["json"]["message"]
    assert "foi aprovada por" not in message
    assert "foi aprovada" in message


def test_multi_item_request_dispatches_single_notification() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    items = [
        _item(request_item="0001", approval_raw="L", approval_status="approved"),
        _item(request_item="0002", approval_raw="L", approval_status="approved"),
        _item(request_item="0003", approval_raw="L", approval_status="approved"),
    ]
    result = _use_case(
        gateway=_FakeGateway({"items": items}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    ).execute()
    assert result["dispatched"] == 1
    assert len(posts) == 1


def test_mixed_items_rejected_wins_over_approved() -> None:
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    items = [
        _item(request_item="0001", approval_raw="L", approval_status="approved"),
        _item(request_item="0002", approval_raw="R", approval_status="rejected"),
    ]
    result = _use_case(
        gateway=_FakeGateway({"items": items}),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    ).execute()
    assert result["rejected"] == 1
    assert posts[0]["json"]["metadata"]["event"] == "purchase_request_rejected"


def test_new_request_seen_already_approved_notifies() -> None:
    posts: list[dict] = []
    result = _use_case(
        gateway=_FakeGateway({"items": [_item(approval_raw="L", approval_status="approved",
                                             request_number="164800")]}),
        states=_FakeStateRepo(),  # tabela já populada? não — mas cursor marca baseline feita
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    ).execute()
    assert result["dispatched"] == 1


def test_concurrent_claim_only_one_instance_dispatches() -> None:
    """Duas execuções sobre o mesmo repo: só a primeira claim vence."""
    posts: list[dict] = []
    states = _FakeStateRepo()
    states.insert_baseline(
        [{"branch": "01", "request_number": "164708", "approval_status": "blocked",
          "requester_protheus_user_id": "000234", "approver_name": None}]
    )
    payload = {"items": [_item(approval_raw="L", approval_status="approved")]}
    first = _use_case(
        gateway=_FakeGateway(payload),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    )
    second = _use_case(
        gateway=_FakeGateway(payload),
        states=states,
        cursor=_FakeCursorRepo(initial=1),
        notifier=_notifier(posts),
    )
    # Segunda instância "perde" a claim quando a primeira já marcou pending.
    first._states.rows[("01", "164708")]["notify_pending"] = True
    first._states.rows[("01", "164708")]["approval_status"] = "approved"
    result = second.execute()
    assert result["claimed"] == 0
    assert result["dispatched"] == 0


def test_aggregation_rules() -> None:
    states = aggregate_request_approval_states(
        [
            _item(request_item="0001", approval_status="approved"),
            _item(request_item="0002", approval_status="approved"),
        ]
    )
    assert states[0]["approval_status"] == "approved"

    states = aggregate_request_approval_states(
        [
            _item(request_item="0001", approval_status="approved"),
            _item(request_item="0002", approval_status="blocked"),
        ]
    )
    assert states[0]["approval_status"] == "blocked"

    states = aggregate_request_approval_states(
        [_item(request_item="0001", approval_raw="X", approval_status="")]
    )
    assert states[0]["approval_status"] == "unknown"


def test_content_services() -> None:
    approved = PurchaseRequestApprovedNotificationContentService
    rejected = PurchaseRequestRejectedNotificationContentService
    assert approved.notification_type() == "success"
    assert rejected.notification_type() == "warning"
    assert approved.category() == "purchase_request_approved"
    assert rejected.category() == "purchase_request_rejected"
    assert approved.build_deep_link_path(branch="02", request_number="164708") == (
        "/apps/purchase-requests?branch=02&request_number=164708"
    )
    assert "por JOÃO" in approved.format_message(
        request_number="164708", approver_name="JOÃO"
    )
    assert "rejeitada. Consulte" in rejected.format_message(
        request_number="164708", approver_name=None
    )
