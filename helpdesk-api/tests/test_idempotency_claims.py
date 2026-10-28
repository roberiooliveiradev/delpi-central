"""Idempotency claim protocol — regressions for uncertain post-write states.

GLPI offers neither distributed transactions nor native idempotency, so
exactly-once cannot be guaranteed end-to-end. What IS guaranteed:

- a key is atomically claimed BEFORE the external side effect
  (``INSERT ... ON CONFLICT`` / locked dict insert) — two concurrent
  same-key requests can never both execute the write;
- any failure after the side effect (crash, lost response, failed
  result save) leaves the claim ``in_flight`` — same-key retries fail
  closed with ``idempotency_in_flight`` until reconciliation by
  authoritative read, instead of re-executing blindly;
- a completed governed response (including the 207 partial that carries
  the persisted ``document_id``) is replayed under the same key without
  a second upload;
- provable pre-side-effect rejections (expired OAuth session, feature
  gate) release the claim so a corrected intent is not bricked forever;
- a key reused with a different intent is blocked, never replayed.
"""

from __future__ import annotations

import threading
import time

import pytest

from helpdesk_app.domain.errors import GlpiUnavailable, GlpiValidation
from helpdesk_app.infrastructure.persistence.memory import MemoryIdempotencyStore
from tests.conftest import FakeGlpi, auth_headers, build_client, link


class _CrashAfterWriteGlpi(FakeGlpi):
    """GLPI persists the Document, then the response is lost."""

    def upload_ticket_document(self, access_token, *, ticket_id, filename, content, mime, title=None):
        self.calls += 1
        self.uploads.append((ticket_id, filename, content, mime, title))
        raise GlpiUnavailable("connection lost after Document was created")


class _SlowUploadGlpi(FakeGlpi):
    """Widens the race window so a concurrent claim overlaps."""

    def upload_ticket_document(self, access_token, **kwargs):
        time.sleep(0.15)
        return super().upload_ticket_document(access_token, **kwargs)


class _PartialAfterWriteGlpi(FakeGlpi):
    """Document persisted, then a downstream postcondition fails — the
    client tags the error with the persisted identifier."""

    def upload_ticket_document(self, access_token, *, ticket_id, filename, content, mime, title=None):
        self.calls += 1
        self.uploads.append((ticket_id, filename, content, mime, title))
        exc = GlpiValidation("Document_Item link failed")
        exc.details = {"document_id": 777}
        raise exc


class _FailingSaveStore(MemoryIdempotencyStore):
    """Result save blows up once — simulating DB loss after the write."""

    def __init__(self):
        super().__init__()
        self.fail_next_save = True

    def save(self, subject, operation, key, response):
        if self.fail_next_save:
            self.fail_next_save = False
            raise GlpiUnavailable("idempotency store write failed")
        return super().save(subject, operation, key, response)


def _upload(client, filename="evidence.png", content=b"img", key="idem-x"):
    return client.post(
        "/tickets/7/attachments",
        files={"file": (filename, content, "image/png")},
        headers={**auth_headers(), "Idempotency-Key": key},
    )


# ---------------------------------------------------------------------------
# GLPI persists + BFF loses the response → blocked, never re-executed
# ---------------------------------------------------------------------------


def test_post_write_crash_leaves_claim_in_flight_and_blocks_retry():
    glpi = _CrashAfterWriteGlpi()
    client, _ = build_client(glpi=glpi)
    link(client)
    glpi.session_uid = 68

    first = _upload(client)
    assert first.status_code == 502
    assert first.json()["error"] == "glpi_unavailable"
    assert len(glpi.uploads) == 1  # the side effect DID happen

    # Same-key retry: the prior execution may have persisted — fail
    # closed instead of re-uploading.
    retry = _upload(client)
    assert retry.status_code == 409
    body = retry.json()
    assert body["error"] == "idempotency_in_flight"
    assert body["intent"]["filename"] == "evidence.png"
    assert len(glpi.uploads) == 1  # no duplicate document


# ---------------------------------------------------------------------------
# GLPI persists + idempotency save fails → same block
# ---------------------------------------------------------------------------


