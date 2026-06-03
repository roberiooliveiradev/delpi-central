"""Casos M1–M17 — playbook memória e contexto (§79)."""

from __future__ import annotations

MEMORY_CONTEXT_REGRESSION_CASES: list[dict] = [
    {"id": "M1", "kind": "product_follow_up"},
    {"id": "M3", "kind": "continuation_missing"},
    {"id": "M4", "kind": "this_table"},
    {"id": "M5", "kind": "this_ambiguous"},
    {"id": "M6", "kind": "user_correction"},
    {"id": "M7", "kind": "topic_change"},
    {"id": "M8", "kind": "resume_task"},
    {"id": "M2", "kind": "preference_persist"},
    {"id": "M9", "kind": "preference_topic_reset"},
    {"id": "M10", "kind": "correction_priority"},
    {"id": "M12", "kind": "sql_edit"},
    {"id": "M14", "kind": "sensitive_skip_write"},
    {"id": "M15", "kind": "clear_context"},
    {"id": "M16", "kind": "semantic_rag_enrich"},
    {"id": "M17", "kind": "episodic_recall"},
]
