"""ATLAS P2.2h.2m: challenge-bound, signed READ-ONLY Git observation.

Offline library only, not an MCP/HTTP route, signer service or deploy tool.
A valid HMAC proves a key signed THIS observation, not that the collector,
filesystem, local Git configuration or checkout contents were independently
trusted. The signer must be run by a separately approved least-privilege host
collector and receive a journal-issued one-shot nonce from a trusted backend.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .deploy_git_checkout_readonly import (
    GitCheckoutObservation, GitCheckoutReadOnlyObserver, _ALLOWLIST,
)
from .deploy_host_receipt import SignedHostReceipt, _time, _unique_pairs
from .deploy_host_source import RuntimeTarget, validate_target

_REPO = "roberiooliveiradev/delpi-central"
_DOMAIN = b"atlas:git-checkout-observation:v1:\x00"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_BRANCH = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._/-]{0,127}\Z")
_MAX_BYTES = 3072
_MAX_AGE = timedelta(seconds=90)
_MAX_SKEW = timedelta(seconds=5)
_FIELDS = frozenset((
    "version", "repository", "host_id", "environment", "service_id",
    "compose_project", "container_name", "branch", "head_sha",
    "tracked_and_untracked_clean", "observation_scope", "observed_at",
    "challenge",
))
_SCOPE = "tracked_and_untracked_nonignored"


class GitCheckoutWitnessError(Exception):
    """Finite and safe rejection codes, never raw Git output, keys or nonces."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class VerifiedGitCheckoutWitness:
    """Authenticated MAC only; it is never a PREPARE or ACT authorization."""

    host_id: str
    environment: str
    service_id: str
    container_name: str
    compose_project: str
    branch: str
    head_sha: str
    observed_clean: bool
    observed_at: datetime
    challenge_sha256: str
    receipt_sha256: str
    signature_verified: bool = True
    challenge_bound: bool = True
    checkout_trust_approved: bool = False
    challenge_consumed: bool = False
    rollback_ready: bool = False
    prepare_eligible: bool = False


def _valid_target(target: object) -> bool:
    if not validate_target(target):
        return False
    expected = _ALLOWLIST.get((target.environment, target.service_id))
    return expected is not None and (
        target.container_name, target.compose_project
    ) == expected


def _valid_nonce(value: object) -> bool:
    return type(value) is str and _HEX64.fullmatch(value) is not None


def _valid_key(value: object) -> bool:
    return type(value) is bytes and len(value) >= 32


def _fresh(value: datetime, now: datetime) -> bool:
    age = now.astimezone(timezone.utc) - value.astimezone(timezone.utc)
    return -_MAX_SKEW <= age <= _MAX_AGE


def _configured(
    *, target: RuntimeTarget, key: bytes,
    challenge: str, now: datetime,
) -> None:
    if (
        not _valid_target(target) or not _valid_key(key)
        or not _valid_nonce(challenge)
        or type(now) is not datetime
        or now.tzinfo is None or now.utcoffset() is None
    ):
        raise GitCheckoutWitnessError("GIT_WITNESS_NOT_CONFIGURED")


def _valid_observation(observation: object, target: RuntimeTarget) -> bool:
    return (
        type(observation) is GitCheckoutObservation
        and observation.environment == target.environment
        and observation.service_id == target.service_id
        and type(observation.branch) is str
        and _BRANCH.fullmatch(observation.branch) is not None
        and type(observation.head_sha) is str
        and _SHA40.fullmatch(observation.head_sha) is not None
        and type(observation.tracked_and_untracked_clean) is bool
        and type(observation.observed_at) is datetime
        and observation.observed_at.tzinfo is not None
        and observation.observed_at.utcoffset() is not None
        and observation.status == "inspection_only_blocked"
        and observation.checkout_attested is False
        and observation.challenge_bound is False
        and observation.rollback_ready is False
        and observation.prepare_eligible is False
    )


