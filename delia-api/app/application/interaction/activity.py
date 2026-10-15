"""ActivityEvent.v1 — bounded semantic observation of an in-flight turn.

DELIA-C3-PROGRESSIVE-ACTIVITY-NDJSON-END-TO-END-IMPLEMENTATION-01
(doc 70 §15/§16 — Option A approved): the interaction application layer
emits honest, provider-neutral activity observations while a turn runs.
An event records a frontier the runtime actually reached — never a
plan, never an inference, never a raw provider payload.

Ownership: this module owns the semantic contract and the wire record
shape only. The NDJSON carriage (queue, worker thread, Flask Response)
lives in ``interfaces/http`` — Application never touches a framework
object. A simple channel callable is the transport seam: no port
interface is needed because there is exactly one producer-facing
operation (append one event) and one consumer (the HTTP adapter).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Mapping

ACTIVITY_EVENT_VERSION = "1"
ACTIVITY_RECORD_TYPE = "activity_event"
TURN_RESULT_RECORD_TYPE = "turn_result"
TURN_ERROR_RECORD_TYPE = "turn_error"

# Bounded disclosure: every free-text value is truncated before it can
# reach the wire. These bounds mirror the provenance projection scale —
# they exist so an owner-controlled string can never grow a stream
# unboundedly.
MAX_REF_TEXT_CHARS = 200


class ActivityPhase(str, Enum):
    """Closed semantic vocabulary — observed frontiers, not planned steps."""

    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    CONTEXTUALIZING = "CONTEXTUALIZING"
    CAPABILITY_SELECTED = "CAPABILITY_SELECTED"
    SOURCE_QUERY_STARTED = "SOURCE_QUERY_STARTED"
    SOURCE_QUERY_COMPLETED = "SOURCE_QUERY_COMPLETED"
    OUTCOME_PREPARING = "OUTCOME_PREPARING"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ActivityState(str, Enum):
    """Per-event observed state — the frontend maps it to its own
    presentation vocabulary; it is never invented progress."""

    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    DENIED = "denied"
    CANCELLED = "cancelled"
    WAITING = "waiting"
    NO_DATA = "no_data"


# Honest default state per phase; an emitter may override when the
# observation itself is a failure/denial (e.g. SOURCE_QUERY_COMPLETED
# after a provider error).
_PHASE_DEFAULT_STATE = {
    ActivityPhase.REQUEST_RECEIVED: ActivityState.COMPLETED,
    ActivityPhase.CONTEXTUALIZING: ActivityState.RUNNING,
    ActivityPhase.CAPABILITY_SELECTED: ActivityState.COMPLETED,
    ActivityPhase.SOURCE_QUERY_STARTED: ActivityState.RUNNING,
    ActivityPhase.SOURCE_QUERY_COMPLETED: ActivityState.COMPLETED,
    ActivityPhase.OUTCOME_PREPARING: ActivityState.RUNNING,
    ActivityPhase.WAITING_CONFIRMATION: ActivityState.WAITING,
    ActivityPhase.COMPLETED: ActivityState.COMPLETED,
    ActivityPhase.PARTIAL: ActivityState.PARTIAL,
    ActivityPhase.BLOCKED: ActivityState.BLOCKED,
    ActivityPhase.FAILED: ActivityState.FAILED,
    ActivityPhase.CANCELLED: ActivityState.CANCELLED,
}


class ActivityOutcomeStatus(str, Enum):
    """Safe result classification — real observation, never HTTP-inferred."""

    RETURNED_DATA = "returned_data"
    COMPLETED_NO_DATA = "completed_no_data"
    PARTIAL = "partial"
    ERROR = "error"


_REF_KEYS = frozenset(
    {"remote_name", "protocol", "operation_class", "source_id",
     "source_system", "display_name", "owner_ref"}
)


def _bounded_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    return text[:MAX_REF_TEXT_CHARS]


def capability_ref(
    *,
    remote_name: str | None,
    protocol: str | None = None,
    operation_class: str | None = None,
) -> dict[str, str] | None:
    """Bounded capability reference — the owner-declared remote name and
    only fields legitimately observed. ``protocol`` must come from real
    provenance (an outcome), never from the binding internals."""
    ref: dict[str, str] = {}
    for key, value in (
        ("remote_name", remote_name),
        ("protocol", protocol),
        ("operation_class", operation_class),
    ):
        text = _bounded_text(value)
        if text is not None:
            ref[key] = text
    return ref or None


def source_ref(
    *,
    source_system: str | None,
    source_id: str | None = None,
) -> dict[str, str] | None:
    """Bounded source reference — mirrors the existing disclosure-safe
    ``provenance.to_projection()`` shape. Never URLs or endpoints."""
    ref: dict[str, str] = {}
    for key, value in (
        ("source_id", source_id),
        ("source_system", source_system),
    ):
        text = _bounded_text(value)
        if text is not None:
            ref[key] = text
    return ref or None


def owner_ref(
    *,
    display_name: str | None,
    owner_ref: str | None = None,
) -> dict[str, str] | None:
    """Bounded owner/specialist identity — only when actually selected."""
    ref: dict[str, str] = {}
    for key, value in (
        ("display_name", display_name),
        ("owner_ref", owner_ref),
    ):
        text = _bounded_text(value)
        if text is not None:
            ref[key] = text
    return ref or None


def outcome_ref(
    *,
    status: ActivityOutcomeStatus | str,
    record_count: int | None = None,
) -> dict[str, Any] | None:
    """Safe result summary — a classification plus a real count only.
    ``record_count`` is included solely when it was actually counted;
    it is never inferred from transport success."""
    try:
        status_value = ActivityOutcomeStatus(status).value
    except ValueError:
        return None
    ref: dict[str, Any] = {"status": status_value}
    if isinstance(record_count, int) and not isinstance(record_count, bool) \
            and record_count >= 0:
        ref["record_count"] = record_count
    return ref


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    """One observed execution frontier — ActivityEvent.v1 (doc 70 §16).

    Reference payloads are pre-sanitized bounded dicts; the serializer
    additionally allowlists keys so nothing unexpected can reach the
    wire even if a caller constructs a ref by hand.
    """

    event_id: str
    sequence: int
    timestamp: str
    session_id: str
    turn_id: str
    phase: ActivityPhase
    state: ActivityState
    label_code: str
    correlation_id: str | None = None
    capability_ref: Mapping[str, Any] | None = None
    source_ref: Mapping[str, Any] | None = None
    owner_ref: Mapping[str, Any] | None = None
    outcome_ref: Mapping[str, Any] | None = None
    version: str = ACTIVITY_EVENT_VERSION

    def to_record(self) -> dict[str, Any]:
        """NDJSON line payload — contract order, optional refs omitted
        when absent."""
        record: dict[str, Any] = {
            "type": ACTIVITY_RECORD_TYPE,
            "version": self.version,
            "event_id": self.event_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "phase": self.phase.value,
            "state": self.state.value,
            "label_code": self.label_code,
        }
        if self.correlation_id:
            record["correlation_id"] = self.correlation_id
        for name, ref in (
            ("capability_ref", self.capability_ref),
            ("source_ref", self.source_ref),
            ("owner_ref", self.owner_ref),
        ):
            if isinstance(ref, Mapping):
                allowed = {
                    k: _bounded_text(v)
                    for k, v in ref.items()
                    if k in _REF_KEYS and _bounded_text(v) is not None
                }
                if allowed:
                    record[name] = allowed
        if isinstance(self.outcome_ref, Mapping):
            status = self.outcome_ref.get("status")
            count = self.outcome_ref.get("record_count")
            projection: dict[str, Any] = {}
            try:
                projection["status"] = ActivityOutcomeStatus(status).value
            except ValueError:
                projection["status"] = None
            if isinstance(count, int) and not isinstance(count, bool) \
                    and count >= 0:
                projection["record_count"] = count
            if projection.get("status"):
                record["outcome_ref"] = projection
        return record


class ActivityEventSink:
    """Request-scoped emitter bound to the real session/turn identity.

    Created inside the use case only after ``session_id`` and
    ``turn_id`` exist — an event can never carry invented identifiers.
    The sink stamps ``event_id``/``sequence``/``timestamp`` itself;
    callers supply only the observed semantics.
    """

    def __init__(
        self,
        channel: Callable[[ActivityEvent], None],
        *,
        session_id: str,
        turn_id: str,
    ) -> None:
        self._channel = channel
        self._session_id = session_id
        self._turn_id = turn_id
        self._sequence = 0

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def turn_id(self) -> str:
        return self._turn_id

    def emit(
        self,
        *,
        phase: ActivityPhase,
        state: ActivityState | None = None,
        label_code: str | None = None,
        correlation_id: str | None = None,
        capability_ref: Mapping[str, Any] | None = None,
        source_ref: Mapping[str, Any] | None = None,
        owner_ref: Mapping[str, Any] | None = None,
        outcome_ref: Mapping[str, Any] | None = None,
    ) -> ActivityEvent:
        """Record one observed frontier and hand it to the channel.

        The channel is synchronous and bounded (an in-memory queue or a
        test collector); a transport failure must never crash the use
        case, so emission is fail-safe — the event is an observation,
        not part of the result's authority.
        """
        self._sequence += 1
        event = ActivityEvent(
            event_id=str(uuid.uuid4()),
            sequence=self._sequence,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self._session_id,
            turn_id=self._turn_id,
            phase=phase,
            state=state or _PHASE_DEFAULT_STATE[phase],
            label_code=(
                _bounded_text(label_code) or phase.value
            ),
            correlation_id=(
                _bounded_text(correlation_id)
            ),
            capability_ref=capability_ref,
            source_ref=source_ref,
            owner_ref=owner_ref,
            outcome_ref=outcome_ref,
        )
        try:
            self._channel(event)
        except Exception:  # noqa: BLE001 — activity must never break the turn
            pass
        return event


def activity_sink_or_none(
    channel: Callable[[ActivityEvent], None] | None,
    *,
    session_id: str,
    turn_id: str,
) -> ActivityEventSink | None:
    """Build the request-scoped sink when a channel is present."""
    if channel is None:
        return None
    return ActivityEventSink(channel, session_id=session_id, turn_id=turn_id)
