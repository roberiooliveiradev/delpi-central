from __future__ import annotations

from typing import Any

from app.domain.services.lmp_history_event_enrichment import (
    is_engineering_flow,
    is_event_open,
    normalize_revision,
    revisions_match,
)

FLOW_TRANSITION_LABELS: dict[str, str] = {
    "engineering_entry": "Entrada na engenharia",
    "advanced_from_engineering": "Saída da engenharia (avanço)",
    "returned_from_engineering": "Retorno da engenharia",
}

INTERNAL_CONTEXT_FIELDS = frozenset(
    {
        "next_revision",
        "next_process_code",
        "next_stage_code",
        "next_start_date",
        "previous_revision",
        "previous_process_code",
        "previous_stage_code",
    }
)


def label_for_flow_transition(code: str | None) -> str | None:
    normalized = str(code or "").strip()
    if not normalized:
        return None
    return FLOW_TRANSITION_LABELS.get(normalized, normalized)


def _is_next_engineering(event: dict[str, Any]) -> bool:
    next_event = {
        "process_code": event.get("next_process_code"),
        "stage_code": event.get("next_stage_code"),
        "is_engineering": False,
    }
    return is_engineering_flow(next_event)


def _is_closed_for_flow_transition(event: dict[str, Any]) -> bool:
    if not is_event_open(event):
        return True

    return bool(str(event.get("next_start_date") or "").strip())


def detect_engineering_entry(event: dict[str, Any]) -> bool:
    if not is_engineering_flow(event) and not bool(event.get("is_engineering")):
        return False

    previous_stage = str(event.get("previous_stage_code") or "").strip()
    if not previous_stage:
        return True

    previous_event = {
        "revision": event.get("previous_revision"),
        "process_code": event.get("previous_process_code"),
        "stage_code": previous_stage,
        "is_engineering": False,
    }

    if (
        revisions_match(previous_event.get("revision"), event.get("revision"))
        and is_engineering_flow(previous_event)
    ):
        return False

    return True


def detect_flow_transition(event: dict[str, Any]) -> str | None:
    if not is_engineering_flow(event) and not bool(event.get("is_engineering")):
        return None

    if not _is_closed_for_flow_transition(event):
        return None

    next_stage = str(event.get("next_stage_code") or "").strip()
    next_revision = str(event.get("next_revision") or "").strip()
    if not next_stage:
        return None

    if _is_next_engineering(event):
        return None

    current_revision = str(event.get("revision") or "").strip()
    current_stage = str(event.get("stage_code") or "").strip()

    if revisions_match(next_revision, current_revision) and next_stage > current_stage:
        return "advanced_from_engineering"

    if not revisions_match(next_revision, current_revision):
        if normalize_revision(next_revision) > normalize_revision(current_revision):
            return "returned_from_engineering"
        if next_stage < current_stage:
            return "returned_from_engineering"

    if next_stage < current_stage:
        return "returned_from_engineering"

    return None


def enrich_flow_transition_fields(event: dict[str, Any]) -> dict[str, Any]:
    transition = detect_flow_transition(event)
    is_entry = detect_engineering_entry(event)

    cleaned = {
        key: value
        for key, value in event.items()
        if key not in INTERNAL_CONTEXT_FIELDS
    }

    flow_codes: list[str] = []
    if is_entry:
        flow_codes.append("engineering_entry")
    if transition:
        flow_codes.append(transition)

    cleaned["is_engineering_entry"] = is_entry
    cleaned["flow_transition"] = transition
    cleaned["flow_transitions"] = flow_codes
    cleaned["flow_transition_label"] = (
        label_for_flow_transition(transition) if transition else None
    )
    cleaned["flow_transition_labels"] = [
        label
        for code in flow_codes
        if (label := label_for_flow_transition(code)) is not None
    ]

    return cleaned
