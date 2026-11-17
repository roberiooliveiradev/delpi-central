"""Read-only ATLAS HML pre-activation evidence bundle, NEVER a deploy gate.

An operator may run this once with the existing atlas-hml identity. It reads
only local OS posture, bounded Git HEAD metadata and UNIX socket *metadata*.
It NEVER opens or connects to a Docker socket, runs Git, starts a process,
creates credentials, persists an approval or asserts independent attestation.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .atlas_hml_collector_isolation import (
    CollectorPostureFacts,
    observe_current_process,
    review_facts,
)
from .atlas_hml_git_head_peek import GitHeadMetadataPeek, UntrustedGitHead
from .atlas_hml_uds_policy import HMLUDSPolicyError, verify_socket_metadata

_UNSAFE_TO_READ = (
    "named_account_matches_process",
    "primary_group_exclusive",
    "privileged_groups_absent",
    "checkout_write_denied",
    "raw_socket_write_denied",
    "capabilities_zero",
    "permitted_capabilities_zero",
    "ambient_capabilities_zero",
)
_PROXY_STATES = frozenset({
    "skipped_unsafe_account",
    "unavailable",
    "metadata_only_untrusted",
    "unsafe_or_unverifiable",
})
_ALWAYS_BLOCKS = (
    "HOST_OS_IDENTITY_NOT_INDEPENDENTLY_ATTESTED",
    "HML_UPSTREAM_PROCESS_NOT_INDEPENDENTLY_ATTESTED",
    "HML_PROXY_POLICY_NOT_INDEPENDENTLY_ATTESTED",
    "COLLECTOR_TRANSPORT_NOT_ATTESTED",
    "GIT_FILESYSTEM_SNAPSHOT_NOT_ATOMIC",
    "GIT_IGNORED_FILES_NOT_MEASURED",
    "JOURNAL_CHALLENGE_NOT_CONSUMED",
    "BACKUP_RESTORE_AND_ROLLBACK_NOT_ATTESTED",
    "CORE_PREPARE_NOT_AUTHORIZED",
    "INDEPENDENT_SECURITY_REVIEW_REQUIRED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")


class HMLReviewBundleError(Exception):
    """Always finite and free from filesystem, account and token details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLReadOnlyReviewBundle:
    status: str
    environment: str
    service_id: str
    observed_at: str
    checks: CollectorPostureFacts
    git_head_metadata_only_untrusted: str | None
    git_branch: str | None
    git_clean_status_observed: bool
    proxy_socket_metadata: str
    blocks: tuple[str, ...]
    host_identity_attested: bool = False
    collector_transport_attested: bool = False
    proxy_policy_independently_attested: bool = False
    checkout_integrity_attested: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def safe_to_read_metadata(facts: CollectorPostureFacts) -> bool:
    """Only decide if even *diagnostic metadata* should be observed."""
    review_facts(facts)
    return all(getattr(facts, key) is True for key in _UNSAFE_TO_READ)


def assemble_bundle(
    *,
    facts: CollectorPostureFacts,
    git: UntrustedGitHead | None,
    proxy_state: str,
    now: datetime,
) -> HMLReadOnlyReviewBundle:
    """Compose only known local observations; never authorize anything."""
    review = review_facts(facts)
    if (
        type(proxy_state) is not str or proxy_state not in _PROXY_STATES
        or type(now) is not datetime
        or now.tzinfo is None or now.utcoffset() is None
    ):
        raise HMLReviewBundleError("HML_REVIEW_INPUT_INVALID")
    safe = safe_to_read_metadata(facts)
    if not safe:
        # No caller may invent a valid observation for a privileged account.
        if proxy_state != "skipped_unsafe_account" or git is not None:
            raise HMLReviewBundleError("HML_REVIEW_UNSAFE_EVIDENCE")
    elif proxy_state == "skipped_unsafe_account":
        raise HMLReviewBundleError("HML_REVIEW_INPUT_INVALID")

    head: str | None = None
    branch: str | None = None
    blocks = list((*review.blocks, *_ALWAYS_BLOCKS))
    if git is not None:
        if (
            type(git) is not UntrustedGitHead
            or git.source != "filesystem_head_only_untrusted"
            or git.branch != "main"
            or type(git.head_sha) is not str
            or _SHA40.fullmatch(git.head_sha) is None
            or git.checkout_attested is not False
            or git.clean_status_observed is not False
            or git.challenge_bound is not False
            or git.prepare_eligible is not False
            or git.can_execute is not False
        ):
            raise HMLReviewBundleError("HML_REVIEW_GIT_CONTRACT_INVALID")
        head = git.head_sha
        branch = git.branch
        blocks.extend((
            "HML_GIT_METADATA_ONLY_UNTRUSTED",
            "HML_GIT_STATUS_NOT_CHECKED",
        ))
    else:
        blocks.append("HML_GIT_METADATA_UNAVAILABLE")

    if proxy_state == "metadata_only_untrusted":
        blocks.append("HML_PROXY_METADATA_ONLY_NOT_ATTESTED")
    elif proxy_state == "unavailable":
        blocks.append("HML_PROXY_UNAVAILABLE")
    elif proxy_state == "unsafe_or_unverifiable":
        blocks.append("HML_PROXY_METADATA_UNSAFE_OR_UNVERIFIABLE")
    else:
        blocks.append("HML_HOST_METADATA_SKIPPED_UNSAFE_ACCOUNT")

    return HMLReadOnlyReviewBundle(
        status="blocked",
        environment="hml",
        service_id="public-hub",
        observed_at=now.astimezone(timezone.utc).isoformat(),
        checks=facts,
        git_head_metadata_only_untrusted=head,
        git_branch=branch,
        git_clean_status_observed=False,
        proxy_socket_metadata=proxy_state,
        blocks=tuple(dict.fromkeys(blocks)),
    )


def collect_local_bundle() -> HMLReadOnlyReviewBundle:
    """A fixed-path, one-shot observation. No socket connect or Docker GET."""
    facts = observe_current_process()
    git: UntrustedGitHead | None = None
    if not safe_to_read_metadata(facts):
        state = "skipped_unsafe_account"
    else:
        try:
            git = GitHeadMetadataPeek().read()
        except Exception:
            # Filesystem errors are untrusted. Never reflect their details.
            git = None
        try:
            verify_socket_metadata()
            state = "metadata_only_untrusted"
        except HMLUDSPolicyError as exc:
            state = (
                "unavailable" if exc.code == "HML_PROXY_UNAVAILABLE"
                else "unsafe_or_unverifiable"
            )
        except Exception:
            state = "unsafe_or_unverifiable"
    return assemble_bundle(
        facts=facts, git=git, proxy_state=state,
        now=datetime.now(timezone.utc),
    )


def main() -> int:
    """Exit 0 means a blocked diagnostic was printed, NEVER readiness."""
    try:
        result = collect_local_bundle()
        print(json.dumps(
            asdict(result), sort_keys=True, separators=(",", ":"),
        ))
        return 0
    except Exception:
        print(json.dumps({
            "status": "blocked",
            "code": "HML_REVIEW_BUNDLE_UNAVAILABLE",
            "prepare_eligible": False,
            "can_execute": False,
        }, sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
