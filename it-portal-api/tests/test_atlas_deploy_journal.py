"""SQL adapter contract tests with an explicit transaction/unique simulation.

NOT a PostgreSQL integration test. Transaction semantics must be verified with
an isolated real PostgreSQL database before wiring an API or applying schema.
"""
import copy
import hashlib
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_journal import (
    PrepareIntent, JournalRejected, issue_challenge, store_prepared,
    _SQL_CREATE, _SQL_CHALLENGE, _SQL_CONSUME, _SQL_EVENT, _SQL_READ, _SQL_TIME,
)

NOW = datetime(2026, 11, 15, 15, tzinfo=timezone.utc)
SUBJECT = '11111111-2222-4333-8444-555555555555'
REQUEST = '01234567-89ab-4def-8abc-0123456789ab'


class CursorResult:
    def __init__(self, row=None): self.row = row
    def fetchone(self): return self.row


class FakePg:
    """Tiny transactional fake that models UNIQUE, rollback and one-shot state."""
    def __init__(self):
        self.now = NOW
        self.challenges = {}
        self.proposals = {}
        self.events = []
        self.statements = []
        self.fault = False

    @contextmanager
    def transaction(self):
        saved = copy.deepcopy((self.challenges, self.proposals, self.events))
        try:
            yield self
        except BaseException:
            self.challenges, self.proposals, self.events = saved
            raise

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        assert '%s' in sql or params is None
        if self.fault: raise RuntimeError('db password should never appear in errors')
        if sql == _SQL_TIME: return CursorResult((self.now,))
        if sql == _SQL_CHALLENGE:
            rid, subject, env, svc, digest, issued, expiry = params
            self.challenges[digest] = (rid, subject, env, svc, issued, expiry, None)
            return CursorResult()
        if sql == _SQL_CREATE:
            (pid, subject, req_id, env, svc, sha, base, phash,
             digest, issued, expiry) = params
            k = (subject, req_id)
            if k in self.proposals: return CursorResult(None)
            self.proposals[k] = (pid, subject, req_id, env, svc, sha, base,
                                 phash, digest, expiry, 'pending_approval')
            return CursorResult((pid,))
        if sql == _SQL_CONSUME:
            subject, env, svc, digest = params
            item = self.challenges.get(digest)
            if (item is None or item[1:4] != (subject, env, svc) or
                    item[-1] is not None or item[5] <= self.now):
                return CursorResult(None)
            self.challenges[digest] = item[:-1] + (self.now,)
            return CursorResult((item[0],))
        if sql == _SQL_EVENT:
            self.events.append(params)
            return CursorResult()
        if sql == _SQL_READ:
            return CursorResult(self.proposals.get(tuple(params)))
        raise AssertionError('unexpected SQL')


def intent(**changes):
    d = PrepareIntent(
        requester_subject=SUBJECT, request_id=REQUEST,
        environment='hml', service_id='it-portal-api',
        target_sha='a'*40, base_sha='b'*40, proposal_hash='c'*64,
    )
    return replace(d, **changes)


def challenge(db, **changes):
    return issue_challenge(db, requester_subject=changes.get('requester_subject', SUBJECT),
                           environment=changes.get('environment','hml'),
                           service_id=changes.get('service_id','it-portal-api'))


def test_issue_challenge_and_atomic_create():
    db=FakePg()
    nonce=challenge(db)
    assert len(nonce)==64 and hashlib.sha256(bytes.fromhex(nonce)).hexdigest() in db.challenges
    result=store_prepared(db, intent=intent(), signed_receipt_challenge=nonce)
    assert result.result=='created_pending_approval'
    assert len(db.proposals)==1 and len(db.events)==1
    assert list(db.challenges.values())[0][-1]==NOW
    assert len(db.statements)>=4
    assert 'ON CONFLICT (requester_subject, request_id) DO NOTHING' in _SQL_CREATE
    assert 'FOR UPDATE' in _SQL_READ


def test_duplicate_replay_has_same_proposal_id_no_new_nonce_or_event():
    db=FakePg()
    nonce=challenge(db)
    first=store_prepared(db,intent=intent(),signed_receipt_challenge=nonce)
    replay=store_prepared(db,intent=intent(),signed_receipt_challenge=nonce)
    assert replay.proposal_id==first.proposal_id
    assert replay.result=='replay_pending_approval'
    assert len(db.events)==1


def test_modified_payload_conflicts_without_changing_original_record():
    db=FakePg()
    nonce=challenge(db)
    store_prepared(db,intent=intent(),signed_receipt_challenge=nonce)
    snapshot=copy.deepcopy((db.proposals,db.events))
    with pytest.raises(JournalRejected,match='IDEMPOTENCY_PAYLOAD_CONFLICT'):
        store_prepared(db,intent=intent(target_sha='d'*40),signed_receipt_challenge=nonce)
    assert (db.proposals,db.events)==snapshot


def test_challenge_swapping_is_denied_on_replay():
    db=FakePg()
    nonce=challenge(db)
    store_prepared(db,intent=intent(),signed_receipt_challenge=nonce)
    other=challenge(db)
    with pytest.raises(JournalRejected,match='IDEMPOTENCY_PAYLOAD_CONFLICT'):
        store_prepared(db,intent=intent(),signed_receipt_challenge=other)


def test_bad_challenge_rolls_back_create():
    db=FakePg()
    with pytest.raises(JournalRejected,match='CHALLENGE_MISSING_OR_CONSUMED'):
        store_prepared(db,intent=intent(),signed_receipt_challenge='f'*64)
    assert not db.events and not db.proposals


def test_expired_and_wrong_service_challenges_rollback():
    for reason in ('expired','service'):
        db=FakePg()
        if reason=='expired':
            nonce=challenge(db)
            db.now+=timedelta(seconds=91)
        else:
            nonce=challenge(db, service_id='gateway')
        with pytest.raises(JournalRejected, match='CHALLENGE_MISSING_OR_CONSUMED'):
            store_prepared(db,intent=intent(),signed_receipt_challenge=nonce)
        assert len(db.proposals)==0 and len(db.events)==0


def test_database_failure_returns_sanitized_code():
    db=FakePg();db.fault=True
    with pytest.raises(JournalRejected) as error:
        challenge(db)
    assert str(error.value)=='JOURNAL_DATABASE_UNAVAILABLE'
    assert 'password' not in str(error.value)


@pytest.mark.parametrize('updates', [
    {'requester_subject':'not-uuid'}, {'request_id':'bad'},
    {'service_id':'../bad'}, {'environment':'dev'},
    {'target_sha':'main'}, {'base_sha':'a'*40},
    {'proposal_hash':'x'*64},
])
def test_bad_candidate_does_not_access_database(updates):
    db=FakePg()
    with pytest.raises(JournalRejected,match='PREPARE_INVALID'):
        store_prepared(db,intent=intent(**updates),signed_receipt_challenge='f'*64)
    assert not db.statements


def test_replay_closed_proposal_rejected():
    db=FakePg()
    nonce=challenge(db)
    store_prepared(db,intent=intent(),signed_receipt_challenge=nonce)
    k=(SUBJECT,REQUEST)
    db.proposals[k]=db.proposals[k][:-1]+('approved',)
    with pytest.raises(JournalRejected,match='IDEMPOTENCY_ALREADY_CLOSED'):
        store_prepared(db,intent=intent(),signed_receipt_challenge=nonce)
