"""Detecção de intenção para memória semântica — Playbook memória e contexto (Fase 5)."""

from __future__ import annotations

import re


class ChatSemanticMemoryIntentService:
    _DOC_QUESTION_RE = re.compile(
        r"\b(?:como\s+funciona|o\s+que\s+[eé]|documenta[cç][aã]o|manual|pol[ií]tica|"
        r"procedimento|arquitetura|rbac|autoriza[cç][aã]o|permiss[aã]o|fluxo\s+de)\b",
        re.IGNORECASE,
    )
    _PLAYBOOK_RE = re.compile(
        r"\b(?:playbook|padr[aã]o\s+do\s+playbook|mesmo\s+padr[aã]o|roteiro\s+oficial)\b",
        re.IGNORECASE,
    )
    _OPERATIONAL_BLOCK_RE = re.compile(
        r"\b(?:estoque|produto\s+\d|filial\s+\d|roteiro|consulta\s+operacional)\b",
        re.IGNORECASE,
    )

    @classmethod
    def should_enrich_semantic_retrieval(
        cls,
        message: str | None,
        *,
        snapshot: dict | None = None,
    ) -> bool:
        normalized = (message or "").strip()

        if len(normalized) < 8:
            return False

        if cls._OPERATIONAL_BLOCK_RE.search(normalized) and not cls._DOC_QUESTION_RE.search(
            normalized
        ):
            return False

        if cls._DOC_QUESTION_RE.search(normalized) or cls._PLAYBOOK_RE.search(normalized):
            return True

        snap = snapshot or {}
        state = snap.get("conversationState") or {}
        task = state.get("activeTask")

        if isinstance(task, dict):
            task_type = str(task.get("type") or "")

            if task_type in (
                "playbook_creation",
                "documentation",
                "sql_task",
            ):
                return True

        return bool(snap.get("proceduralMemoryHints"))

    @classmethod
    def intent_kind(cls, message: str | None, *, snapshot: dict | None = None) -> str | None:
        normalized = (message or "").strip()

        if cls._PLAYBOOK_RE.search(normalized):
            return "playbook"

        if cls._DOC_QUESTION_RE.search(normalized):
            return "documentation"

        snap = snapshot or {}
        task = (snap.get("conversationState") or {}).get("activeTask")

        if isinstance(task, dict):
            mapping = {
                "playbook_creation": "playbook",
                "documentation": "documentation",
                "sql_task": "technical",
            }

            return mapping.get(str(task.get("type") or ""))

        return None
