"""Decompose multi-intent editor messages into typed PresentationMutation ops.

One ranking must not drop a clause. Destructive polarity is per goal.
"""

from __future__ import annotations

import re
from typing import Any

_PERIOD_RE = re.compile(r"perioddays\s*=\s*(\d+)", re.IGNORECASE)
_PAUSE_RE = re.compile(
    r"\b(desativ\w*|paus\w*|inativ\w*)\b",
    re.IGNORECASE,
)
_DELETE_SLIDE_RE = re.compile(
    r"\b(apague o slide|apagar o slide|excluir o slide|exclua o slide|delete slide)\b",
    re.IGNORECASE,
)
_FILTER_RE = re.compile(
    r"perioddays|centraliz\w*|duplicidade|filtros?\s+duplic",
    re.IGNORECASE,
)
_COUNT_TWO_RE = re.compile(r"\b(dois|duas|2)\b", re.IGNORECASE)


def plan_compound_goals(message: str) -> dict[str, Any] | None:
    """Return ops + goal ledger when the message has 2+ independent intents.

    A lone delete stays None so the capability scorer owns that case.
    """
    text = str(message or "").strip()
    if not text:
        return None

    goals: list[dict[str, Any]] = []
    ops: list[dict[str, Any]] = []

    if _FILTER_RE.search(text):
        days_match = _PERIOD_RE.search(text)
        days = int(days_match.group(1)) if days_match else None
        defaults: dict[str, Any] = {}
        if days is not None:
            defaults["periodDays"] = days
        goals.append({"id": "centralize_period", "op": "patch_playlist_data_defaults"})
        ops.append(
            {
                "op": "patch_playlist_data_defaults",
                "dataDefaults": defaults,
                "replace": False,
            }
        )
        keys = ["periodDays"] if days is not None else []
        goals.append({"id": "relayer_filters", "op": "re_layer_playlist_filters"})
        ops.append(
            {
                "op": "re_layer_playlist_filters",
                "scope": "playlist",
                "keys": keys,
            }
        )

    if _PAUSE_RE.search(text) and re.search(r"\bslides?\b", text, re.IGNORECASE):
        count = 2 if _COUNT_TWO_RE.search(text) else 1
        for index in range(count):
            goals.append({"id": f"pause_slide_{index + 1}", "op": "update_slide"})
            ops.append({"op": "update_slide", "isActive": False})

    delete_only = bool(_DELETE_SLIDE_RE.search(text)) and not goals
    if delete_only:
        return None

    if _DELETE_SLIDE_RE.search(text) and goals:
        goals.append({"id": "delete_slide", "op": "delete_slide"})
        ops.append({"op": "delete_slide"})

    if len(goals) < 2:
        return None

    return {
        "interpretedGoals": goals,
        "ignoredGoals": [],
        "warnings": [],
        "ops": ops,
        "matchedCapabilityKeys": [str(goal["op"]) for goal in goals],
    }
