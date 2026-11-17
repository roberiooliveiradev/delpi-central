"""One-shot candidate: guarded HML inspect -> atomic snapshot (CI-only).

No operational entrypoint, daemon, timer, Docker socket constructor, MCP tool,
host filesystem path or PREPARE/ACT capability is exposed. Only an injected
transport and an explicitly supplied disposable directory are accepted.

The code does NOT confine a privileged process: anyone holding the raw Docker
socket can bypass Python, even if this class enforces a single GET. Architecture
option B remains unapproved until independent security and Linux review.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx

from .atlas_hml_engine_boundary import HMLDockerInspectOnly, HML_TARGET
from .atlas_hml_snapshot_publisher_candidate import (
    HMLSnapshotPublishError,
    _publish_in_review_directory,
    build_hml_snapshot_claim,
)
from .deploy_host_source import HostSourceError


class HMLOneShotError(Exception):
    """Finite error code only; never expose Docker JSON or OS error text."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLOneShotReceipt:
    status: str
    service_id: str
    environment: str
    snapshot_written: bool
    snapshot_origin_attested: bool = False
    upstream_isolation_attested: bool = False
    host_identity_attested: bool = False
    checkout_integrity_attested: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


async def _run_disposable_hml_producer_once(
    *, upstream: httpx.AsyncBaseTransport, directory: Path,
    owner_uid: int, expected_gid: int, observed_at: datetime,
) -> HMLOneShotReceipt:
    """Fixture-only one-shot assembly, never a deploy/installation API.

    This function cannot select another target, HTTP method, or destination
    file. Callers supply a disposable directory and *injected* transport.
    Production may NOT import/call it until ADR and privilege review.
    """
    if (
        not isinstance(upstream, httpx.AsyncBaseTransport)
        or not isinstance(directory, Path)
        or not directory.is_absolute()
        or type(owner_uid) is not int or owner_uid < 0
        or type(expected_gid) is not int or expected_gid < 0
        or type(observed_at) is not datetime
        or observed_at.tzinfo is None
        or observed_at.utcoffset() is None
    ):
        raise HMLOneShotError("HML_ONESHOT_INPUT_INVALID")

    try:
        inspector = HMLDockerInspectOnly(upstream=upstream)
        runtime = await inspector.inspect(HML_TARGET)
    except (HostSourceError, httpx.HTTPError, OSError, ValueError, TypeError):
        raise HMLOneShotError("HML_ONESHOT_INSPECT_UNAVAILABLE") from None

    try:
        data = build_hml_snapshot_claim(runtime, observed_at=observed_at)
        _publish_in_review_directory(
            directory, raw=data, owner_uid=owner_uid,
            expected_gid=expected_gid, now=observed_at,
        )
    except HMLSnapshotPublishError:
        # Publication failure must never be interpreted as a successful
        # observation; pre-existing snapshot is subject to its original TTL.
        raise HMLOneShotError("HML_ONESHOT_PUBLISH_UNAVAILABLE") from None

    return HMLOneShotReceipt(
        status="blocked",
        service_id="public-hub",
        environment="hml",
        snapshot_written=True,
    )
