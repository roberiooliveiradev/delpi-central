"""Memória procedural (playbooks e políticas) — Playbook memória e contexto (Fase 5, §21)."""

from __future__ import annotations

from typing import Any


class ChatProceduralMemoryProviderService:
    _TASK_PROCEDURES: dict[str, list[dict[str, str]]] = {
        "playbook_creation": [
            {
                "id": "editor-textos",
                "title": "Especialista em textos",
                "queryBoost": "playbook editor textos Minha DELPI",
                "kind": "playbook",
            },
            {
                "id": "memoria-contexto",
                "title": "Memória e contexto",
                "queryBoost": "playbook memória contexto sessão",
                "kind": "playbook",
            },
        ],
        "sql_task": [
            {
                "id": "sql-avancado",
                "title": "SQL avançado",
                "queryBoost": "playbook SQL schema descoberta",
                "kind": "playbook",
            },
            {
                "id": "sql-knowledge",
                "title": "Conhecimento SQL",
                "queryBoost": "sql knowledge política consulta",
                "kind": "policy",
            },
        ],
        "email_writing": [
            {
                "id": "email-writing",
                "title": "Escrita de e-mails",
                "queryBoost": "playbook e-mail tom formal",
                "kind": "playbook",
            },
        ],
        "canvas_edit": [
            {
                "id": "canvas-lousa",
                "title": "Lousa e correção",
                "queryBoost": "playbook lousa canvas correção",
                "kind": "playbook",
            },
        ],
        "documentation": [
            {
                "id": "company-knowledge",
                "title": "Conhecimento da empresa",
                "queryBoost": "documentação procedimento DELPI",
                "kind": "documentation",
            },
        ],
    }

    _INTENT_PROCEDURES: dict[str, list[dict[str, str]]] = {
        "documentation": [
            {
                "id": "rbac-docs",
                "title": "Autorização e permissões",
                "queryBoost": "RBAC autorização JWT permissão resolver",
                "kind": "documentation",
            },
        ],
        "playbook": [
            {
                "id": "playbook-search",
                "title": "Playbooks oficiais",
                "queryBoost": "playbook roadmap melhorias chat",
                "kind": "playbook",
            },
        ],
        "technical": [
            {
                "id": "architecture",
                "title": "Arquitetura do chat",
                "queryBoost": "arquitetura chat intelligence pipeline",
                "kind": "documentation",
            },
        ],
    }

    @classmethod
    def resolve_hints(
        cls,
        *,
        message: str | None = None,
        snapshot: dict | None = None,
        intent_kind: str | None = None,
    ) -> list[dict[str, str]]:
        hints: list[dict[str, str]] = []
        snap = snapshot or {}
        task = (snap.get("conversationState") or {}).get("activeTask")

        if isinstance(task, dict):
            task_type = str(task.get("type") or "")
            hints.extend(cls._TASK_PROCEDURES.get(task_type, []))

        if intent_kind:
            hints.extend(cls._INTENT_PROCEDURES.get(intent_kind, []))

        deduped: list[dict[str, str]] = []
        seen: set[str] = set()

        for item in hints:
            key = str(item.get("id") or "")

            if not key or key in seen:
                continue

            seen.add(key)
            deduped.append(dict(item))

        return deduped[:6]

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None, intent_kind: str | None) -> dict:
        result = dict(snapshot)
        hints = cls.resolve_hints(message=message, snapshot=result, intent_kind=intent_kind)

        if hints:
            result["proceduralMemoryHints"] = hints

        return result

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        hints = (snapshot or {}).get("proceduralMemoryHints") or []

        if not hints:
            return None

        lines = [
            f"- {item.get('title') or item.get('id')}: buscar «{item.get('queryBoost')}»."
            for item in hints
            if isinstance(item, dict)
        ]

        if not lines:
            return None

        return "Procedimentos sugeridos para esta tarefa:\n" + "\n".join(lines[:5])

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        hints = (snapshot or {}).get("proceduralMemoryHints") or []

        return {
            "count": len(hints),
            "ids": [str(item.get("id") or "") for item in hints if isinstance(item, dict)],
        }
