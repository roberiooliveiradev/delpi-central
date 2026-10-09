"""Requester backfill — classify/repair logic over a fake gateway.

The gateway is what the production script uses: list rows in the window,
raw ticket detail (user_recipient), authoritative requester read, and
the bounded add_ticket_requester write.
"""

from helpdesk_app.maintenance.repair_missing_requesters import (
    ALREADY_CORRECT,
    AMBIGUOUS,
    CONFLICT,
    ERROR,
    NO_IDENTITY,
    REPAIRABLE,
    apply_repairs,
    scan,
)


class FakeBackfillGateway:
    def __init__(self, rows, requesters=None, fail_ids=()):
        self._rows = {int(r["id"]): r for r in rows}
        self._requesters = dict(requesters or {})
        self._fail_ids = set(fail_ids)
        self.writes = []

    def list_ticket_rows(self, token, *, created_from, created_to):
        assert token
        return list(self._rows.values())

    def ticket_row(self, token, ticket_id):
        return self._rows.get(int(ticket_id), {})

    def ticket_requester(self, token, ticket_id):
        return self._requesters.get(int(ticket_id))

    def add_ticket_requester(self, token, ticket_id, user_id):
        if int(ticket_id) in self._fail_ids:
            raise RuntimeError("glpi refused")
        self.writes.append((int(ticket_id), int(user_id)))
        self._requesters[int(ticket_id)] = int(user_id)


def _row(ticket_id, recipient_id=None, title="t", name="Maria"):
    row = {"id": ticket_id, "name": title, "date_creation": "2026-10-01T10:00:00"}
    if recipient_id is not None:
        row["user_recipient"] = {"id": recipient_id, "name": name}
    elif recipient_id is None and name is not None:
        row["user_recipient"] = {"id": None, "name": name}
    return row


def test_missing_requester_with_recipient_is_repaired():
    gw = FakeBackfillGateway([_row(1, recipient_id=12)])
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    assert report.findings[0].classification == REPAIRABLE
    apply_repairs(gw, "tok", report)
    assert report.repaired == [1]
    assert gw.writes == [(1, 12)]
    assert report.findings[0].classification == ALREADY_CORRECT


def test_already_correct_is_skipped_without_write():
    gw = FakeBackfillGateway([_row(2, recipient_id=12)], requesters={2: 12})
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    assert report.findings[0].classification == ALREADY_CORRECT
    apply_repairs(gw, "tok", report)
    assert gw.writes == []
    assert report.repaired == []


def test_retry_after_repair_is_idempotent():
    gw = FakeBackfillGateway([_row(3, recipient_id=12)])
    first = scan(gw, "tok", from_iso="a", to_iso="b")
    apply_repairs(gw, "tok", first)
    second = scan(gw, "tok", from_iso="a", to_iso="b")
    apply_repairs(gw, "tok", second)
    assert second.findings[0].classification == ALREADY_CORRECT
    assert gw.writes == [(3, 12)]


def test_conflicting_requester_is_untouched():
    gw = FakeBackfillGateway([_row(4, recipient_id=12)], requesters={4: 77})
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    assert report.findings[0].classification == CONFLICT
    apply_repairs(gw, "tok", report)
    assert gw.writes == []
    assert gw._requesters[4] == 77


def test_recipient_without_identity_is_ambiguous_and_untouched():
    gw = FakeBackfillGateway([_row(5, recipient_id=None)])
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    assert report.findings[0].classification == AMBIGUOUS
    apply_repairs(gw, "tok", report)
    assert gw.writes == []


def test_no_recipient_identity_is_out_of_repair():
    gw = FakeBackfillGateway([{"id": 6, "name": "t", "date_creation": "2026-10-01T10:00:00"}])
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    assert report.findings[0].classification == NO_IDENTITY
    apply_repairs(gw, "tok", report)
    assert gw.writes == []


def test_write_failure_marks_only_that_ticket():
    gw = FakeBackfillGateway(
        [_row(7, recipient_id=12), _row(8, recipient_id=15)], fail_ids={7}
    )
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    apply_repairs(gw, "tok", report)
    assert report.failed == [7]
    assert report.repaired == [8]
    assert gw.writes == [(8, 15)]


def test_distinct_historical_identities_preserved():
    gw = FakeBackfillGateway(
        [_row(9, recipient_id=12, name="Ana"), _row(10, recipient_id=44, name="Bia")]
    )
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    apply_repairs(gw, "tok", report)
    assert gw.writes == [(9, 12), (10, 44)]
    assert gw._requesters == {9: 12, 10: 44}


def test_readback_mismatch_is_failure_not_success():
    class MismatchGw(FakeBackfillGateway):
        def add_ticket_requester(self, token, ticket_id, user_id):
            self.writes.append((int(ticket_id), int(user_id)))
            self._requesters[int(ticket_id)] = 999  # GLPI stored a different id

    gw = MismatchGw([_row(11, recipient_id=12)])
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    apply_repairs(gw, "tok", report)
    assert report.failed == [11]
    assert report.repaired == []
    assert report.findings[0].classification == ERROR


def test_requester_present_but_recipient_missing_is_conflict():
    gw = FakeBackfillGateway(
        [{"id": 12, "name": "t", "date_creation": "2026-10-01T10:00:00"}],
        requesters={12: 33},
    )
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    assert report.findings[0].classification == CONFLICT
    apply_repairs(gw, "tok", report)
    assert gw.writes == []


def test_trashed_ticket_is_out_of_scope():
    row = _row(13, recipient_id=12)
    row["is_deleted"] = True
    gw = FakeBackfillGateway([row])
    report = scan(gw, "tok", from_iso="a", to_iso="b")
    assert report.findings[0].classification == "OUT_OF_SCOPE"
    apply_repairs(gw, "tok", report)
    assert gw.writes == []
