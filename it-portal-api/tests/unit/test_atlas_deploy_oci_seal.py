"""No network, database, Docker, GitHub authentication or deploy is used."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_oci_seal import (
    ApprovalEvidence, CIReleaseEvidence, HostRuntimeEvidence, OCIProposalIntent,
    OCIGateRejected, seal_oci_candidate, evaluate_portal_approval,
    REPOSITORY, IMAGE, WORKFLOW, SOURCE_REF,
)

NOW = datetime(2026, 11, 16, 14, 0, tzinfo=timezone.utc)
REQUESTER = "11111111-2222-4333-8444-555555555555"
APPROVER = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
SHA = 'f81ddd0075de1e4ef8bb68ca58791e9c43e70759'
BASE = '03cecb7ed90946c799a66ca9b22b45beb221282e'
MANIFEST = 'sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a'
TARGET = 'sha256:1a4cfd5d0370e35739cb679d3c0170845e55213488c2c5f7c7d249afba5365a9'
CURRENT = 'sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb'


def inputs(environment='prod'):
    project = 'infra' if environment == 'prod' else 'delpi-hml'
    container = 'delpi-public-hub' if environment == 'prod' else 'delpi-hml-public-hub'
    intent = OCIProposalIntent(
        requester_subject=REQUESTER, request_id='01234567-89ab-4def-8abc-0123456789ab',
        environment=environment, service_id='public-hub', target_commit_sha=SHA,
        base_commit_sha=BASE, manifest_digest=MANIFEST, target_image_id=TARGET,
        base_image_id=CURRENT, rollback_image_id=CURRENT,
        attestation_statement_sha256='c' * 64, host_challenge_sha256='e' * 64,
        preview_hash='d' * 64,
        rollback_ready=True,
    )
    ci = CIReleaseEvidence(
        repository=REPOSITORY, image=IMAGE, workflow=WORKFLOW,
        source_ref=SOURCE_REF, commit_sha=SHA, manifest_digest=MANIFEST,
        image_config_id=TARGET, statement_sha256='c' * 64,
        verified_at=NOW - timedelta(seconds=20), signature_verified=True,
    )
    host = HostRuntimeEvidence(
        environment=environment, service_id='public-hub',
        container_name=container, compose_project=project,
        commit_sha=BASE, running_image_id=CURRENT,
        observed_at=NOW-timedelta(seconds=2), challenge_verified=True,
        challenge_sha256='e'*64,
        running=True, healthy=True, checkout_clean=True,
    )
    return intent, ci, host


def seal(i=None,c=None,h=None,now=NOW,enabled=True):
    defaults=inputs()
    return seal_oci_candidate(intent=i or defaults[0],ci=c or defaults[1],
                              host=h or defaults[2],now=now,
                              backend_policy_enabled=enabled)


def reject(code, *,i=None,c=None,h=None,now=NOW,enabled=True):
    with pytest.raises(OCIGateRejected) as exc:
        seal(i=i,c=c,h=h,now=now,enabled=enabled)
    assert exc.value.code==code


def test_exact_manifest_and_two_distinct_imageids_produce_candidate_only():
    candidate=seal()
    assert candidate.status=='candidate_only'
    assert len(candidate.binding_sha256)==64
    assert candidate.expires_at==NOW+timedelta(minutes=10)
    assert candidate.requester_subject==REQUESTER
    assert candidate.environment=='prod'


def test_cross_env_hml_isolated():
    i,c,h=inputs('hml')
    candidate=seal(i,c,h)
    assert candidate.environment=='hml'
    assert candidate.binding_sha256!=seal().binding_sha256


def test_deterministic_for_same_evidence_and_timestamp():
    assert seal().binding_sha256==seal().binding_sha256
    assert seal(now=NOW+timedelta(seconds=1)).binding_sha256!=seal().binding_sha256


def test_default_policy_deny():
    reject('OCI_POLICY_DISABLED', enabled=False)


@pytest.mark.parametrize('property,value,code',[
    ('requester_subject', 'unknown', 'OCI_TARGET_INVALID'),
    ('request_id','invalid','OCI_TARGET_INVALID'),
    ('service_id','gateway','OCI_TARGET_INVALID'),
    ('service_id','public-hub;docker rm -f','OCI_TARGET_INVALID'),
    ('environment','dev','OCI_TARGET_INVALID'),
    ('environment','../../prod','OCI_TARGET_INVALID'),
    ('target_commit_sha','f81ddd','OCI_COMMIT_INVALID'),
    ('target_commit_sha','F'*40,'OCI_COMMIT_INVALID'),
    ('base_commit_sha','latest','OCI_COMMIT_INVALID'),
    ('target_commit_sha',BASE,'OCI_ALREADY_DEPLOYED'),
    ('manifest_digest','sha256:bad','OCI_DIGEST_INVALID'),
    ('manifest_digest','latest','OCI_DIGEST_INVALID'),
    ('manifest_digest','sha512:'+'a'*64,'OCI_DIGEST_INVALID'),
    ('target_image_id','sha256:'+'C'*64,'OCI_DIGEST_INVALID'),
    ('base_image_id','sha256:'+'a'*63,'OCI_DIGEST_INVALID'),
    ('rollback_image_id',TARGET,'OCI_ROLLBACK_IMAGE_INVALID'),
    ('base_image_id',TARGET,'OCI_ROLLBACK_IMAGE_INVALID'),
    ('attestation_statement_sha256','malformed','OCI_BINDING_FIELDS_INVALID'),
    ('host_challenge_sha256','malformed','OCI_BINDING_FIELDS_INVALID'),
    ('preview_hash','short','OCI_BINDING_FIELDS_INVALID'),
    ('rollback_ready',False,'OCI_ROLLBACK_NOT_READY'),
])
def test_invalid_intent_fails_closed(property,value,code):
    i,c,h=inputs()
    reject(code,i=replace(i,**{property:value}),c=c,h=h)


@pytest.mark.parametrize('property,value,code',[
    ('repository','other/repository','OCI_ATTESTATION_INVALID'),
    ('image','ghcr.io/other','OCI_ATTESTATION_INVALID'),
    ('workflow','other.yml','OCI_ATTESTATION_INVALID'),
    ('source_ref','refs/heads/testing','OCI_ATTESTATION_INVALID'),
    ('signature_verified',False,'OCI_ATTESTATION_INVALID'),
    ('commit_sha',BASE,'OCI_ATTESTATION_DRIFT'),
    ('manifest_digest','sha256:'+'e'*64,'OCI_ATTESTATION_DRIFT'),
    ('image_config_id',CURRENT,'OCI_ATTESTATION_DRIFT'),
    ('statement_sha256','f'*64,'OCI_ATTESTATION_DRIFT'),
    ('verified_at',NOW-timedelta(seconds=121),'OCI_ATTESTATION_STALE'),
    ('verified_at',NOW+timedelta(seconds=6),'OCI_ATTESTATION_STALE'),
    ('verified_at',NOW.replace(tzinfo=None),'OCI_ATTESTATION_STALE'),
])
def test_untrusted_ci_never_seals(property,value,code):
    i,c,h=inputs()
    reject(code,i=i,c=replace(c,**{property:value}),h=h)


@pytest.mark.parametrize('property,value,code',[
    ('environment','hml','OCI_HOST_DRIFT'),
    ('service_id','gateway','OCI_HOST_DRIFT'),
    ('container_name','delpi-hml-public-hub','OCI_HOST_DRIFT'),
    ('compose_project','delpi-hml','OCI_HOST_DRIFT'),
    ('commit_sha',SHA,'OCI_HOST_DRIFT'),
    ('running_image_id',TARGET,'OCI_HOST_DRIFT'),
    ('challenge_sha256','a'*64,'OCI_HOST_DRIFT'),
    ('running',False,'OCI_HOST_UNTRUSTED'),
    ('healthy',False,'OCI_HOST_UNTRUSTED'),
    ('checkout_clean',False,'OCI_HOST_UNTRUSTED'),
    ('challenge_verified',False,'OCI_HOST_UNTRUSTED'),
    ('observed_at',NOW-timedelta(seconds=121),'OCI_HOST_STALE'),
    ('observed_at',NOW+timedelta(seconds=6),'OCI_HOST_STALE'),
    ('observed_at',NOW.replace(tzinfo=None),'OCI_HOST_STALE'),
])
def test_host_drifts_and_health_fail_closed(property,value,code):
    i,c,h=inputs()
    reject(code,i=i,c=c,h=replace(h,**{property:value}))


def approval_for(candidate):
    return ApprovalEvidence(
        proposal_id=str(uuid4()),binding_sha256=candidate.binding_sha256,
        requester_subject=REQUESTER,approver_subject=APPROVER,
        environment='prod',service_id='public-hub',state='approved',
        approved_at=NOW,expires_at=candidate.expires_at,
        permission_fresh=True,permissions_checked_at=NOW,
        approved_in_portal=True,revoked=False,
        already_consumed=False,
    )


def test_synthetic_approval_gate_is_not_execution():
    c=seal()
    assert evaluate_portal_approval(candidate=c,approval=approval_for(c),now=NOW,
                                    backend_policy_enabled=True)=='approval_evidence_shape_only'


def test_approval_default_deny():
    c=seal()
    with pytest.raises(OCIGateRejected,match='OCI_POLICY_DISABLED'):
        evaluate_portal_approval(candidate=c,approval=approval_for(c),now=NOW)


@pytest.mark.parametrize('property,value,code',[
    ('proposal_id','fake','OCI_APPROVAL_IDENTITY_INVALID'),
    ('requester_subject','fake','OCI_APPROVAL_IDENTITY_INVALID'),
    ('approver_subject',REQUESTER,'OCI_SELF_APPROVAL_DENIED'),
    ('requester_subject','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','OCI_APPROVAL_TARGET_MISMATCH'),
    ('environment','hml','OCI_APPROVAL_TARGET_MISMATCH'),
    ('service_id','gateway','OCI_APPROVAL_TARGET_MISMATCH'),
    ('binding_sha256','f'*64,'OCI_APPROVAL_BINDING_DRIFT'),
    ('state','revoked','OCI_APPROVAL_NOT_ACTIVE'),
    ('permission_fresh',False,'OCI_APPROVAL_NOT_ACTIVE'),
    ('approved_in_portal',False,'OCI_APPROVAL_NOT_ACTIVE'),
    ('revoked',True,'OCI_APPROVAL_NOT_ACTIVE'),
    ('already_consumed',True,'OCI_APPROVAL_NOT_ACTIVE'),
    ('expires_at',NOW+timedelta(minutes=11),'OCI_APPROVAL_EXPIRED'),
    ('approved_at',NOW+timedelta(seconds=6),'OCI_APPROVAL_EXPIRED'),
    ('approved_at',NOW-timedelta(seconds=1),'OCI_APPROVAL_EXPIRED'),
    ('permissions_checked_at',NOW-timedelta(seconds=121),'OCI_APPROVAL_PERMISSION_STALE'),
])
def test_approval_replay_cross_target_and_revocation_denied(property,value,code):
    candidate=seal()
    approval=replace(approval_for(candidate),**{property:value})
    with pytest.raises(OCIGateRejected) as exc:
        evaluate_portal_approval(candidate=candidate,approval=approval,now=NOW,
                                 backend_policy_enabled=True)
    assert exc.value.code==code


def test_approval_expires_in_ten_minutes():
    c=seal()
    with pytest.raises(OCIGateRejected,match='OCI_APPROVAL_EXPIRED'):
        evaluate_portal_approval(candidate=c,approval=approval_for(c),
                                 now=NOW+timedelta(minutes=10),backend_policy_enabled=True)


def test_candidate_cannot_be_edited_between_issue_and_approval():
    from dataclasses import FrozenInstanceError
    c=seal()
    with pytest.raises(FrozenInstanceError):
        c.binding_sha256='a'*64


def test_no_dangerous_runtime_dependencies():
    from pathlib import Path
    code=Path(__file__).resolve().parents[2] / 'it_portal_app/infrastructure/persistence/atlas_deploy_oci_seal.py'
    content=code.read_text()
    for forbidden in ('subprocess','docker compose','docker pull','os.system','requests.post','ssh '):
        assert forbidden not in content