def test_failed_result_save_leaves_claim_in_flight():
    glpi = FakeGlpi()
    store = _FailingSaveStore()
    client, _ = build_client(glpi=glpi, idempotency=store)
    link(client)
    glpi.session_uid = 68

    first = _upload(client)
    assert first.status_code == 502
    assert len(glpi.uploads) == 1

    retry = _upload(client)
    assert retry.status_code == 409
    assert retry.json()["error"] == "idempotency_in_flight"
    assert len(glpi.uploads) == 1


# ---------------------------------------------------------------------------
# Concurrent same-key requests — exactly one side effect
# ---------------------------------------------------------------------------


def test_concurrent_same_key_requests_produce_single_side_effect():
    glpi = _SlowUploadGlpi()
    client, _ = build_client(glpi=glpi)
    link(client)
    glpi.session_uid = 68

    results = []

    def hit():
        results.append(_upload(client))

    threads = [threading.Thread(target=hit) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one Document was written.
    assert len(glpi.uploads) == 1
    statuses = sorted(r.status_code for r in results)
    # Winner stored a governed response; loser either replayed it (same
    # body) or failed closed in-flight — never a second write.
    assert statuses in ([201, 201], [201, 409])
    if statuses == [201, 201]:
        bodies = [r.json() for r in results]
        assert bodies[0] == bodies[1]


# ---------------------------------------------------------------------------
# Rejected-before-write releases the claim — corrected retry proceeds
# ---------------------------------------------------------------------------


def test_prewrite_rejection_releases_claim_for_corrected_retry():
    glpi = FakeGlpi()
    client, _ = build_client(glpi=glpi)
    # No linked session → LinkRequired before any side effect.
    rejected = _upload(client)
    assert rejected.status_code == 409
    assert rejected.json()["error"] == "glpi_link_required"
    assert len(glpi.uploads) == 0

    # Link and retry the SAME key — the claim was released.
    link(client)
    glpi.session_uid = 68
    retried = _upload(client)
    assert retried.status_code == 201
    assert len(glpi.uploads) == 1


def test_validation_rejection_keeps_claim_blocked():
    """A same-key replay of a rejected validation intent stays blocked —
    the store cannot prove nothing persisted downstream, so it fails
    closed rather than silently re-executing or replaying."""
    glpi = FakeGlpi()
    client, _ = build_client(glpi=glpi)
    link(client)
    glpi.session_uid = 68
    # ticket 99 does not exist → GlpiNotFound pre-write (but classified
    # conservatively as uncertain).
    rejected = client.post(
        "/tickets/99/attachments",
        files={"file": ("e.png", b"img", "image/png")},
        headers={**auth_headers(), "Idempotency-Key": "idem-404"},
    )
    assert rejected.status_code == 404
    retry = client.post(
        "/tickets/99/attachments",
        files={"file": ("e.png", b"img", "image/png")},
        headers={**auth_headers(), "Idempotency-Key": "idem-404"},
    )
    assert retry.status_code == 409
    assert retry.json()["error"] == "idempotency_in_flight"


# ---------------------------------------------------------------------------
# Post-Document failure with persisted id → governed 207, replayable
# ---------------------------------------------------------------------------


def test_post_document_failure_governs_partial_with_document_id():
    glpi = _PartialAfterWriteGlpi()
    client, _ = build_client(glpi=glpi)
    link(client)
    glpi.session_uid = 68

    first = _upload(client)
    assert first.status_code == 207
    body = first.json()
    assert body["document_id"] == 777
    assert body["outcome"] == "verification_failed"
    assert body["author_verified"] is False
    assert len(glpi.uploads) == 1

    # Reconciliation: the SAME key replays the governed partial — the
    # document_id is recovered without any new upload.
    replay = _upload(client)
    assert replay.status_code == 207
    assert replay.json() == body
    assert len(glpi.uploads) == 1


# ---------------------------------------------------------------------------
# Key reuse with a different intent → blocked, never replayed
# ---------------------------------------------------------------------------


def test_key_reuse_with_different_intent_is_blocked():
    glpi = FakeGlpi()
    client, _ = build_client(glpi=glpi)
    link(client)
    glpi.session_uid = 68

    first = _upload(client, filename="a.png", content=b"A")
    assert first.status_code == 201

    # Same key, different content — a different intent must not replay
    # the stored response nor execute a new write.
    second = _upload(client, filename="b.png", content=b"B")
    assert second.status_code == 409
    assert second.json()["error"] == "idempotency_in_flight"
    assert len(glpi.uploads) == 1
