"""Casos M1–M15 — playbook memória e contexto (§79)."""

from __future__ import annotations

MEMORY_CONTEXT_REGRESSION_CASES: list[dict] = [
    {"id": "M1", "kind": "product_follow_up"},
    {"id": "M3", "kind": "continuation_missing"},
    {"id": "M5", "kind": "this_ambiguous"},
    {"id": "M6", "kind": "user_correction"},
    {"id": "M7", "kind": "topic_change"},
    {"id": "M10", "kind": "correction_priority"},
    {"id": "M14", "kind": "sensitive_skip_write"},
    {"id": "M15", "kind": "clear_context"},
]
