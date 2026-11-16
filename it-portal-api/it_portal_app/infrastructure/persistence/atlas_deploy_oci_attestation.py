"""P2.2h.2g: backend-only, read-only GitHub-signed OCI provenance reader.

This is NOT an HTTP endpoint, PREPARE authorizer, OCI configuration-ID proof,
host witness, approval or ACT executor. Verification uses the real GitHub CLI
with pinned repository, workflow, source and immutable OCI digest; never use
unverified UI/MCP attestation JSON as a trusted input.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .atlas_deploy_oci_seal import IMAGE, REPOSITORY, SOURCE_REF, WORKFLOW

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_VERSION = re.compile(r"^gh version (\d+)\.(\d+)\.(\d+)(?:\s|$)")
_PREDICATE = "https://slsa.dev/provenance/v1"
_ISSUER = "https://token.actions.githubusercontent.com"
_MIN_GH_VERSION = (2, 97, 0)
_MAX_JSON = 128_000
_MAX_STATEMENT = 64_000
# Fixed executable search path. No caller-controlled path, subcommand or URL.
_ENV_PATH = "/usr/local/bin:/usr/bin:/bin"


class OCIAttestationReadError(Exception):
    """Finite, non-sensitive failure codes only."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class VerifiedOCIStatement:
    """Actual statement bytes verified by gh, not image config or deploy proof."""

    repository: str
    image: str
    workflow: str
    source_ref: str
    commit_sha: str
    manifest_digest: str
    statement_sha256: str
    verified_at: datetime


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON field")
        result[name] = value
    return result


def _json(raw: str | bytes) -> object:
    return json.loads(
        raw, object_pairs_hook=_unique_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
    )


def _verified_statement(raw: str, expected_digest: str) -> str:
    try:
        result = _json(raw)
        if type(result) is not list or len(result) != 1 or type(result[0]) is not dict:
            raise ValueError("ambiguous or empty verification result")
        entry = result[0]
        verification = entry.get("verificationResult")
        attestation = entry.get("attestation")
        if type(verification) is not dict or type(attestation) is not dict:
            raise ValueError("missing verified attestation")
        signature = verification.get("signature")
        timestamps = verification.get("verifiedTimestamps")
        if (type(signature) is not dict or type(signature.get("certificate")) is not dict
                or type(timestamps) is not list or not timestamps):
            raise ValueError("missing certificate or verified timestamp")
        bundle = attestation.get("bundle", attestation)
        envelope = bundle.get("dsseEnvelope") if type(bundle) is dict else None
        if (type(envelope) is not dict
                or envelope.get("payloadType") != "application/vnd.in-toto+json"):
            raise ValueError("missing signed DSSE statement")
        encoded = envelope.get("payload")
        if type(encoded) is not str or not encoded or len(encoded) > _MAX_STATEMENT * 2:
            raise ValueError("invalid signed statement")
        statement_bytes = base64.b64decode(encoded, validate=True)
        if not statement_bytes or len(statement_bytes) > _MAX_STATEMENT:
            raise ValueError("invalid signed statement length")
        statement = _json(statement_bytes)
        if type(statement) is not dict or statement != verification.get("statement"):
            raise ValueError("verified/DSSE statement drift")
        if (statement.get("_type") != "https://in-toto.io/Statement/v1"
                or statement.get("predicateType") != _PREDICATE):
            raise ValueError("unexpected predicate")
        subjects = statement.get("subject")
        if type(subjects) is not list or len(subjects) != 1 or type(subjects[0]) is not dict:
            raise ValueError("ambiguous subject")
        subject = subjects[0]
        digest = subject.get("digest")
        if (subject.get("name") != IMAGE or type(digest) is not dict
                or digest.get("sha256") != expected_digest.removeprefix("sha256:")):
            raise OCIAttestationReadError("OCI_ATTESTATION_SUBJECT_DRIFT")
        return hashlib.sha256(statement_bytes).hexdigest()
    except OCIAttestationReadError:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, binascii.Error):
        raise OCIAttestationReadError("OCI_ATTESTATION_OUTPUT_INVALID") from None


