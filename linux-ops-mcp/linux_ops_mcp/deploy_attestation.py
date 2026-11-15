"""P2.2a: backend-only release, host and fresh Core permission attestation.

Pure functions: no GitHub HTTP, database, Docker, shell, or MCP tool wiring.
The trusted backend must obtain these facts independently using fixed providers;
NEVER construct them from model/user arguments, logs, PR descriptions or prompts.
An attestation is NOT an approval, durable journal or authority to execute.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .deploy_policy import TrustedDeployEvidence

_CANONICAL_REPOSITORY = "roberiooliveiradev/delpi-central"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_FRESHNESS = timedelta(seconds=120)
_CLOCK_SKEW = timedelta(seconds=5)
_PREPARE_PERMISSION = "linux_ops.deploy.prepare"
_VIEW_PERMISSION = "linux_ops.deploy.view"


@dataclass(frozen=True)
class WorkflowRunProof:
    workflow_id: int
    run_id: int
    attempt: int
    head_sha: str
    head_branch: str
    event: str
    status: str
    conclusion: str | None


@dataclass(frozen=True)
class GithubProof:
    repository: str
    commit_sha: str
    branch: str
    branch_contains_commit: bool
    runs: tuple[WorkflowRunProof, ...]
    checked_at: datetime


@dataclass(frozen=True)
class HostProof:
    environment: str
    service_id: str
    repository: str
    deployed_commit_sha: str | None
    checkout_clean: bool
    service_healthy: bool
    migrations_safe: bool
    rollback_ready: bool
    checked_at: datetime


@dataclass(frozen=True)
class CoreProof:
    subject: str
    principal_type: str
    permissions: frozenset[str]
    checked_at: datetime


@dataclass(frozen=True)
class AttestationResult:
    status: str
    blocks: tuple[str, ...]
    evidence: TrustedDeployEvidence | None = None


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _fresh(checked: object, now: object) -> bool:
    if not isinstance(checked, datetime) or not isinstance(now, datetime):
        return False
    if checked.tzinfo is None or checked.utcoffset() is None:
        return False
    if now.tzinfo is None or now.utcoffset() is None:
        return False
    age = now.astimezone(timezone.utc) - checked.astimezone(timezone.utc)
    return -_CLOCK_SKEW <= age <= _FRESHNESS


def attest_preview_evidence(
    *,
    environment: str,
    service_id: str,
    commit_sha: str,
    requester_subject: str,
    required_workflow_ids: tuple[int, ...],
    github: GithubProof | None,
    host: HostProof | None,
    core: CoreProof | None,
    now: datetime,
) -> AttestationResult:
    """Verify fixed-shape facts from trusted backend readers, never MCP inputs.

    The caller must independently fetch GitHub workflow runs and prove commit
    ancestry, fetch host revision via an authenticated local executor, and fetch
    fresh Core permissions. This function only checks the returned facts.
    """
    blocked: list[str] = []
    if environment not in ("hml", "prod") or type(environment) is not str:
        blocked.append("ENVIRONMENT_INVALID")
    if type(service_id) is not str or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", service_id):
        blocked.append("SERVICE_INVALID")
    if not _sha(commit_sha):
        blocked.append("COMMIT_SHA_INVALID")
    if type(requester_subject) is not str or re.fullmatch(r"[A-Za-z0-9._:@-]{3,128}", requester_subject) is None:
        blocked.append("REQUESTER_INVALID")
    if not _fresh(now, now):
        blocked.append("CLOCK_INVALID")

    required_valid = (
        isinstance(required_workflow_ids, tuple)
        and bool(required_workflow_ids)
        and all(type(w) is int and w > 0 for w in required_workflow_ids)
        and len(required_workflow_ids) == len(set(required_workflow_ids))
    )
    if not required_valid:
        blocked.append("CI_POLICY_MISSING")

    if not isinstance(github, GithubProof):
        blocked.append("GITHUB_PROOF_MISSING")
    else:
        if not _fresh(github.checked_at, now):
            blocked.append("GITHUB_PROOF_STALE")
        if github.repository != _CANONICAL_REPOSITORY or github.branch != "main":
            blocked.append("GITHUB_SOURCE_MISMATCH")
        if not _sha(github.commit_sha) or github.commit_sha != commit_sha or github.branch_contains_commit is not True:
            blocked.append("GITHUB_COMMIT_NOT_APPROVED")
        if not isinstance(github.runs, tuple):
            blocked.append("CI_RUNS_MALFORMED")
        elif required_valid:
            for workflow_id in required_workflow_ids:
                matching = [r for r in github.runs if isinstance(r, WorkflowRunProof)
                            and type(r.workflow_id) is int and r.workflow_id == workflow_id]
                if len(matching) != 1:
                    blocked.append("CI_REQUIRED_CHECK_MISSING_OR_AMBIGUOUS")
                    continue
                r = matching[0]
                if not (
                    type(r.run_id) is int and r.run_id > 0
                    and type(r.attempt) is int and r.attempt > 0
                    and r.head_sha == commit_sha
                    and r.head_branch == "main"
                    and r.event == "push"
                    and r.status == "completed"
                    and r.conclusion == "success"
                ):
                    blocked.append("CI_CHECK_NOT_VERIFIED")

    if not isinstance(host, HostProof):
        blocked.append("HOST_PROOF_MISSING")
    else:
        if not _fresh(host.checked_at, now):
            blocked.append("HOST_PROOF_STALE")
        if host.repository != _CANONICAL_REPOSITORY or host.environment != environment or host.service_id != service_id:
            blocked.append("HOST_TARGET_MISMATCH")
        if not _sha(host.deployed_commit_sha):
            blocked.append("DEPLOYED_REVISION_UNVERIFIED")
        elif host.deployed_commit_sha == commit_sha:
            blocked.append("ALREADY_DEPLOYED")
        if host.checkout_clean is not True:
            blocked.append("CHECKOUT_NOT_CLEAN")
        if host.service_healthy is not True:
            blocked.append("HEALTH_NOT_PASSED")
        if host.migrations_safe is not True:
            blocked.append("MIGRATION_UNSAFE")
        if host.rollback_ready is not True:
            blocked.append("ROLLBACK_NOT_READY")

    if not isinstance(core, CoreProof):
        blocked.append("CORE_PROOF_MISSING")
    else:
        if not _fresh(core.checked_at, now):
            blocked.append("CORE_PROOF_STALE")
        if core.principal_type != "user" or core.subject != requester_subject:
            blocked.append("CORE_SUBJECT_MISMATCH")
        if not isinstance(core.permissions, frozenset) or not all(type(p) is str for p in core.permissions):
            blocked.append("CORE_PERMISSIONS_INVALID")
        elif not {_VIEW_PERMISSION, _PREPARE_PERMISSION}.issubset(core.permissions):
            # Superadmin flag alone does not imply deployment approval.
            blocked.append("CORE_PREPARE_PERMISSION_MISSING")

    if blocked:
        return AttestationResult("blocked", tuple(dict.fromkeys(blocked)))

    assert isinstance(host, HostProof)
    return AttestationResult(
        status="verified_for_preview_only", blocks=(),
        evidence=TrustedDeployEvidence(
            approved_commit_sha=commit_sha,
            deployed_commit_sha=host.deployed_commit_sha,
            ci_passed=True, approved_ref_contains_commit=True,
            checkout_clean=True, health_passed=True,
            migrations_safe=True, rollback_ready=True,
            checked_at=now.astimezone(timezone.utc),
        ),
    )
