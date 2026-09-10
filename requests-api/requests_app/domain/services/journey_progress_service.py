"""Resolve journey_progress projection from declarative workflow_definition.journey.

Presentation-only — does not participate in WorkflowEngine transitions.
"""

from __future__ import annotations

from typing import Any

_VALID_OUTCOMES = frozenset(
    {"in_progress", "waiting_requester", "succeeded", "cancelled", "rejected"}
)
_STAGE_STATES = frozenset({"complete", "current", "upcoming", "error"})


def resolve_journey_progress(
    workflow: dict[str, Any] | None,
    *,
    status: str,
) -> dict[str, Any] | None:
    """Build a ready-to-render journey_progress dict, or None if journey is absent."""
    journey = (workflow or {}).get("journey")
    if not isinstance(journey, dict):
        return None

    stages_cfg = journey.get("stages") or []
    mappings = journey.get("statusMappings") or []
    if not isinstance(stages_cfg, list) or not stages_cfg:
        return None

    mapping = _find_mapping(mappings, status)
    if mapping is None:
        return None

    stage_id = mapping.get("stageId")
    if not isinstance(stage_id, str) or not stage_id:
        return None

    try:
        percentage = int(mapping.get("progressPercent"))
    except (TypeError, ValueError):
        return None
    percentage = max(0, min(100, percentage))

    outcome_raw = str(mapping.get("outcome") or "in_progress")
    outcome = outcome_raw if outcome_raw in _VALID_OUTCOMES else "in_progress"
    summary = mapping.get("summary")
    summary_str = str(summary).strip() if summary else None

    stage_ids = []
    stage_labels: dict[str, str] = {}
    for item in stages_cfg:
        if not isinstance(item, dict):
            continue
        sid = item.get("id")
        if not isinstance(sid, str) or not sid:
            continue
        stage_ids.append(sid)
        stage_labels[sid] = str(item.get("label") or sid)

    if stage_id not in stage_ids:
        return None

    current_index = stage_ids.index(stage_id)
    error_outcomes = frozenset({"cancelled", "rejected"})
    stages_out: list[dict[str, Any]] = []
    for index, sid in enumerate(stage_ids):
        if index < current_index:
            state = "complete"
        elif index == current_index:
            state = "error" if outcome in error_outcomes else "current"
        else:
            state = "upcoming"
        stages_out.append(
            {
                "id": sid,
                "label": stage_labels[sid],
                "state": state if state in _STAGE_STATES else "upcoming",
            }
        )

    return {
        "percentage": percentage,
        "current_stage_id": stage_id,
        "outcome": outcome,
        "summary": summary_str or None,
        "stages": stages_out,
    }


def _find_mapping(mappings: Any, status: str) -> dict[str, Any] | None:
    if not isinstance(mappings, list):
        return None
    for item in mappings:
        if not isinstance(item, dict):
            continue
        statuses = item.get("statuses") or []
        if isinstance(statuses, list) and status in statuses:
            return item
    return None