class GitHubOCIProvenanceReader:
    """Execute a pinned, patched gh attestation verifier, never shell commands.

    The optional process runner is only a trusted test dependency. It must not
    be wired from HTTP, MCP or user parameters. Credentials come from backend
    secrets; the CLI output is consumed only after exit status zero.
    """

    def __init__(
        self, *, github_token: str,
        run_command: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        if (type(github_token) is not str or not 20 <= len(github_token) <= 4096
                or github_token.strip() != github_token
                or github_token.startswith("Bearer ")
                or any(char in github_token for char in ("\n", "\r", "\x00"))):
            raise OCIAttestationReadError("OCI_ATTESTATION_CREDENTIAL_INVALID")
        self._token = github_token
        self._runner = run_command
        self._clock = clock

    def _execute(self, argv: list[str], *, timeout: int) -> str:
        # No environment inheritance: prevent user-selected GH_HOST, GH_CONFIG_DIR,
        # PATH and other GH_* settings from relaxing origin or trust policy.
        environment = {
            "PATH": _ENV_PATH, "GH_HOST": "github.com", "GH_TOKEN": self._token,
            "GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1", "NO_COLOR": "1",
        }
        try:
            completed = self._runner(
                argv, env=environment, capture_output=True, text=True,
                check=False, timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError):
            raise OCIAttestationReadError("OCI_ATTESTATION_VERIFIER_UNAVAILABLE") from None
        if (type(completed.returncode) is not int or completed.returncode != 0
                or type(completed.stdout) is not str):
            # Never surface upstream stdout/stderr: they may contain credentials.
            raise OCIAttestationReadError("OCI_ATTESTATION_VERIFY_FAILED")
        if len(completed.stdout.encode("utf-8")) > _MAX_JSON:
            raise OCIAttestationReadError("OCI_ATTESTATION_OUTPUT_TOO_LARGE")
        return completed.stdout

    def read(self, *, manifest_digest: str, commit_sha: str) -> VerifiedOCIStatement:
        if type(manifest_digest) is not str or _DIGEST.fullmatch(manifest_digest) is None:
            raise OCIAttestationReadError("OCI_MANIFEST_DIGEST_INVALID")
        if type(commit_sha) is not str or _SHA.fullmatch(commit_sha) is None:
            raise OCIAttestationReadError("OCI_COMMIT_SHA_INVALID")
        now = self._clock()
        if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
            raise OCIAttestationReadError("OCI_ATTESTATION_CLOCK_INVALID")
        version_output = self._execute(["gh", "version"], timeout=5)
        match = _VERSION.match(version_output)
        if not match or tuple(int(x) for x in match.groups()) < _MIN_GH_VERSION:
            raise OCIAttestationReadError("OCI_ATTESTATION_VERIFIER_OUTDATED")
        # CLI 2.97.0+ fixes unsafe identity pattern handling in attestation
        # verification. Verified CLI claims remain bound to fixed owner/workflow.
        argv = [
            "gh", "attestation", "verify", f"oci://{IMAGE}@{manifest_digest}",
            "--repo", REPOSITORY,
            "--signer-workflow", WORKFLOW,
            "--source-ref", SOURCE_REF,
            "--source-digest", commit_sha,
            "--predicate-type", _PREDICATE,
            "--cert-oidc-issuer", _ISSUER,
            "--deny-self-hosted-runners",
            "--limit", "1",
            "--format", "json",
        ]
        raw = self._execute(argv, timeout=25)
        statement_sha256 = _verified_statement(raw, manifest_digest)
        return VerifiedOCIStatement(
            repository=REPOSITORY, image=IMAGE, workflow=WORKFLOW,
            source_ref=SOURCE_REF, commit_sha=commit_sha,
            manifest_digest=manifest_digest, statement_sha256=statement_sha256,
            verified_at=now.astimezone(timezone.utc),
        )
