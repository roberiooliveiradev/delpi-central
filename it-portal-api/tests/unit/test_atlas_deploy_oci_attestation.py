"""P2.2h.2g: fully offline GitHub CLI trust adapter tests, no live OCI/API."""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_oci_attestation import (
    GitHubOCIProvenanceReader, OCIAttestationReadError,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_seal import (
    IMAGE, REPOSITORY, SOURCE_REF, WORKFLOW,
)

NOW = datetime(2026, 11, 16, 18, 30, tzinfo=timezone.utc)
DIGEST = "sha256:" + "a" * 64
COMMIT = "b" * 40
TOKEN = "synthetic-ci-token-never-real-12345"


def statement():
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": IMAGE, "digest": {"sha256": DIGEST[7:]}}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {"buildDefinition": {"buildType": "https://example.test/trusted"}},
    }


def signed_result(raw_statement=None, *, verified_statement=None):
    original = raw_statement if raw_statement is not None else statement()
    data = json.dumps(original, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return [{
        "attestation": {
            "bundle": {"dsseEnvelope": {
                "payload": base64.b64encode(data).decode("ascii"),
                "payloadType": "application/vnd.in-toto+json",
            }},
        },
        "verificationResult": {
            "signature": {"certificate": {"subject": "trusted-cli-verification"}},
            "verifiedTimestamps": [{"source": "transparency-log"}],
            "statement": verified_statement if verified_statement is not None else original,
        },
    }]


class FakeGh:
    def __init__(self, *, attestation=None, version="gh version 2.98.1 (synthetic)",
                 verify_code=0, verifier_raises=None):
        self.result = signed_result() if attestation is None else attestation
        self.version = version
        self.verify_code = verify_code
        self.verifier_raises = verifier_raises
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), kwargs))
        if self.verifier_raises is not None:
            raise self.verifier_raises
        if argv == ["gh", "version"]:
            return subprocess.CompletedProcess(argv, 0, self.version, "")
        return subprocess.CompletedProcess(
            argv, self.verify_code, json.dumps(self.result), "secret-token-should-not-leak",
        )


def reader(fake=None, *, clock=lambda: NOW):
    gh = fake or FakeGh()
    return GitHubOCIProvenanceReader(
        github_token=TOKEN, run_command=gh, clock=clock,
    ), gh


def reject(code, fake=None, *, digest=DIGEST, commit=COMMIT):
    instance, gh = reader(fake)
    with pytest.raises(OCIAttestationReadError) as exc:
        instance.read(manifest_digest=digest, commit_sha=commit)
    assert exc.value.code == code
    assert TOKEN not in str(exc.value)
    return gh


def test_signed_provenance_is_exact_and_bound_to_immutable_oci_subject():
    instance, fake = reader()
    result = instance.read(manifest_digest=DIGEST, commit_sha=COMMIT)
    statement_bytes = json.dumps(statement(), separators=(",", ":"), sort_keys=True).encode("utf-8")
    assert result.statement_sha256 == hashlib.sha256(statement_bytes).hexdigest()
    assert result.verified_at == NOW
    assert (result.manifest_digest, result.commit_sha) == (DIGEST, COMMIT)
    assert (result.repository, result.image, result.workflow, result.source_ref) == (
        REPOSITORY, IMAGE, WORKFLOW, SOURCE_REF,
    )
    assert not hasattr(result, "image_config_id")
    assert not hasattr(result, "rollback_ready")
    assert len(fake.calls) == 2
    first, opts = fake.calls[0]
    assert first == ["gh", "version"]
    assert opts["timeout"] == 5
    args, opts = fake.calls[1]
    assert args[:3] == ["gh", "attestation", "verify"]
    assert args[3] == f"oci://{IMAGE}@{DIGEST}"
    for flag, value in (
        ("--repo", REPOSITORY), ("--signer-workflow", WORKFLOW),
        ("--source-ref", SOURCE_REF), ("--source-digest", COMMIT),
        ("--predicate-type", "https://slsa.dev/provenance/v1"),
        ("--cert-oidc-issuer", "https://token.actions.githubusercontent.com"),
        ("--limit", "1"), ("--format", "json"),
    ):
        assert args[args.index(flag) + 1] == value
    assert "--deny-self-hosted-runners" in args
    assert "--bundle" not in args and "--bundle-from-oci" not in args
    assert "--owner" not in args
    assert opts["timeout"] == 25
    assert opts["check"] is False and opts["capture_output"] is True
    assert opts["text"] is True and "shell" not in opts
    assert opts["env"]["GH_HOST"] == "github.com"
    assert opts["env"]["GH_TOKEN"] == TOKEN
    assert "GH_CONFIG_DIR" not in opts["env"]


@pytest.mark.parametrize("digest,commit,code", [
    ("sha256:bad", COMMIT, "OCI_MANIFEST_DIGEST_INVALID"),
    ("sha256:" + "A" * 64, COMMIT, "OCI_MANIFEST_DIGEST_INVALID"),
    ("sha256:" + "a" * 63, COMMIT, "OCI_MANIFEST_DIGEST_INVALID"),
    (DIGEST + ";sh -c true", COMMIT, "OCI_MANIFEST_DIGEST_INVALID"),
    (None, COMMIT, "OCI_MANIFEST_DIGEST_INVALID"),
    (DIGEST, "main", "OCI_COMMIT_SHA_INVALID"),
    (DIGEST, "../bad", "OCI_COMMIT_SHA_INVALID"),
    (DIGEST, "B" * 40, "OCI_COMMIT_SHA_INVALID"),
    (DIGEST, None, "OCI_COMMIT_SHA_INVALID"),
])
def test_invalid_input_never_reaches_process(digest, commit, code):
    gh = reject(code, digest=digest, commit=commit)
    assert gh.calls == []


