"""ATLAS P2.2h.2z: recovery/migration metadata for a future HML pilot.

Offline sanity checks ONLY: a reference ID or an operator's declaration
does not prove that a backup restored, rollback ran or migration was safe.
Do not ingest arbitrary files/URLs, execute commands or elevate eligibility.
Never construct rollback_ready=True or migrations_safe=True here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from .atlas_deploy_host_receipt_bridge import ExpectedBaseRelease

_REF = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}\Z")
_IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_WINDOW = timedelta(hours=72)
_SKEW = timedelta(seconds=5)
_ALWAYS = (
    "BACKUP_RESTORE_INDEPENDENT_PROOF_MISSING",
    "ROLLBACK_EXECUTION_INDEPENDENT_PROOF_MISSING",
    "MIGRATION_SAFETY_INDEPENDENT_PROOF_MISSING",
    "RECOVERY_REVIEW_AUTHORITY_UNVERIFIED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLRecoveryReviewError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class RecoveryArtifactMetadata:
    """Untrusted references, never a signed proof or executable instruction."""

    backup_inventory_ref: str | None = None
    restore_test_ref: str | None = None
    restore_tested_at: datetime | None = None
    rollback_test_ref: str | None = None
    rollback_tested_at: datetime | None = None
    rollback_image_id: str | None = None
    migration_review_ref: str | None = None
    migration_reviewed_at: datetime | None = None
    migration_plan_sha256: str | None = None
    observed_by_subject: str | None = None
    reviewed_by_subject: str | None = None


@dataclass(frozen=True, slots=True)
class HMLRecoveryMetadataReport:
    """Only a checklist diagnostic. Status NEVER ready or approved."""

    status: str
    blocks: tuple[str, ...]
    submitted_metadata_consistent: bool
    submitted_metadata_recent: bool
    rollback_matches_base: bool
    actual_restore_verified: bool = False
    actual_rollback_verified: bool = False
    actual_migrations_verified: bool = False
    independent_reviewer_verified: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _aware(t: object) -> bool:
    return type(t) is datetime and t.tzinfo is not None and t.utcoffset() is not None


def _valid_uuid4(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        obj = UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return obj.version == 4 and str(obj) == value


def _reference(value: object) -> bool:
    return type(value) is str and _REF.fullmatch(value) is not None


def _recent(t: object, now: datetime) -> bool:
    if not _aware(t):
        return False
    age = now.astimezone(timezone.utc) - t.astimezone(timezone.utc)
    return -_SKEW <= age <= _WINDOW


def inspect_hml_recovery_metadata(
    *,
    base: ExpectedBaseRelease,
    submitted: RecoveryArtifactMetadata | None,
    now: datetime,
) -> HMLRecoveryMetadataReport:
    """Inspect references without opening files/links or accepting a sign-off.

    All submitted fields are untrusted, including operator identities.
    A successful metadata review has *no* effect on PREPARE/ACT.
    """
    if (
        type(base) is not ExpectedBaseRelease
        or type(base.image_id) is not str
        or _IMAGE.fullmatch(base.image_id) is None
        or not _aware(now)
        or submitted is not None and type(submitted) is not RecoveryArtifactMetadata
    ):
        raise HMLRecoveryReviewError("ATLAS_RECOVERY_METADATA_INVALID")

    if submitted is None:
        return HMLRecoveryMetadataReport(
            status="blocked", blocks=(*_ALWAYS, "RECOVERY_METADATA_NOT_SUBMITTED"),
            submitted_metadata_consistent=False,
            submitted_metadata_recent=False,
            rollback_matches_base=False,
        )

    fields_ok = all(_reference(x) for x in (
        submitted.backup_inventory_ref,
        submitted.restore_test_ref,
        submitted.rollback_test_ref,
        submitted.migration_review_ref,
    ))
    migration_ok = (
        type(submitted.migration_plan_sha256) is str
        and _SHA.fullmatch(submitted.migration_plan_sha256) is not None
    )
    rollback_ok = (
        type(submitted.rollback_image_id) is str
        and _IMAGE.fullmatch(submitted.rollback_image_id) is not None
        and submitted.rollback_image_id == base.image_id
    )
    independent_claimed = (
        _valid_uuid4(submitted.observed_by_subject)
        and _valid_uuid4(submitted.reviewed_by_subject)
        and submitted.observed_by_subject != submitted.reviewed_by_subject
    )
    timestamps_ok = all(_recent(ts, now) for ts in (
        submitted.restore_tested_at,
        submitted.rollback_tested_at,
        submitted.migration_reviewed_at,
    ))
    consistent = bool(fields_ok and migration_ok and rollback_ok and independent_claimed)
    blocked = list(_ALWAYS)
    if not fields_ok or not migration_ok:
        blocked.append("RECOVERY_METADATA_INCOMPLETE_OR_MALFORMED")
    if not rollback_ok:
        blocked.append("ROLLBACK_BASE_IMAGE_NOT_MATCHED")
    if not independent_claimed:
        blocked.append("INDEPENDENT_REVIEWER_NOT_ESTABLISHED")
    if not timestamps_ok:
        blocked.append("RECOVERY_METADATA_OUTSIDE_REVIEW_WINDOW")
    return HMLRecoveryMetadataReport(
        status="blocked",
        blocks=tuple(blocked),
        submitted_metadata_consistent=consistent,
        submitted_metadata_recent=timestamps_ok,
        rollback_matches_base=rollback_ok,
    )
