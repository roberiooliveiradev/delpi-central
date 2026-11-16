"""ATLAS P2.2h.2i: hermetic two-source OCI release evidence composition.

No network, registry credentials, production DB, Docker, approval or ACT.
The real reader integration uses mocked process/HTTP boundaries only.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import subprocess
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_oci_attestation import (
    GitHubOCIProvenanceReader, VerifiedOCIStatement,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_registry import (
    GHCRImageIdentityReader, OCIImageIdentity,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_release_evidence import (
    OCIReleaseEvidenceError, OCIReleaseEvidenceReader,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_seal import (
    CIReleaseEvidence, IMAGE, REPOSITORY, SOURCE_REF, WORKFLOW,
)

NOW = datetime(2026, 11, 16, 20, 0, tzinfo=timezone.utc)
SHA = "b" * 40
MANIFEST = "sha256:" + "a" * 64
CHILD = "sha256:" + "c" * 64
CONFIG = "sha256:" + "d" * 64
STATEMENT = "e" * 64


def signed(**changes):
    return replace(
        VerifiedOCIStatement(
            repository=REPOSITORY, image=IMAGE, workflow=WORKFLOW,
            source_ref=SOURCE_REF, commit_sha=SHA, manifest_digest=MANIFEST,
            statement_sha256=STATEMENT,
            verified_at=NOW - timedelta(seconds=25),
        ),
        **changes,
    )


def registry(**changes):
    return replace(
        OCIImageIdentity(
            image=IMAGE, manifest_digest=MANIFEST,
            image_manifest_digest=CHILD,
            image_config_id=CONFIG, platform="linux/amd64",
            read_at=NOW - timedelta(seconds=5),
        ),
        **changes,
    )


class FakeProvenance:
    def __init__(self, result=None, exception=None):
        self.result = signed() if result is None else result
        self.exception = exception
        self.calls = []

    def read(self, *, manifest_digest, commit_sha):
        self.calls.append((manifest_digest, commit_sha))
        if self.exception:
            raise self.exception
        return self.result


class FakeRegistry:
    def __init__(self, result=None, exception=None):
        self.result = registry() if result is None else result
        self.exception = exception
        self.calls = []

    async def read(self, *, manifest_digest):
        self.calls.append(manifest_digest)
        if self.exception:
            raise self.exception
        return self.result


def run(proof=None, image=None, *, digest=MANIFEST, sha=SHA, clock=lambda: NOW):
    a = proof or FakeProvenance()
    b = image or FakeRegistry()
    reader = OCIReleaseEvidenceReader(
        provenance_reader=a, registry_reader=b, clock=clock,
    )
    result = asyncio.run(reader.read(manifest_digest=digest, commit_sha=sha))
    return result, a, b


def expect_error(code, proof=None, image=None, **kwargs):
    a = proof or FakeProvenance()
    b = image or FakeRegistry()
    with pytest.raises(OCIReleaseEvidenceError) as err:
        run(a, b, **kwargs)
    assert err.value.code == code
    assert "secret" not in str(err.value)
    return a, b


def test_two_independent_sources_produce_candidate_only_ci_release_evidence():
    result, attestor, ghcr = run()
    assert type(result) is CIReleaseEvidence
    assert result.signature_verified is True
    assert (result.repository, result.image, result.workflow, result.source_ref) == (
        REPOSITORY, IMAGE, WORKFLOW, SOURCE_REF,
    )
    assert (result.commit_sha, result.manifest_digest) == (SHA, MANIFEST)
    assert result.image_config_id == CONFIG
    assert result.statement_sha256 == STATEMENT
    assert result.verified_at == NOW - timedelta(seconds=25)
    assert attestor.calls == [(MANIFEST, SHA)]
    assert ghcr.calls == [MANIFEST]
    assert not hasattr(result, "can_execute")
    assert not hasattr(result, "rollback_ready")


@pytest.mark.parametrize("digest,sha", [
    ("latest", SHA),
    ("sha256:bad", SHA),
    ("sha256:" + "A" * 64, SHA),
    ("sha256:" + "a" * 64 + ";curl", SHA),
    (None, SHA),
    (MANIFEST, "main"),
    (MANIFEST, "B" * 40),
    (MANIFEST, "../etc/passwd"),
    (MANIFEST, None),
])
def test_invalid_target_denied_before_verifier_or_registry(digest, sha):
    a, b = expect_error("OCI_RELEASE_TARGET_INVALID", digest=digest, sha=sha)
    assert not a.calls and not b.calls


@pytest.mark.parametrize("field,value", [
    ("repository", "another-owner/repo"),
    ("image", "ghcr.io/another/image"),
    ("workflow", "another-workflow"),
    ("source_ref", "refs/heads/feature"),
    ("commit_sha", "f" * 40),
    ("manifest_digest", "sha256:" + "f" * 64),
])
def test_attestation_identity_drift_never_contacts_registry(field, value):
    a, b = expect_error(
        "OCI_RELEASE_ATTESTATION_DRIFT",
        FakeProvenance(signed(**{field: value})),
    )
    assert len(a.calls) == 1 and b.calls == []


@pytest.mark.parametrize("field,value", [
    ("statement_sha256", "bad"),
    ("statement_sha256", "F" * 64),
    ("statement_sha256", None),
    ("verified_at", NOW.replace(tzinfo=None)),
    ("verified_at", "recent"),
])
def test_attestation_shape_invalid_never_contacts_registry(field, value):
    a, b = expect_error(
        "OCI_RELEASE_ATTESTATION_INVALID",
        FakeProvenance(signed(**{field: value})),
    )
    assert a.calls and not b.calls


def test_fake_untyped_provenance_result_never_reaches_registry():
    a, b = expect_error(
        "OCI_RELEASE_ATTESTATION_INVALID",
        FakeProvenance(result={"commit_sha": SHA}),
    )
    assert len(a.calls) == 1 and b.calls == []


def test_upstream_attestor_exception_is_sanitized_and_registry_not_called():
    a, b = expect_error(
        "OCI_RELEASE_ATTESTATION_UNAVAILABLE",
        FakeProvenance(exception=RuntimeError("secret=unsafe-backend-token")),
    )
    assert len(a.calls) == 1 and b.calls == []


@pytest.mark.parametrize("field,value,code", [
    ("image", "ghcr.io/attacker/another", "OCI_RELEASE_REGISTRY_DRIFT"),
    ("manifest_digest", "sha256:" + "e" * 64, "OCI_RELEASE_REGISTRY_DRIFT"),
    ("image_manifest_digest", "bad", "OCI_RELEASE_REGISTRY_INVALID"),
    ("image_config_id", "not-a-digest", "OCI_RELEASE_REGISTRY_INVALID"),
    ("image_config_id", "sha256:" + "F" * 64, "OCI_RELEASE_REGISTRY_INVALID"),
    ("read_at", NOW.replace(tzinfo=None), "OCI_RELEASE_REGISTRY_INVALID"),
    ("platform", "unverified", "OCI_RELEASE_PLATFORM_UNVERIFIED"),
    ("platform", "linux/arm64", "OCI_RELEASE_PLATFORM_UNVERIFIED"),
])
def test_registry_drift_and_unverified_platform_denied(field, value, code):
    a, b = expect_error(
        code, FakeProvenance(), FakeRegistry(registry(**{field: value})),
    )
    assert a.calls == [(MANIFEST, SHA)] and b.calls == [MANIFEST]


def test_untyped_registry_result_is_rejected():
    a, b = expect_error(
        "OCI_RELEASE_REGISTRY_INVALID",
        FakeProvenance(), FakeRegistry(result={"image_config_id": CONFIG}),
    )
    assert a.calls and b.calls


def test_registry_unavailable_is_sanitized():
    a, b = expect_error(
        "OCI_RELEASE_REGISTRY_UNAVAILABLE",
        FakeProvenance(),
        FakeRegistry(exception=RuntimeError("secret=upstream-credential")),
    )
    assert a.calls and b.calls


@pytest.mark.parametrize("ts", [
    NOW - timedelta(seconds=121),
    NOW + timedelta(seconds=6),
])
def test_ancient_or_future_attestation_cannot_be_refreshed_by_registry(ts):
    expect_error(
        "OCI_RELEASE_EVIDENCE_STALE",
        FakeProvenance(signed(verified_at=ts)),
        FakeRegistry(registry(read_at=NOW)),
    )


@pytest.mark.parametrize("ts", [
    NOW - timedelta(seconds=121),
    NOW + timedelta(seconds=6),
])
def test_registry_time_outside_freshness_denied(ts):
    expect_error(
        "OCI_RELEASE_EVIDENCE_STALE",
        FakeProvenance(),
        FakeRegistry(registry(read_at=ts)),
    )


def test_registry_timestamp_before_attestation_is_fail_closed():
    expect_error(
        "OCI_RELEASE_EVIDENCE_ORDER_INVALID",
        FakeProvenance(signed(verified_at=NOW)),
        FakeRegistry(registry(read_at=NOW - timedelta(seconds=10))),
    )


def test_utc_normalization_preserves_age_and_earliest_evidence_timestamp():
    utc_minus_3 = timezone(timedelta(hours=-3))
    old = (NOW - timedelta(seconds=35)).astimezone(utc_minus_3)
    recent = (NOW - timedelta(seconds=5)).astimezone(utc_minus_3)
    result, _, _ = run(
        FakeProvenance(signed(verified_at=old)),
        FakeRegistry(registry(read_at=recent)),
    )
    assert result.verified_at == old
    assert result.verified_at.astimezone(timezone.utc) == NOW - timedelta(seconds=35)


@pytest.mark.parametrize("clock_value", [
    NOW.replace(tzinfo=None),
    "server-time-string",
    None,
])
def test_end_clock_not_aware_denied(clock_value):
    expect_error(
        "OCI_RELEASE_CLOCK_INVALID",
        clock=lambda: clock_value,
    )


def test_both_sources_must_be_refreshed_on_every_call_not_cached():
    a, b = FakeProvenance(), FakeRegistry()
    run(a, b)
    run(a, b)
    assert a.calls == [(MANIFEST, SHA), (MANIFEST, SHA)]
    assert b.calls == [MANIFEST, MANIFEST]


def test_real_adapters_work_together_with_hermetic_git_cli_and_registry_io():
    # This checks the real composition, not a real GitHub/Sigstore signature.
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": "https://slsa.dev/provenance/v1",
        "subject": [{"name": IMAGE, "digest": {"sha256": MANIFEST[7:]}}],
        "predicate": {"buildDefinition": {"buildType": "test-only"}},
    }
    statement_bytes = json.dumps(
        statement, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    cli_json = json.dumps([{
        "attestation": {"bundle": {"dsseEnvelope": {
            "payloadType": "application/vnd.in-toto+json",
            "payload": base64.b64encode(statement_bytes).decode("ascii"),
        }}},
        "verificationResult": {
            "signature": {"certificate": {"example": "synthetic"}},
            "verifiedTimestamps": [{"test": True}],
            "statement": statement,
        },
    }])

    cli_calls = []

    def fake_cli(argv, **options):
        cli_calls.append((argv, options))
        if argv == ["gh", "version"]:
            return subprocess.CompletedProcess(argv, 0, "gh version 2.98.1", "")
        return subprocess.CompletedProcess(argv, 0, cli_json, "")

    child_obj = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": CONFIG, "size": 130,
        },
        "layers": [],
    }
    child = json.dumps(
        child_obj, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    child_digest = "sha256:" + hashlib.sha256(child).hexdigest()
    index_obj = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [{
            "mediaType": child_obj["mediaType"],
            "digest": child_digest, "size": len(child),
            "platform": {"os": "linux", "architecture": "amd64"},
        }],
    }
    index = json.dumps(
        index_obj, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    index_digest = "sha256:" + hashlib.sha256(index).hexdigest()

    # This test uses computed hashes, not the constant MANIFEST test fixture.
    signed_statement = dict(statement)
    signed_statement["subject"] = [{
        "name": IMAGE, "digest": {"sha256": index_digest[7:]},
    }]
    signed_bytes = json.dumps(
        signed_statement, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    cli_json = json.dumps([{
        "attestation": {"bundle": {"dsseEnvelope": {
            "payloadType": "application/vnd.in-toto+json",
            "payload": base64.b64encode(signed_bytes).decode("ascii"),
        }}},
        "verificationResult": {
            "signature": {"certificate": {}},
            "verifiedTimestamps": [{"synthetic": True}],
            "statement": signed_statement,
        },
    }])

    http_calls = []

    def fake_http(request):
        http_calls.append(request)
        assert request.method == "GET"
        assert request.url.host == "ghcr.io"
        assert request.url.scheme == "https"
        assert request.headers.get("authorization") is None
        if request.url.path.endswith(index_digest):
            return httpx.Response(
                200,
                content=index,
                headers={
                    "content-type": index_obj["mediaType"],
                    "docker-content-digest": index_digest,
                },
            )
        if request.url.path.endswith(child_digest):
            return httpx.Response(
                200,
                content=child,
                headers={
                    "content-type": child_obj["mediaType"],
                    "docker-content-digest": child_digest,
                },
            )
        raise AssertionError("unexpected registry URL")

    attestor = GitHubOCIProvenanceReader(
        github_token="synthetic-ci-testing-token-only-123456",
        run_command=fake_cli, clock=lambda: NOW - timedelta(seconds=5),
    )
    ghcr = GHCRImageIdentityReader(
        transport=httpx.MockTransport(fake_http),
        clock=lambda: NOW - timedelta(seconds=1),
    )
    outcome = asyncio.run(OCIReleaseEvidenceReader(
        provenance_reader=attestor,
        registry_reader=ghcr,
        clock=lambda: NOW,
    ).read(manifest_digest=index_digest, commit_sha=SHA))
    assert type(outcome) is CIReleaseEvidence
    assert outcome.commit_sha == SHA
    assert outcome.manifest_digest == index_digest
    assert outcome.image_config_id == CONFIG
    assert outcome.statement_sha256 == hashlib.sha256(signed_bytes).hexdigest()
    assert outcome.verified_at == NOW - timedelta(seconds=5)
    assert len(cli_calls) == 2 and len(http_calls) == 2
    assert all(x.method == "GET" for x in http_calls)
    assert not hasattr(outcome, "approval")


def test_module_has_no_route_or_deployment_executor():
    from pathlib import Path

    module = (
        Path(__file__).resolve().parents[2]
        / "it_portal_app/infrastructure/persistence/atlas_deploy_oci_release_evidence.py"
    )
    source = module.read_text()
    for forbidden in ("@router.", "docker run", "docker compose", "subprocess.run", "CREATE TABLE"):
        assert forbidden not in source
