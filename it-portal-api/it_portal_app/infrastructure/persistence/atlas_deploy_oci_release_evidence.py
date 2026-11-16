"""ATLAS P2.2h.2i: compose two *independent* read-only OCI evidence readers.

Inert private backend module. No route, tool, DB write, approval, PREPARE or ACT.
Only the backend may construct this adapter with the real pinned GitHub and
GHCR readers. Never accept VerifiedOCIStatement/OCIImageIdentity objects (or
the readers themselves) from an HTTP/MCP request: dataclasses do not attest
to their origin or prove an actual cryptographic signature.
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Callable

from .atlas_deploy_oci_attestation import (
    GitHubOCIProvenanceReader,
    VerifiedOCIStatement,
)
from .atlas_deploy_oci_registry import GHCRImageIdentityReader, OCIImageIdentity
from .atlas_deploy_oci_seal import (
    CIReleaseEvidence,
    IMAGE,
    REPOSITORY,
    SOURCE_REF,
    WORKFLOW,
)

_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_EVIDENCE_AGE = timedelta(seconds=120)
_CLOCK_SKEW = timedelta(seconds=5)


class OCIReleaseEvidenceError(Exception):
    """Public-safe codes only; never include source responses, tokens or URLs."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _aware(value: object) -> bool:
    return (
        type(value) is datetime
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _fresh(value: datetime, now: datetime) -> bool:
    delta = now.astimezone(timezone.utc) - value.astimezone(timezone.utc)
    return -_CLOCK_SKEW <= delta <= _MAX_EVIDENCE_AGE


class OCIReleaseEvidenceReader:
    """Build CIReleaseEvidence only from live, independently checked sources.

    The constructor takes server-owned reader instances. Injecting fake
    readers is exclusively for hermetic tests, not an HTTP/MCP API contract.
    A successful return is *only release/CI evidence*, never permission to
    create a proposal, approve it or execute a deployment.
    """

    def __init__(
        self, *,
        provenance_reader: GitHubOCIProvenanceReader,
        registry_reader: GHCRImageIdentityReader,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._provenance = provenance_reader
        self._registry = registry_reader
        self._clock = clock

    async def read(
        self, *, manifest_digest: str, commit_sha: str,
    ) -> CIReleaseEvidence:
        # Never reach a CLI/registry with a tag, URL, partial SHA or invalid
        # digest. Callers choose a target but cannot choose trust authorities.
        if (
            type(manifest_digest) is not str
            or _DIGEST.fullmatch(manifest_digest) is None
            or type(commit_sha) is not str
            or _COMMIT.fullmatch(commit_sha) is None
        ):
            raise OCIReleaseEvidenceError("OCI_RELEASE_TARGET_INVALID")

        # The pinned GitHub CLI verifier uses a blocking subprocess. Offload
        # it to a worker thread; never run a shell command on the API loop.
        # Exception text from a vendor or injected process must never leak.
        try:
            signed = await asyncio.to_thread(
                self._provenance.read,
                manifest_digest=manifest_digest,
                commit_sha=commit_sha,
            )
        except Exception:
            raise OCIReleaseEvidenceError("OCI_RELEASE_ATTESTATION_UNAVAILABLE") from None

        if type(signed) is not VerifiedOCIStatement:
            raise OCIReleaseEvidenceError("OCI_RELEASE_ATTESTATION_INVALID")
        if (
            signed.repository != REPOSITORY
            or signed.image != IMAGE
            or signed.workflow != WORKFLOW
            or signed.source_ref != SOURCE_REF
            or signed.commit_sha != commit_sha
            or signed.manifest_digest != manifest_digest
        ):
            raise OCIReleaseEvidenceError("OCI_RELEASE_ATTESTATION_DRIFT")
        if (
            type(signed.statement_sha256) is not str
            or _HEX64.fullmatch(signed.statement_sha256) is None
            or not _aware(signed.verified_at)
        ):
            raise OCIReleaseEvidenceError("OCI_RELEASE_ATTESTATION_INVALID")

        # Invoke the separate GHCR hash-verifying reader only after the
        # signed statement agrees with the requested immutable OCI identity.
        try:
            registry = await self._registry.read(manifest_digest=manifest_digest)
        except Exception:
            raise OCIReleaseEvidenceError("OCI_RELEASE_REGISTRY_UNAVAILABLE") from None

        if type(registry) is not OCIImageIdentity:
            raise OCIReleaseEvidenceError("OCI_RELEASE_REGISTRY_INVALID")
        if (
            registry.image != IMAGE
            or registry.manifest_digest != manifest_digest
        ):
            raise OCIReleaseEvidenceError("OCI_RELEASE_REGISTRY_DRIFT")
        if (
            type(registry.image_manifest_digest) is not str
            or _DIGEST.fullmatch(registry.image_manifest_digest) is None
            or type(registry.image_config_id) is not str
            or _DIGEST.fullmatch(registry.image_config_id) is None
            or not _aware(registry.read_at)
        ):
            raise OCIReleaseEvidenceError("OCI_RELEASE_REGISTRY_INVALID")
        if registry.platform != "linux/amd64":
            # Direct manifests have platform='unverified'. They are usable
            # for inspection but not as release authority until verified.
            raise OCIReleaseEvidenceError("OCI_RELEASE_PLATFORM_UNVERIFIED")

        now = self._clock()
        if not _aware(now):
            raise OCIReleaseEvidenceError("OCI_RELEASE_CLOCK_INVALID")
        if not (
            _fresh(signed.verified_at, now)
            and _fresh(registry.read_at, now)
        ):
            raise OCIReleaseEvidenceError("OCI_RELEASE_EVIDENCE_STALE")
        if registry.read_at < signed.verified_at - _CLOCK_SKEW:
            raise OCIReleaseEvidenceError("OCI_RELEASE_EVIDENCE_ORDER_INVALID")

        # Use the EARLIEST verification timestamp so downstream freshness
        # checks cannot mistake a fresh registry read for a fresh signature.
        verified_at = min(signed.verified_at, registry.read_at)
        return CIReleaseEvidence(
            repository=REPOSITORY,
            image=IMAGE,
            workflow=WORKFLOW,
            source_ref=SOURCE_REF,
            commit_sha=commit_sha,
            manifest_digest=manifest_digest,
            image_config_id=registry.image_config_id,
            statement_sha256=signed.statement_sha256,
            verified_at=verified_at,
            signature_verified=True,
        )