def issue_git_checkout_witness(
    *, observer: GitCheckoutReadOnlyObserver, target: RuntimeTarget,
    signing_key: bytes, challenge: str, now: datetime,
) -> SignedHostReceipt:
    """Obtain a fresh local read-only Git measurement and sign its exact bytes.

    Observer injection is ONLY for isolated tests/trusted host composition;
    never expose a caller-selected root, runner or observer in any API.
    A dirty checkout or a feature branch is signed as a diagnostic, not
    represented as clean or promoted into an eligible claim.
    """
    _configured(target=target, key=signing_key, challenge=challenge, now=now)
    if not isinstance(observer, GitCheckoutReadOnlyObserver):
        raise GitCheckoutWitnessError("GIT_WITNESS_OBSERVER_INVALID")
    try:
        observed = observer.read(target=target)
    except Exception:
        # Git stderr and paths can contain private operational information.
        raise GitCheckoutWitnessError("GIT_WITNESS_OBSERVATION_UNAVAILABLE") from None
    if not _valid_observation(observed, target):
        raise GitCheckoutWitnessError("GIT_WITNESS_OBSERVATION_INVALID")
    if not _fresh(observed.observed_at, now):
        raise GitCheckoutWitnessError("GIT_WITNESS_OBSERVATION_STALE")

    body = {
        "version": 1, "repository": _REPO, "host_id": target.host_id,
        "environment": target.environment, "service_id": target.service_id,
        "compose_project": target.compose_project,
        "container_name": target.container_name,
        "branch": observed.branch, "head_sha": observed.head_sha,
        "tracked_and_untracked_clean": observed.tracked_and_untracked_clean,
        "observation_scope": _SCOPE,
        "observed_at": observed.observed_at.astimezone(timezone.utc).isoformat(
            timespec="seconds",
        ).replace("+00:00", "Z"),
        "challenge": challenge,
    }
    payload = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    if len(payload) > _MAX_BYTES:
        raise GitCheckoutWitnessError("GIT_WITNESS_RECEIPT_INVALID")
    signature = hmac.new(signing_key, _DOMAIN + payload, hashlib.sha256).hexdigest()
    return SignedHostReceipt(payload, signature)


def verify_git_checkout_witness(
    receipt: SignedHostReceipt, *, verification_key: bytes,
    target: RuntimeTarget, expected_challenge: str, now: datetime,
) -> VerifiedGitCheckoutWitness:
    """Verify MAC, target and nonce, without any access to Git or Docker.

    This does not consume the challenge in the journal. A verified MAC
    cannot prove that the signer process or its Git repository was trusted.
    """
    _configured(
        target=target, key=verification_key,
        challenge=expected_challenge, now=now,
    )
    if (
        type(receipt) is not SignedHostReceipt
        or type(receipt.body) is not bytes
        or not 1 <= len(receipt.body) <= _MAX_BYTES
        or type(receipt.mac_hex) is not str
        or _HEX64.fullmatch(receipt.mac_hex) is None
    ):
        raise GitCheckoutWitnessError("GIT_WITNESS_RECEIPT_INVALID")

    expected = hmac.new(
        verification_key, _DOMAIN + receipt.body, hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, receipt.mac_hex):
        raise GitCheckoutWitnessError("GIT_WITNESS_SIGNATURE_INVALID")
    try:
        payload = json.loads(
            receipt.body, object_pairs_hook=_unique_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid constant")),
        )
    except (ValueError, UnicodeError, TypeError):
        raise GitCheckoutWitnessError("GIT_WITNESS_RECEIPT_INVALID") from None
    if type(payload) is not dict or frozenset(payload) != _FIELDS:
        raise GitCheckoutWitnessError("GIT_WITNESS_RECEIPT_INVALID")
    if (
        type(payload["version"]) is not int or payload["version"] != 1
        or payload["repository"] != _REPO
        or payload["host_id"] != target.host_id
        or payload["environment"] != target.environment
        or payload["service_id"] != target.service_id
        or payload["compose_project"] != target.compose_project
        or payload["container_name"] != target.container_name
        or type(payload["challenge"]) is not str
        or not hmac.compare_digest(payload["challenge"], expected_challenge)
    ):
        raise GitCheckoutWitnessError("GIT_WITNESS_TARGET_MISMATCH")
    if (
        type(payload["head_sha"]) is not str
        or _SHA40.fullmatch(payload["head_sha"]) is None
        or type(payload["branch"]) is not str
        or _BRANCH.fullmatch(payload["branch"]) is None
        or type(payload["tracked_and_untracked_clean"]) is not bool
        or payload["observation_scope"] != _SCOPE
    ):
        raise GitCheckoutWitnessError("GIT_WITNESS_OBSERVATION_INVALID")
    observed = _time(payload["observed_at"])
    if observed is None:
        raise GitCheckoutWitnessError("GIT_WITNESS_TIME_INVALID")
    if not _fresh(observed, now):
        raise GitCheckoutWitnessError("GIT_WITNESS_OBSERVATION_STALE")

    return VerifiedGitCheckoutWitness(
        host_id=target.host_id, environment=target.environment,
        service_id=target.service_id, container_name=target.container_name,
        compose_project=target.compose_project,
        branch=payload["branch"], head_sha=payload["head_sha"],
        observed_clean=payload["tracked_and_untracked_clean"],
        observed_at=observed,
        challenge_sha256=hashlib.sha256(
            bytes.fromhex(expected_challenge),
        ).hexdigest(),
        receipt_sha256=hashlib.sha256(receipt.body).hexdigest(),
    )
