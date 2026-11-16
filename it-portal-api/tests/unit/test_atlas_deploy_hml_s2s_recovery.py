"""P2.2h.2y-aa: Keycloak S2S boundary + recovery metadata + combined HML gate.

Uses the real ServiceTokenValidator policy, with the cryptographic JWT
decoder stubbed ONLY in isolated tests; no real Keycloak/JWKS/GHCR/DB/host.
No request routes, secret provisioning, grants or deploy.
"""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_core_gate import TrustedHumanActor
from it_portal_app.infrastructure.persistence.atlas_deploy_hml_admission import HMLPilotBlockedDiagnostic
from it_portal_app.infrastructure.persistence.atlas_deploy_hml_s2s_collector import (
    AtlasCollectorIdentityError, HMLCollectorClientObservation,
    HMLCollectorIdentityPolicy, HMLCollectorS2SVerifier,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_hml_recovery_review import (
    HMLRecoveryReviewError, RecoveryArtifactMetadata, inspect_hml_recovery_metadata,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_hml_technical_admission import (
    HMLTechnicalAdmissionBlocked, HMLTechnicalAdmissionError, HMLTechnicalReadinessReviewer,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_host_receipt_bridge import (
    ExpectedBaseRelease, PinnedHostTarget, SignedReceiptWire,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_readiness_review import TargetReleaseReview

NOW = datetime(2026,11,16,23,55,tzinfo=timezone.utc)
HML = PinnedHostTarget(
    host_id="srv-api-pilot",environment="hml",service_id="public-hub",
    container_name="delpi-hml-public-hub",compose_project="delpi-hml",
)
CONFIG = HMLCollectorIdentityPolicy(
    host_id="srv-api-pilot",
    client_id="itp-atlas-hml-srv-api-01",
    audience="it-portal-api",
)
TOKEN = "keycloak-s2s-opaque-test-value"
SUBJECT = "11111111-2222-4333-8444-555555555555"
HUMAN = TrustedHumanActor(
    subject=SUBJECT, principal_type="user", access_token="human-keycloak-jwt-fake",
)
BASE = ExpectedBaseRelease("a"*40,"sha256:"+"b"*64)
RELEASE = TargetReleaseReview(
    requester_subject=SUBJECT,environment="hml",service_id="public-hub",
    target_commit_sha="c"*40,manifest_digest="sha256:"+"d"*64,
    target_image_id="sha256:"+"e"*64,statement_sha256="f"*64,
)
NONCE = "1"*64
RECEIPT = SignedReceiptWire(b"not-an-actual-receipt", "0"*64)


def claims(**changes):
    return {
        "azp":CONFIG.client_id,
        "sub":"service-account-atlas-hml",
        "scope":"it-portal.atlas.hml.observe",
        "aud":[CONFIG.audience],
        "iss":"https://keycloak.delpi.invalid/realms/delpi",
        "exp":int((NOW+timedelta(minutes=5)).timestamp()),
        **changes,
    }


def s2s(monkeypatch, *, item=None, config=CONFIG, now=NOW, enabled=True):
    observed=[]
    def token_decoder(raw, expected_audience=None):
        observed.append((raw,expected_audience))
        if isinstance(item,Exception):
            raise item
        return claims() if item is None else item
    monkeypatch.setattr(
        "delpi_auth.service_token_validator.validate_token", token_decoder,
    )
    return HMLCollectorS2SVerifier(
        policy=config,clock=lambda:now,enabled=enabled,
    ),observed


def s2s_denied(monkeypatch,code, *, token=TOKEN, host=HML, **kw):
    verifier,observed=s2s(monkeypatch,**kw)
    with pytest.raises(AtlasCollectorIdentityError) as err:
        verifier.verify(service_token=token,host=host)
    assert err.value.code==code
    assert TOKEN not in str(err.value)
    return observed


def test_keycloak_signed_client_boundary_uses_real_shared_validator_with_pinned_audience(monkeypatch):
    verifier,observed=s2s(monkeypatch)
    v=verifier.verify(service_token=TOKEN,host=HML)
    assert observed==[(TOKEN,CONFIG.audience)]
    assert type(v) is HMLCollectorClientObservation
    assert v.client_id==CONFIG.client_id and v.host_id==HML.host_id
    assert v.scope=="it-portal.atlas.hml.observe"
    assert v.keycloak_client_verified is True
    assert v.token_expires_at==NOW+timedelta(minutes=5)
    assert not v.host_process_attested
    assert not v.transport_mutual_auth_attested
    assert not v.checkout_attested
    assert not v.challenge_consumed
    assert not v.prepare_eligible
    assert not v.can_execute


def test_s2s_default_off_does_not_call_token_decoder(monkeypatch):
    assert not s2s_denied(monkeypatch,"ATLAS_COLLECTOR_S2S_DISABLED",enabled=False)


@pytest.mark.parametrize("config",[
    replace(CONFIG,client_id="all-clients"),
    replace(CONFIG,audience=""),
    replace(CONFIG,host_id="../../root"),
])
def test_s2s_bad_owner_configuration_fails_closed_before_decoder(monkeypatch,config):
    assert not s2s_denied(
        monkeypatch,"ATLAS_COLLECTOR_S2S_CONFIG_INVALID",config=config,
    )


@pytest.mark.parametrize("host,token",[
    (replace(HML,environment="prod"),TOKEN),
    (replace(HML,compose_project="infra"),TOKEN),
    (replace(HML,container_name="delpi-public-hub"),TOKEN),
    (replace(HML,host_id="another-host"),TOKEN),
    (replace(HML,service_id="linux-ops"),TOKEN),
    (HML,""),
    (HML," "+TOKEN),
    (HML,"A"*16385),
])
def test_s2s_rejects_noncanon_host_and_bad_token_before_decoder(monkeypatch,host,token):
    assert not s2s_denied(
        monkeypatch,"ATLAS_COLLECTOR_S2S_TARGET_DENIED",
        host=host,token=token,
    )


@pytest.mark.parametrize("change",[
    {"azp":"another-keycloak-client"},
    {"scope":"it-portal.observations.ingest"},
    {"scope":""},
])
def test_s2s_wrong_client_or_scope_is_denied(monkeypatch,change):
    observed=s2s_denied(monkeypatch,"ATLAS_COLLECTOR_S2S_DENIED",item=claims(**change))
    assert observed==[(TOKEN,CONFIG.audience)]


@pytest.mark.parametrize("change",[
    {"aud":["another-bff"]},
    {"iss":""},
    {"exp":None},
    {"sub":""},
])
def test_invalid_identity_projection_denied(monkeypatch,change):
    code=("ATLAS_COLLECTOR_S2S_DENIED" if change=={"sub":""}
          else "ATLAS_COLLECTOR_S2S_CLAIMS_INVALID")
    observed=s2s_denied(monkeypatch,code,item=claims(**change))
    assert len(observed)==1


@pytest.mark.parametrize("delta",[
    timedelta(seconds=1),timedelta(seconds=5),
    timedelta(seconds=-1),timedelta(minutes=16),
])
def test_service_token_expired_or_overlong_is_denied(monkeypatch,delta):
    item=claims(exp=int((NOW+delta).timestamp()))
    s2s_denied(monkeypatch,"ATLAS_COLLECTOR_S2S_LIFETIME_DENIED",item=item)


def test_s2s_jwt_service_validation_failure_does_not_leak_internal_error(monkeypatch):
    observed=s2s_denied(
        monkeypatch,"ATLAS_COLLECTOR_S2S_DENIED",
        item=ValueError("private JWKS token credential"),
    )
    assert len(observed)==1


def test_s2s_requires_aware_clock(monkeypatch):
    assert not s2s_denied(
        monkeypatch,"ATLAS_COLLECTOR_S2S_CLOCK_INVALID",
        now=NOW.replace(tzinfo=None),
    )


def recovery(*, now=NOW, **overrides):
    meta=RecoveryArtifactMetadata(
        backup_inventory_ref="backup-inventory-hml-20261116",
        restore_test_ref="restore-ci-rehearsal",
        restore_tested_at=NOW-timedelta(minutes=20),
        rollback_test_ref="rollback-ci-rehearsal",
        rollback_tested_at=NOW-timedelta(minutes=30),
        rollback_image_id=BASE.image_id,
        migration_review_ref="migration-policy-readonly",
        migration_reviewed_at=NOW-timedelta(minutes=40),
        migration_plan_sha256="f"*64,
        observed_by_subject=SUBJECT,
        reviewed_by_subject="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
    )
    return inspect_hml_recovery_metadata(
        base=BASE,submitted=replace(meta,**overrides),now=now,
    )


def test_no_recovery_evidence_never_auto_fills_backup_restore_rollback():
    report=inspect_hml_recovery_metadata(base=BASE,submitted=None,now=NOW)
    assert report.status=="blocked"
    assert not report.submitted_metadata_consistent
    assert not report.submitted_metadata_recent
    assert not report.actual_restore_verified
    assert not report.actual_rollback_verified
    assert not report.actual_migrations_verified
    assert not report.independent_reviewer_verified
    assert not report.prepare_eligible
    assert not report.can_execute
    assert "RECOVERY_METADATA_NOT_SUBMITTED" in report.blocks


def test_complete_self_declared_recovery_metadata_still_never_authorizes():
    r=recovery()
    assert r.status=="blocked"
    assert r.submitted_metadata_consistent
    assert r.submitted_metadata_recent
    assert r.rollback_matches_base
    assert not r.actual_restore_verified
    assert not r.actual_rollback_verified
    assert not r.actual_migrations_verified
    assert not r.prepare_eligible and not r.can_execute
    assert "ROLLBACK_EXECUTION_INDEPENDENT_PROOF_MISSING" in r.blocks
    assert "PREPARE_DISABLED" in r.blocks and "ACT_DISABLED" in r.blocks


@pytest.mark.parametrize("change,block",[
    ({"rollback_image_id":"sha256:"+"c"*64},"ROLLBACK_BASE_IMAGE_NOT_MATCHED"),
    ({"rollback_image_id":None},"ROLLBACK_BASE_IMAGE_NOT_MATCHED"),
    ({"backup_inventory_ref":"../../prod/secrets"},"RECOVERY_METADATA_INCOMPLETE_OR_MALFORMED"),
    ({"restore_test_ref":"https://evil.invalid/file"},"RECOVERY_METADATA_INCOMPLETE_OR_MALFORMED"),
    ({"migration_plan_sha256":"bad"},"RECOVERY_METADATA_INCOMPLETE_OR_MALFORMED"),
    ({"observed_by_subject":SUBJECT,"reviewed_by_subject":SUBJECT},
      "INDEPENDENT_REVIEWER_NOT_ESTABLISHED"),
    ({"reviewed_by_subject":None},"INDEPENDENT_REVIEWER_NOT_ESTABLISHED"),
    ({"restore_tested_at":NOW-timedelta(hours=73)},
      "RECOVERY_METADATA_OUTSIDE_REVIEW_WINDOW"),
    ({"rollback_tested_at":NOW+timedelta(seconds=6)},
      "RECOVERY_METADATA_OUTSIDE_REVIEW_WINDOW"),
    ({"migration_reviewed_at":NOW.replace(tzinfo=None)},
      "RECOVERY_METADATA_OUTSIDE_REVIEW_WINDOW"),
])
def test_malformed_mismatched_stale_claims_get_blocking_diagnostics(change,block):
    r=recovery(**change)
    assert block in r.blocks
    assert not r.prepare_eligible and not r.can_execute


def test_malformed_recovery_container_or_clock_rejected():
    with pytest.raises(HMLRecoveryReviewError,match="ATLAS_RECOVERY_METADATA_INVALID"):
        inspect_hml_recovery_metadata(base=BASE,submitted={"backup":"fake"},now=NOW)
    with pytest.raises(HMLRecoveryReviewError,match="ATLAS_RECOVERY_METADATA_INVALID"):
        inspect_hml_recovery_metadata(
            base=BASE,submitted=None,now=NOW.replace(tzinfo=None),
        )


def human_result(**changes):
    return replace(HMLPilotBlockedDiagnostic(
        status="blocked",
        blocks=(
            "BACKUP_RESTORE_TEST_NOT_ATTESTED",
            "COLLECTOR_TRANSPORT_IDENTITY_NOT_PROVEN",
            "PREPARE_DISABLED","ACT_DISABLED",
        ),
        environment="hml",service_id="public-hub",
        base_commit_sha=BASE.commit_sha,target_commit_sha=RELEASE.target_commit_sha,
        core_checked_at=NOW+timedelta(seconds=2),
        journal_checked_at=NOW+timedelta(seconds=1),
    ),**changes)


class FakeHumanReadiness:
    def __init__(self, result=None, issue=None):
        self.result=human_result() if result is None else result
        self.issue=issue
        self.calls=[]
    async def review(self,**args):
        self.calls.append(args)
        if self.issue is not None:
            raise self.issue
        return self.result


def combined(monkeypatch, *, item=None, host=HML, release=RELEASE,
             actor=HUMAN, recovery_data=None, human=None,
             now=NOW, enabled=True, s2s_enabled=True):
    verifier, observed=s2s(monkeypatch,item=item,now=now,enabled=s2s_enabled)
    fake=human or FakeHumanReadiness()
    wrapper=HMLTechnicalReadinessReviewer(
        s2s=verifier,human_and_ci=fake,enabled=enabled,
    )
    async def execute():
        return await wrapper.read(
            service_token=TOKEN,actor=actor,release=release,
            host=host,base=BASE,
            runtime_receipt=RECEIPT,checkout_receipt=RECEIPT,
            challenge=NONCE,recovery=recovery_data,
        )
    return execute,observed,fake


def deny_combined(monkeypatch,code,**kw):
    run,seen,human=combined(monkeypatch,**kw)
    with pytest.raises(HMLTechnicalAdmissionError) as err:
        asyncio.run(run())
    assert err.value.code==code
    assert TOKEN not in str(err.value)
    assert NONCE not in str(err.value)
    return seen,human


def test_combined_disabled_does_not_reach_s2s_or_core(monkeypatch):
    seen,human=deny_combined(
        monkeypatch,"ATLAS_HML_TECHNICAL_DISABLED",enabled=False,
    )
    assert not seen and not human.calls


def test_combined_denies_prod_or_nonhuman_without_s2s_lookup(monkeypatch):
    for args in (
        {"host":replace(HML,environment="prod")},
        {"release":replace(RELEASE,environment="prod")},
        {"release":replace(RELEASE,requester_subject="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")},
        {"actor":replace(HUMAN,principal_type="service")},
    ):
        seen,human=deny_combined(
            monkeypatch,"ATLAS_HML_TECHNICAL_SCOPE_DENIED",**args,
        )
        assert not seen and not human.calls


def test_combined_s2s_denied_before_human_or_network_provenance(monkeypatch):
    seen,human=deny_combined(
        monkeypatch,"ATLAS_HML_TECHNICAL_S2S_DENIED",
        item=claims(scope="it-portal.observations.ingest"),
    )
    assert len(seen)==1 and not human.calls


def test_combined_full_pilot_review_still_blocked_with_no_recovery(monkeypatch):
    run,seen,human=combined(monkeypatch)
    report=asyncio.run(run())
    assert len(seen)==1 and len(human.calls)==1
    assert type(report) is HMLTechnicalAdmissionBlocked
    assert report.status=="blocked"
    assert report.environment=="hml" and report.service_id=="public-hub"
    assert report.host_id==HML.host_id
    assert report.collector_client_id==CONFIG.client_id
    assert report.source_commit_sha==BASE.commit_sha
    assert report.target_commit_sha==RELEASE.target_commit_sha
    assert report.inspected_at==NOW+timedelta(seconds=2)
    assert report.keycloak_client_token_verified
    assert not report.host_process_attested
    assert not report.host_transport_attested
    assert not report.backup_restored
    assert not report.rollback_tested
    assert not report.migrations_safe
    assert not report.core_prepare_authorized
    assert not report.challenge_consumed
    assert not report.prepare_eligible and not report.can_execute
    assert "RECOVERY_METADATA_NOT_SUBMITTED" in report.blocks
    assert "COLLECTOR_TRANSPORT_MUTUAL_AUTH_UNPROVEN" in report.blocks
    assert "PREPARE_DISABLED" in report.blocks and "ACT_DISABLED" in report.blocks


def test_combined_hml_works_as_diagnostic_even_with_complete_metadata(monkeypatch):
    meta=RecoveryArtifactMetadata(
        backup_inventory_ref="backup-inventory-hml",
        restore_test_ref="restore-review",
        restore_tested_at=NOW-timedelta(minutes=1),
        rollback_test_ref="rollback-review",
        rollback_tested_at=NOW-timedelta(minutes=2),
        rollback_image_id=BASE.image_id,
        migration_review_ref="migration-review",
        migration_reviewed_at=NOW-timedelta(minutes=3),
        migration_plan_sha256="e"*64,
        observed_by_subject=SUBJECT,
        reviewed_by_subject="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
    )
    run,_,_=combined(monkeypatch,recovery_data=meta)
    result=asyncio.run(run())
    assert result.status=="blocked" and not result.can_execute
    assert "BACKUP_RESTORE_INDEPENDENT_PROOF_MISSING" in result.blocks


@pytest.mark.parametrize("changes",[
    {"status":"eligible"},
    {"prepare_eligible":True},
    {"can_execute":True},
    {"collector_identity_attested":True},
    {"challenge_consumed":True},
    {"blocks":("ACT_DISABLED",)},
    {"target_commit_sha":"a"*40},
])
def test_combined_rejects_forged_human_readiness_result(monkeypatch,changes):
    seen,human=deny_combined(
        monkeypatch,"ATLAS_HML_TECHNICAL_READINESS_CONTRACT_INVALID",
        human=FakeHumanReadiness(result=human_result(**changes)),
    )
    assert len(seen)==1 and len(human.calls)==1


def test_combined_rejects_expired_service_token_after_slow_core(monkeypatch):
    seen,human=deny_combined(
        monkeypatch,"ATLAS_HML_TECHNICAL_IDENTITY_STALE",
        human=FakeHumanReadiness(result=human_result(
            core_checked_at=NOW+timedelta(minutes=6),
        )),
    )
    assert seen and human.calls


def test_combined_propagates_human_core_failure_without_secrets(monkeypatch):
    seen,human=deny_combined(
        monkeypatch,"ATLAS_HML_TECHNICAL_READINESS_DENIED",
        human=FakeHumanReadiness(issue=RuntimeError("server secret")),
    )
    assert seen and human.calls


def test_no_route_mcp_db_write_docker_or_secret_provisioning():
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]/"it_portal_app/infrastructure/persistence"
    for name in (
        "atlas_deploy_hml_s2s_collector.py",
        "atlas_deploy_hml_recovery_review.py",
        "atlas_deploy_hml_technical_admission.py",
    ):
        text=(root/name).read_text(encoding="utf-8")
        for forbidden in (
            "@router.", "@mcp.", "CREATE ROLE", "GRANT ",
            "INSERT INTO it_portal", "UPDATE it_portal",
            "docker compose", "docker.sock", "subprocess.run",
            "os.system", "psycopg.connect(",
        ):
            assert forbidden not in text
