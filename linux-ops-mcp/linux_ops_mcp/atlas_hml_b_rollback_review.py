"""Source-only rollback baseline and simulation for ATLAS B pre-activation.

Typed inventory of components that *could* be reverted in a future authorized
change. Simulations run exclusively on disposable fixtures. This module never
executes rollback on a real host, never touches Docker/systemd, and never
treats operator claims as SEC attestations.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

_SCHEMA = "atlas.hml.b.rollback-baseline.v1"
_SOURCE = "operator_supplied_untrusted"
_MAX = 8192
_COMPONENTS = (
    "atlas-hml-snapshot-presenter.service.review",
    "atlas-hml-snapshot-presenter.socket.review",
    "atlas-hml-snapshot-producer.service.review",
    "atlas-hml-snapshot-producer.timer.review",
    "atlas-hml-readonly.directory.review",
)
_FIELDS = frozenset({
    "schema", "source", "host", "environment", "architecture",
    "baseline_id", "components", "non_atlas_services_untouched",
    "abort_conditions", "partial_failure_plan", "sec_matrix_refs",
})
_ABORT = frozenset({
    "DOCKER_ENGINE_IMPACT_DETECTED",
    "NON_ATLAS_UNIT_MUTATION_DETECTED",
    "PARTIAL_INSTALL_WITHOUT_ROLLBACK_PATH",
    "SEC_GATE_INCOMPLETE",
    "CHANGE_CONTROL_MISSING",
})
_BLOCKS = (
    "ROLLBACK_PLAN_IS_UNTRUSTED_REVIEW_ARTIFACT",
    "NO_HOST_ROLLBACK_EXECUTED",
    "SEC_01_TO_10_NOT_APPROVED_BY_THIS_MODULE",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLRollbackReviewError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLRollbackBaseline:
    baseline_id: str
    components: tuple[str, ...]
    abort_conditions: tuple[str, ...]
    partial_failure_plan: str
    sec_matrix_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HMLRollbackReview:
    baseline: HMLRollbackBaseline
    status: str = "blocked"
    host_rollback_attested: bool = False
    non_atlas_impact_absent_attested: bool = False
    operational_authorization_granted: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


@dataclass(frozen=True, slots=True)
class HMLRollbackSimulationResult:
    status: str = "blocked"
    rolled_back_components: tuple[str, ...] = ()
    aborted: bool = False
    abort_reason: str | None = None
    host_mutated: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise HMLRollbackReviewError("HML_ROLLBACK_DUPLICATE_FIELD")
        out[key] = value
    return out


def _reject_constant(_: str) -> object:
    raise HMLRollbackReviewError("HML_ROLLBACK_JSON_INVALID")


def review_untrusted_rollback_baseline(raw: bytes) -> HMLRollbackReview:
    """Parse an untrusted rollback baseline claim; output always blocked."""
    if type(raw) is not bytes or not 1 <= len(raw) <= _MAX or b"\x00" in raw:
        raise HMLRollbackReviewError("HML_ROLLBACK_INPUT_INVALID")
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_reject_constant,
        )
    except HMLRollbackReviewError:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise HMLRollbackReviewError("HML_ROLLBACK_JSON_INVALID") from None
    if type(document) is not dict or set(document) != _FIELDS:
        raise HMLRollbackReviewError("HML_ROLLBACK_SCHEMA_INVALID")
    if (
        document["schema"] != _SCHEMA
        or document["source"] != _SOURCE
        or document["host"] != "srv-api"
        or document["environment"] != "hml"
        or document["architecture"] != "B"
        or type(document["baseline_id"]) is not str
        or not 8 <= len(document["baseline_id"]) <= 64
        or type(document["non_atlas_services_untouched"]) is not bool
        or document["non_atlas_services_untouched"] is not True
        or type(document["partial_failure_plan"]) is not str
        or not 8 <= len(document["partial_failure_plan"]) <= 256
    ):
        raise HMLRollbackReviewError("HML_ROLLBACK_SCOPE_DENIED")
    components = document["components"]
    aborts = document["abort_conditions"]
    refs = document["sec_matrix_refs"]
    if (
        type(components) is not list or set(components) != set(_COMPONENTS)
        or any(type(item) is not str for item in components)
        or type(aborts) is not list or not aborts
        or set(aborts) - _ABORT
        or any(type(item) is not str for item in aborts)
        or type(refs) is not list
        or set(refs) != {f"SEC-{n:02d}" for n in range(1, 11)}
    ):
        raise HMLRollbackReviewError("HML_ROLLBACK_INVENTORY_INVALID")
    baseline = HMLRollbackBaseline(
        baseline_id=document["baseline_id"],
        components=tuple(sorted(components)),
        abort_conditions=tuple(sorted(set(aborts))),
        partial_failure_plan=document["partial_failure_plan"],
        sec_matrix_refs=tuple(sorted(refs)),
    )
    return HMLRollbackReview(baseline=baseline)


def simulate_rollback_in_fixture(
    review: HMLRollbackReview, *,
    installed: frozenset[str],
    abort_reason: str | None = None,
) -> HMLRollbackSimulationResult:
    """Simulate rollback against an in-memory fixture set only."""
    if type(review) is not HMLRollbackReview:
        raise HMLRollbackReviewError("HML_ROLLBACK_INPUT_INVALID")
    if type(installed) is not frozenset:
        raise HMLRollbackReviewError("HML_ROLLBACK_INPUT_INVALID")
    if any(type(item) is not str for item in installed):
        raise HMLRollbackReviewError("HML_ROLLBACK_INPUT_INVALID")
    unknown = installed - set(_COMPONENTS)
    if unknown:
        raise HMLRollbackReviewError("HML_ROLLBACK_NON_ATLAS_COMPONENT")
    if abort_reason is not None:
        if type(abort_reason) is not str or abort_reason not in _ABORT:
            raise HMLRollbackReviewError("HML_ROLLBACK_ABORT_INVALID")
        return HMLRollbackSimulationResult(
            aborted=True, abort_reason=abort_reason,
        )
    removable = tuple(sorted(installed & set(review.baseline.components)))
    return HMLRollbackSimulationResult(rolled_back_components=removable)
