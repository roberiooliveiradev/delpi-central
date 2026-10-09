"""VISTA quality telemetry — bounded in-process counters (PHASE 7, §35).

Same ownership pattern as ``presentation_mutation_telemetry``: process-local
counters + bounded deque, thread-safe, snapshot/reset for tests. No new
service, no endpoint, no persistence, no external observability stack.

TELEMETRY_SCOPE = PROCESS_LOCAL — never a cluster-global metric source.

Fail-open for product flow: recording never raises into the caller.
Fail-closed for privacy: every field is allowlisted below — unknown keys
are dropped, and free-form values (prompts, ids, tokens, content) have no
representation here by design.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

SCHEMA_VERSION = "vista-quality-v1"

_lock = threading.Lock()
_events: deque[dict[str, Any]] = deque(maxlen=500)
_counts: dict[str, int] = {}

# Allowlisted fields per event family. Values must already be bounded
# enums/booleans/small buckets — raw strings from the user never reach here.
_FIELD_ALLOWLIST: dict[str, frozenset[str]] = {
    "grounding": frozenset({"selectionState", "resolvedBucket", "missingBucket"}),
    "design": frozenset({"designIntent", "readiness", "sufficiency"}),
    "route_search": frozenset(
        {"tvRouteHit", "solutionLookupUsed", "gapClassification", "candidateBucket"}
    ),
    "verify": frozenset({"outcome"}),
}

_COUNT_BUCKET_MAX = 3


def _bucket(count: int) -> str:
    """Low-cardinality bucket: 0 / 1 / 2 / 3+ — never the raw count."""
    try:
        count = max(int(count or 0), 0)
    except (TypeError, ValueError):
        count = 0
    return str(count) if count < _COUNT_BUCKET_MAX else "3+"


def _safe_value(value: Any) -> Any:
    """Scalars only — enums, bools, pre-bucketed strings. Anything else is
    dropped rather than risk leaking free-form content."""
    if isinstance(value, (bool, int)) or value is None:
        return value
    if isinstance(value, str) and len(value) <= 64:
        return value
    return None


def record_quality_event(family: str, **fields: Any) -> None:
    """Append a bounded event + bump counters. Never raises."""
    try:
        allowed = _FIELD_ALLOWLIST.get(str(family))
        if allowed is None:
            return
        clean = {
            key: _safe_value(value)
            for key, value in fields.items()
            if key in allowed and _safe_value(value) is not None
        }
        with _lock:
            _counts[f"{family}.events"] = _counts.get(f"{family}.events", 0) + 1
            for key, value in clean.items():
                ckey = f"{family}.{key}={value}"
                _counts[ckey] = _counts.get(ckey, 0) + 1
            _events.append(
                {"ts": time.time(), "schema": SCHEMA_VERSION, "family": family, **clean}
            )
    except Exception:  # noqa: BLE001 — telemetry must never break product flow
        return


# ---- bounded recorders (one per hook family) -----------------------------


def record_grounding(*, selection_state: str | None, resolved: int, missing: int) -> None:
    """P4 grounding outcome — no object ids, no content."""
    record_quality_event(
        "grounding",
        selectionState=selection_state,
        resolvedBucket=_bucket(resolved),
        missingBucket=_bucket(missing),
    )


def record_design_methodology(
    *, design_intent: str | None, readiness: str | None, sufficiency: str | None
) -> None:
    """P5 methodology outcome — enums only, no recommendation payload."""
    record_quality_event(
        "design",
        designIntent=design_intent,
        readiness=readiness,
        sufficiency=sufficiency,
    )


def record_route_search(
    *,
    tv_route_hit: bool,
    solution_lookup_used: bool,
    gap_classification: str | None,
    candidates: int,
) -> None:
    """P6 route-search outcome — no query text, no solution ids."""
    record_quality_event(
        "route_search",
        tvRouteHit=tv_route_hit,
        solutionLookupUsed=solution_lookup_used,
        gapClassification=gap_classification,
        candidateBucket=_bucket(candidates),
    )


def record_verify_outcome(*, outcome: str | None) -> None:
    """Commit verification outcome (VERIFIED|OUTCOME_NOT_VERIFIED|…)."""
    record_quality_event("verify", outcome=outcome)


def vista_quality_telemetry_snapshot() -> dict[str, Any]:
    """Internal snapshot for tests/reporting — no route exposes this."""
    with _lock:
        return {
            "schema": SCHEMA_VERSION,
            "scope": "PROCESS_LOCAL",
            "counts": dict(_counts),
            "recent": list(_events)[-50:],
        }


def reset_vista_quality_telemetry() -> None:
    """Test-only reset — not exposed at runtime."""
    with _lock:
        _counts.clear()
        _events.clear()
