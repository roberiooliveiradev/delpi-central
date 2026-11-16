"""ATLAS P2.2h.2v-x: fresh Core human RBAC and HML-only blocked admission.

All Core calls mocked locally. NO real identity tokens, grants, DATABASE,
containers, routes, migrations or deployment operations are invoked.
"""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_core_gate import (
    ACCESS, DEPLOY_VIEW, DEPLOY_PREPARE,
    AtlasCoreGateError, FreshCorePrepareInspector,
    FreshCoreGrantObservation, TrustedHumanActor,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_full_readiness import (
    FullReadinessBlocked,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_hml_admission import (
    HMLAdmissionError, HMLPilotBlockedDiagnostic, HMLReadOnlyAdmissionReviewer,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_host_receipt_bridge import (
    ExpectedBaseRelease, PinnedHostTarget, SignedReceiptWire,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_readiness_review import (
    TargetReleaseReview,
)

NOW = datetime(2026, 11, 16, 23, 0, tzinfo=timezone.utc)
SUBJECT = "11111111-2222-4333-8444-555555555555"
TOKEN = "fixture-valid-jwt-from-authenticated-middleware-only"
SHA = "b" * 40
TARGET_SHA = "c" * 40
IMAGE = "sha256:" + "d" * 64
TARGET_IMAGE = "sha256:" + "e" * 64
ACTOR = TrustedHumanActor(
    subject=SUBJECT, principal_type="user", access_token=TOKEN,
)
RELEASE = TargetReleaseReview(
    requester_subject=SUBJECT, environment="hml", service_id="public-hub",
    target_commit_sha=TARGET_SHA, manifest_digest="sha256:" + "f" * 64,
    target_image_id=TARGET_IMAGE, statement_sha256="a" * 64,
)
HOST = PinnedHostTarget(
    host_id="srv-api-pilot", environment="hml", service_id="public-hub",
    container_name="delpi-hml-public-hub", compose_project="delpi-hml",
)
BASE = ExpectedBaseRelease(SHA, IMAGE)
RECEIPT = SignedReceiptWire(b"dummy-inert", "0" * 64)
NONCE = "1" * 64
REQUIRED = [ACCESS, DEPLOY_VIEW, DEPLOY_PREPARE]


def core_data(**updates):
    return {
        "id": SUBJECT, "permissions": list(REQUIRED),
        "is_superadmin": False, **updates,
    }


class FakeCore:
    def __init__(self, values=None, times=None):
        self.values = list(values if values is not None else [core_data(), core_data()])
        self.times = list(times if times is not None else [NOW, NOW + timedelta(seconds=2)])
        self.calls = []
        self.clock_calls = 0

    async def fetch(self, token, *, force_refresh=False):
        self.calls.append((token, force_refresh))
        value = self.values[len(self.calls)-1]
        if isinstance(value, Exception):
            raise value
        return value

    def clock(self):
        value = self.times[min(self.clock_calls, len(self.times)-1)]
        self.clock_calls += 1
        return value

    def inspector(self, *, enabled=True):
        return FreshCorePrepareInspector(
            fetch_rbac=self.fetch, clock=self.clock, enabled=enabled,
        )


class FakeFull:
    def __init__(self, data=None, failure=None):
        self.data = data if data is not None else full_result()
        self.failure = failure
        self.calls = []

    async def read(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure:
            raise self.failure
        return self.data


def full_result(**changes):
    return replace(FullReadinessBlocked(
        status="blocked",
        blocks=(
            "COLLECTOR_TRANSPORT_IDENTITY_NOT_PROVEN",
            "PREPARE_DISABLED", "ACT_DISABLED",
        ),
        environment="hml", service_id="public-hub",
        target_commit_sha=TARGET_SHA, target_image_id=TARGET_IMAGE,
        base_commit_sha=SHA, base_image_id=IMAGE, host_id=HOST.host_id,
        challenge_checked_at=NOW + timedelta(seconds=1),
        release_verified_at=NOW - timedelta(seconds=5),
        runtime_receipt_sha256="f"*64, git_receipt_sha256="e"*64,
    ), **changes)


def core_denied(code, actor=ACTOR, fake=None, enabled=True):
    f = fake or FakeCore()
    with pytest.raises(AtlasCoreGateError) as err:
        asyncio.run(f.inspector(enabled=enabled).read(actor=actor))
    assert err.value.code == code
    assert TOKEN not in str(err.value)
    assert SUBJECT not in str(err.value)
    return f


def run_hml(*, actor=ACTOR, release=RELEASE, host=HOST, base=BASE,
            core=None, full=None, enabled=True):
    c = core or FakeCore()
    f = full or FakeFull()
    reviewer = HMLReadOnlyAdmissionReviewer(
        core=c.inspector(), full=f, enabled=enabled,
    )
    async def execute():
        return await reviewer.review(
            actor=actor, release=release, host=host, base=base,
            runtime_receipt=RECEIPT, checkout_receipt=RECEIPT,
            challenge=NONCE,
        )
    return asyncio.run(execute()), c, f


def deny_hml(code, *, actor=ACTOR, release=RELEASE, host=HOST,
             base=BASE, core=None, full=None, enabled=True):
    c = core or FakeCore()
    f = full or FakeFull()
    reviewer = HMLReadOnlyAdmissionReviewer(
        core=c.inspector(), full=f, enabled=enabled,
    )
    with pytest.raises(HMLAdmissionError) as err:
        asyncio.run(reviewer.review(
            actor=actor, release=release, host=host, base=base,
            runtime_receipt=RECEIPT, checkout_receipt=RECEIPT,
            challenge=NONCE,
        ))
    assert err.value.code == code
    assert TOKEN not in str(err.value)
    assert NONCE not in str(err.value)
    return c, f


def test_core_default_off_makes_zero_network_requests():
    c = core_denied("ATLAS_CORE_INSPECTION_DISABLED", enabled=False)
    assert not c.calls


@pytest.mark.parametrize("actor", [
    replace(ACTOR, principal_type="service"),
    replace(ACTOR, principal_type="bot"),
    replace(ACTOR, subject="not-uuid"),
    replace(ACTOR, subject="11111111-2222-3333-8444-555555555555"),
    replace(ACTOR, access_token=""),
    replace(ACTOR, access_token=" token "),
    replace(ACTOR, access_token="a" * 16385),
])
def test_core_rejects_invalid_nonhuman_or_untrusted_actor_before_query(actor):
    c = core_denied("ATLAS_CORE_IDENTITY_DENIED", actor=actor)
    assert not c.calls


def test_exact_fresh_core_grants_required_and_never_become_prepare():
    c = FakeCore(values=[core_data()], times=[NOW])
    result = asyncio.run(c.inspector().read(actor=ACTOR))
    assert c.calls == [(TOKEN, True)]
    assert result.subject == SUBJECT
    assert result.checked_at == NOW
    assert result.required_grants_present is True
    assert result.prepare_eligible is False
    assert result.can_execute is False
    assert not hasattr(result, "approval_id")


@pytest.mark.parametrize("grants", [
    [ACCESS, DEPLOY_VIEW], [ACCESS, DEPLOY_PREPARE],
    [DEPLOY_VIEW, DEPLOY_PREPARE],
    ["*"], ["it-portal.*"], ["it-portal.manage"],
])
def test_core_superadmin_wildcards_and_missing_explicit_grants_do_not_bypass(grants):
    c = FakeCore(values=[core_data(permissions=grants, is_superadmin=True)])
    core_denied("ATLAS_CORE_EXPLICIT_GRANT_MISSING", fake=c)
    assert c.calls == [(TOKEN, True)]


@pytest.mark.parametrize("bad", [
    None, {"id":SUBJECT}, {"id":SUBJECT,"permissions":" ".join(REQUIRED)},
    {"id":SUBJECT,"permissions":[ACCESS,None,DEPLOY_PREPARE]},
    {"id":SUBJECT,"permissions":list(REQUIRED)+[False]},
    {"id":SUBJECT,"permissions":list(REQUIRED)*350},
])
def test_invalid_core_response_fails_closed(bad):
    c = FakeCore(values=[bad])
    core_denied("ATLAS_CORE_RESPONSE_INVALID", fake=c)


def test_core_subject_must_match_middleware_identity():
    c = FakeCore(values=[core_data(id="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")])
    core_denied("ATLAS_CORE_IDENTITY_MISMATCH", fake=c)


def test_core_failure_is_sanitized_and_never_uses_stale_cache():
    c = FakeCore(values=[RuntimeError("Core URL and secret token")])
    core_denied("ATLAS_CORE_UNAVAILABLE", fake=c)
    assert c.calls == [(TOKEN, True)]


def test_core_invalid_clock_does_not_claim_freshness():
    c = FakeCore(values=[core_data()], times=[NOW.replace(tzinfo=None)])
    core_denied("ATLAS_CORE_CLOCK_INVALID", fake=c)


def test_hml_admission_disabled_before_any_rbac_or_full_reader():
    c, f = deny_hml("ATLAS_HML_ADMISSION_DISABLED", enabled=False)
    assert not c.calls and not f.calls


def test_hml_rejects_prod_or_requester_mismatch_before_external_readers():
    for options in (
        {"release": replace(RELEASE, environment="prod")},
        {"host": replace(HOST, environment="prod")},
        {"release": replace(RELEASE, requester_subject="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")},
        {"release": replace(RELEASE, service_id="database")},
        {"actor": replace(ACTOR, principal_type="service")},
    ):
        c, f = deny_hml("ATLAS_HML_ACTOR_OR_TARGET_DENIED", **options)
        assert not c.calls and not f.calls


def test_valid_double_fresh_core_and_full_signed_evidence_still_blocked():
    report, c, f = run_hml()
    assert type(report) is HMLPilotBlockedDiagnostic
    assert report.status == "blocked"
    assert report.core_checked_at == NOW + timedelta(seconds=2)
    assert report.journal_checked_at == NOW + timedelta(seconds=1)
    assert report.base_commit_sha == SHA and report.target_commit_sha == TARGET_SHA
    assert report.environment == "hml" and report.service_id == "public-hub"
    assert c.calls == [(TOKEN, True), (TOKEN, True)]
    assert len(f.calls) == 1
    assert f.calls[0]["challenge"] == NONCE
    assert set((
        "BACKUP_RESTORE_TEST_NOT_ATTESTED",
        "ROLLBACK_REHEARSAL_NOT_ATTESTED",
        "MIGRATION_REVERSIBILITY_NOT_ATTESTED",
        "HOST_COLLECTOR_TRANSPORT_NOT_ATTESTED",
        "POSTGRES_ONE_SHOT_WRITER_NOT_APPROVED",
        "PREPARE_DISABLED", "ACT_DISABLED",
    )).issubset(report.blocks)
    assert report.core_explicit_grants_observed
    assert not report.collector_identity_attested
    assert not report.recovery_verified
    assert not report.migrations_verified
    assert not report.challenge_consumed
    assert not report.prepare_eligible
    assert not report.can_execute


def test_missing_core_permission_prevents_any_expensive_oci_host_read():
    c = FakeCore(values=[core_data(permissions=[ACCESS, DEPLOY_VIEW])])
    c, f = deny_hml("ATLAS_HML_CORE_UNAVAILABLE_OR_DENIED", core=c)
    assert len(c.calls) == 1 and not f.calls


def test_core_revoke_between_first_and_second_read_is_fail_closed():
    c = FakeCore(values=[
        core_data(), core_data(permissions=[ACCESS, DEPLOY_VIEW]),
    ])
    c, f = deny_hml("ATLAS_HML_CORE_RECHECK_DENIED", core=c)
    assert len(c.calls) == 2 and len(f.calls) == 1


def test_core_unavailable_after_expensive_release_check_is_denied():
    c = FakeCore(values=[core_data(), RuntimeError("Core offline")])
    c, f = deny_hml("ATLAS_HML_CORE_RECHECK_DENIED", core=c)
    assert len(c.calls) == 2 and len(f.calls) == 1


def test_core_recheck_outside_sixty_second_window_is_denied():
    c = FakeCore(times=[NOW, NOW + timedelta(seconds=61)])
    c, f = deny_hml("ATLAS_HML_CORE_RECHECK_DRIFT", core=c)
    assert len(c.calls) == 2 and len(f.calls) == 1


def test_full_release_reader_failure_is_sanitized_and_never_grants():
    c, f = deny_hml(
        "ATLAS_HML_RELEASE_HOST_OR_JOURNAL_DENIED",
        full=FakeFull(failure=RuntimeError("private database URI")),
    )
    assert len(c.calls) == 1 and len(f.calls) == 1


@pytest.mark.parametrize("changes", [
    {"status":"approved"}, {"can_execute":True},
    {"prepare_eligible":True}, {"core_permission_verified":True},
    {"host_collector_identity_attested":True},
    {"backup_and_rollback_verified":True}, {"migrations_safe":True},
    {"one_shot_challenge_consumed":True},
    {"target_commit_sha":"0"*40},
    {"blocks":("ACT_DISABLED",)},
])
def test_forged_upstream_completion_or_identity_is_not_trusted(changes):
    c, f = deny_hml(
        "ATLAS_HML_UPSTREAM_CONTRACT_INVALID",
        full=FakeFull(data=full_result(**changes)),
    )
    assert len(c.calls) == 1 and len(f.calls) == 1


def test_hml_modules_do_not_register_routes_or_grants_or_write_journal():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "it_portal_app/infrastructure/persistence"
    for name in ("atlas_deploy_core_gate.py", "atlas_deploy_hml_admission.py"):
        source = (root/name).read_text()
        for forbidden in (
            "@router.", "@mcp.", "CREATE ROLE", "GRANT ",
            "psycopg.connect", "docker compose", "subprocess.run",
            "UPDATE it_portal", "INSERT INTO it_portal",
        ):
            assert forbidden not in source