@pytest.mark.parametrize("token", ["", "short", "Bearer " + "x" * 20, "x" * 12 + "\n" + "x" * 12, None])
def test_credentials_cannot_be_empty_unsafe_or_from_header(token):
    with pytest.raises(OCIAttestationReadError, match="OCI_ATTESTATION_CREDENTIAL_INVALID"):
        GitHubOCIProvenanceReader(github_token=token, run_command=FakeGh())


@pytest.mark.parametrize("version", ["gh version 2.96.9", "gh version 2.0.0", "GH unknown", "gh version 2.96.99"])
def test_vulnerable_or_unknown_verifier_version_denied_before_signature_call(version):
    gh = reject("OCI_ATTESTATION_VERIFIER_OUTDATED", FakeGh(version=version))
    assert len(gh.calls) == 1


@pytest.mark.parametrize("clock", [lambda: NOW.replace(tzinfo=None), lambda: "today"])
def test_bad_clock_denied_before_cli(clock):
    instance, gh = reader(clock=clock)
    with pytest.raises(OCIAttestationReadError, match="OCI_ATTESTATION_CLOCK_INVALID"):
        instance.read(manifest_digest=DIGEST, commit_sha=COMMIT)
    assert gh.calls == []


def test_cli_failure_does_not_report_raw_secret():
    gh = reject("OCI_ATTESTATION_VERIFY_FAILED", FakeGh(verify_code=1))
    assert len(gh.calls) == 2
    assert TOKEN not in str(gh.calls[-1][0])


@pytest.mark.parametrize("exc", [
    FileNotFoundError("token=synthetic-ci-token-never-real-12345"),
    subprocess.TimeoutExpired(["gh", "attestation"], 25),
    subprocess.SubprocessError("private backend output"),
])
def test_cli_missing_timeout_or_subprocess_error_is_fail_closed(exc):
    reject("OCI_ATTESTATION_VERIFIER_UNAVAILABLE", FakeGh(verifier_raises=exc))


def test_wrong_signed_subject_image_and_digest_rejected():
    for value in [
        {"name": "ghcr.io/other/image", "digest": {"sha256": DIGEST[7:]}},
        {"name": IMAGE, "digest": {"sha256": "c" * 64}},
    ]:
        s = statement()
        s["subject"] = [value]
        reject("OCI_ATTESTATION_SUBJECT_DRIFT", FakeGh(attestation=signed_result(s)))


def test_valid_cli_exit_does_not_override_signed_statement_validation():
    for change in [
        lambda s: s.update(predicateType="https://in-toto.io/attestation/release/v0.1"),
        lambda s: s.update(_type="invalid"),
        lambda s: s.update(subject=[]),
        lambda s: s.update(subject=[*s["subject"], *s["subject"]]),
    ]:
        s = statement()
        change(s)
        reject("OCI_ATTESTATION_OUTPUT_INVALID", FakeGh(attestation=signed_result(s)))


def test_verified_output_and_signed_dsse_must_have_identical_claims():
    mismatched = deepcopy(statement())
    mismatched["predicate"]["buildDefinition"]["buildType"] = "tampered"
    reject(
        "OCI_ATTESTATION_OUTPUT_INVALID",
        FakeGh(attestation=signed_result(verified_statement=mismatched)),
    )


def test_missing_certificate_timestamp_envelope_or_verification_rejected():
    cases = []
    proof = signed_result()
    for mutate in [
        lambda x: x[0]["verificationResult"]["signature"].pop("certificate"),
        lambda x: x[0]["verificationResult"].update(verifiedTimestamps=[]),
        lambda x: x[0]["attestation"]["bundle"].pop("dsseEnvelope"),
        lambda x: x[0].pop("verificationResult"),
        lambda x: x[0]["attestation"]["bundle"]["dsseEnvelope"].update(payload="not-base64!"),
        lambda x: x[0]["attestation"]["bundle"]["dsseEnvelope"].update(payloadType="wrong"),
    ]:
        p = deepcopy(proof)
        mutate(p)
        cases.append(p)
    for payload in cases:
        reject("OCI_ATTESTATION_OUTPUT_INVALID", FakeGh(attestation=payload))


def test_ambiguous_multiple_or_empty_attestations_are_rejected():
    for data in ([], signed_result() + signed_result(), {}, [None]):
        reject("OCI_ATTESTATION_OUTPUT_INVALID", FakeGh(attestation=data))


def test_duplicate_fields_and_nonfinite_json_are_rejected():
    # Parse the untrusted GH JSON output, not synthetic objects passed in memory.
    from it_portal_app.infrastructure.persistence.atlas_deploy_oci_attestation import _verified_statement
    for text in ('[{"a":1,"a":2}]', "[NaN]", "not-json"):
        with pytest.raises(OCIAttestationReadError, match="OCI_ATTESTATION_OUTPUT_INVALID"):
            _verified_statement(text, DIGEST)


def test_oversize_cli_output_denied():
    class Huge(FakeGh):
        def __call__(self, argv, **kw):
            if argv == ["gh", "version"]:
                return super().__call__(argv, **kw)
            return subprocess.CompletedProcess(argv, 0, "[" + " " * 130_000 + "]", "")
    reject("OCI_ATTESTATION_OUTPUT_TOO_LARGE", Huge())


def test_real_execution_is_not_synthesized_from_a_dataclass():
    # There is no PREPARE or ACT entrypoint, and no release ImageID is asserted.
    instance, _ = reader()
    result = instance.read(manifest_digest=DIGEST, commit_sha=COMMIT)
    assert not hasattr(instance, "store") and not hasattr(instance, "execute")
    assert not hasattr(result, "signature_verified")
