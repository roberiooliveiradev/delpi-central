"""Estado estruturado da sessão — Playbook memória e contexto (Fase 1)."""

from __future__ import annotations

import re
import uuid
from typing import Any


class ChatConversationStateService:
    _TOPIC_CHANGE_RE = re.compile(
        r"\b(?:agora\s+vamos|novo\s+assunto|mudando\s+de|deixe\s+isso|vamos\s+falar\s+de|"
        r"trocar\s+de\s+assunto|outro\s+assunto|agora\s+fa[cç]a\s+um\b|agora\s+crie\s+um\b)\b",
        re.IGNORECASE,
    )
    _CONTINUATION_RE = re.compile(
        r"^\s*(?:siga|continue|prossiga|pr[oó]ximo|pr[oó]xima|seguinte)\s*[.!?]?\s*$",
        re.IGNORECASE,
    )
    _RESUME_RE = re.compile(
        r"\b(?:volte\s+ao|retome|continue\s+o|volte\s+para|siga\s+de\s+onde)\b",
        re.IGNORECASE,
    )
    _CORRECTION_RE = re.compile(
        r"\b(?:n[aã]o\s+[eé]|nao\s+eh)\s+(.+?)\s*,\s*[eé]\s+(.+)$",
        re.IGNORECASE,
    )
    _TASK_PATTERNS: tuple[tuple[str, str, str], ...] = (
        (r"\bplaybook\b", "playbook_creation", "playbook"),
        (r"\b(?:escreva|crie|monte)\s+.*\be-?mail\b", "email_writing", "e-mail"),
        (r"\b(?:ata|reuni[aã]o)\b", "minutes_writing", "ata"),
        (r"\b(?:consulta\s+)?sql\b|\bsql\s+avan", "sql_task", "SQL"),
        (r"\b(?:corrij|revise).*\blousa\b", "canvas_edit", "lousa"),
        (r"\b(?:documenta|manual|procedimento)\b", "documentation", "documentação"),
    )
    _SENSITIVE_RE = re.compile(
        r"\b(?:senha|password|token|api[_-]?key|cpf|cart[aã]o|chave\s+privada)\b",
        re.IGNORECASE,
    )

    @classmethod
    def load_from_previous_messages(cls, previous_messages: list[Any] | None) -> dict[str, Any]:
        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)

            if cls._message_role(item) != "assistant":
                continue

            snapshot = metadata.get("contextSnapshot")

            if not isinstance(snapshot, dict):
                continue

            state = snapshot.get("conversationState")

            if isinstance(state, dict):
                return dict(state)

        return {}

    @classmethod
    def apply_pre_turn(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        previous_messages: list[Any] | None = None,
    ) -> dict:
        result = dict(snapshot)
        normalized = (message or "").strip()
        lowered = normalized.lower()
        state = dict(result.get("conversationState") or cls.load_from_previous_messages(previous_messages))

        if cls._is_clear_context(lowered):
            result["conversationState"] = cls._empty_state()
            result["continuationRequested"] = False
            return result

        if cls._SENSITIVE_RE.search(normalized):
            state["skipMemoryWrite"] = True

        if cls._TOPIC_CHANGE_RE.search(normalized):
            state = cls._pause_current_task(state)
            state["activeTopic"] = cls._infer_topic_from_message(normalized)
            state["activeTask"] = cls._detect_task(normalized)
            result["preferencesTopicChanged"] = True

        elif cls._RESUME_RE.search(normalized):
            resumed = cls._try_resume_task(state, normalized)

            if resumed:
                state = resumed

        elif cls._CONTINUATION_RE.match(normalized):
            result["continuationRequested"] = True

            if not state.get("activeTask"):
                result["continuationMissingContext"] = True
            else:
                state["lastContinuationAt"] = "pre_turn"

        else:
            correction = cls._detect_correction(normalized)

            if correction:
                corrections = list(state.get("userCorrections") or [])
                corrections.append(correction)
                state["userCorrections"] = corrections[-8:]

            task = cls._detect_task(normalized)

            if task:
                if state.get("activeTask") and state["activeTask"].get("type") != task.get("type"):
                    state = cls._pause_current_task(state)

                state["activeTask"] = task
                state["activeTopic"] = state.get("activeTopic") or task.get("label")

        result["conversationState"] = state
        return result

    @classmethod
    def apply_post_turn(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        answer: str | None = None,
    ) -> dict:
        result = dict(snapshot)
        state = dict(result.get("conversationState") or {})
        snippet = (answer or "").strip()

        if snippet and not state.get("skipMemoryWrite"):
            state["lastUsefulAssistantSnippet"] = snippet[:400]

        task = state.get("activeTask")

        if isinstance(task, dict) and snippet:
            task = dict(task)
            task["lastProgressAt"] = "post_turn"

            if task.get("type") == "playbook_creation" and len(snippet) > 200:
                task["status"] = "in_progress"
                task["currentVersion"] = int(task.get("currentVersion") or 0) + 1

            state["activeTask"] = task

        result["conversationState"] = state
        return result

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        state = (snapshot or {}).get("conversationState")

        if not isinstance(state, dict):
            return None

        lines: list[str] = []

        topic = str(state.get("activeTopic") or "").strip()

        if topic:
            lines.append(f"- Assunto ativo: {topic}.")

        task = state.get("activeTask")

        if isinstance(task, dict):
            objective = str(task.get("objective") or task.get("label") or "").strip()
            status = str(task.get("status") or "in_progress").strip()

            if objective:
                lines.append(f"- Tarefa em andamento ({status}): {objective}.")

            constraints = task.get("constraints") or []

            if constraints:
                lines.append(f"- Restrições da tarefa: {', '.join(str(c) for c in constraints[:6])}.")

        corrections = state.get("userCorrections") or []

        if corrections:
            last = corrections[-1]

            if isinstance(last, dict) and last.get("content"):
                lines.append(f"- Correção do usuário (prioridade alta): {last['content']}.")

        if (snapshot or {}).get("continuationRequested") and isinstance(task, dict):
            lines.append(
                "- O usuário pediu «siga» ou «próximo»: continue a tarefa ativa sem reiniciar do zero."
            )

        if not lines:
            return None

        return "Estado da conversa:\n" + "\n".join(lines)

    @classmethod
    def build_continuation_direct_answer(cls, snapshot: dict | None) -> str | None:
        if not (snapshot or {}).get("continuationMissingContext"):
            return None

        return (
            "Não encontrei uma sequência ou tarefa ativa nesta conversa. "
            "Diga qual assunto devo continuar — por exemplo o playbook, o e-mail ou a consulta SQL."
        )

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        state = (snapshot or {}).get("conversationState")

        if not isinstance(state, dict):
            return {}

        task = state.get("activeTask") if isinstance(state.get("activeTask"), dict) else {}

        return {
            "activeTopic": state.get("activeTopic"),
            "activeTaskType": task.get("type"),
            "activeTaskStatus": task.get("status"),
            "taskStackSize": len(state.get("taskStack") or []),
            "correctionsCount": len(state.get("userCorrections") or []),
            "continuationRequested": bool((snapshot or {}).get("continuationRequested")),
        }

    @classmethod
    def _empty_state(cls) -> dict[str, Any]:
        return {
            "activeTopic": None,
            "activeTask": None,
            "taskStack": [],
            "userCorrections": [],
        }

    @classmethod
    def _pause_current_task(cls, state: dict) -> dict:
        state = dict(state)
        current = state.get("activeTask")

        if isinstance(current, dict):
            paused = dict(current)
            paused["status"] = "paused"
            stack = list(state.get("taskStack") or [])
            stack.append(paused)
            state["taskStack"] = stack[-5:]

        state["activeTask"] = None
        return state

    @classmethod
    def _try_resume_task(cls, state: dict, message: str) -> dict | None:
        stack = list(state.get("taskStack") or [])
        lowered = message.lower()

        for index in range(len(stack) - 1, -1, -1):
            task = stack[index]

            if not isinstance(task, dict):
                continue

            label = str(task.get("label") or "").lower()
            task_type = str(task.get("type") or "").lower()

            if label and label in lowered:
                state = dict(state)
                state["activeTask"] = dict(task)
                state["activeTask"]["status"] = "in_progress"
                state["activeTopic"] = task.get("label")
                stack.pop(index)
                state["taskStack"] = stack
                return state

            if "sql" in lowered and "sql" in task_type:
                state = dict(state)
                state["activeTask"] = dict(task)
                state["activeTask"]["status"] = "in_progress"
                state["taskStack"] = stack[:index] + stack[index + 1 :]
                return state

            if "e-mail" in lowered or "email" in lowered:
                if "email" in task_type:
                    state = dict(state)
                    state["activeTask"] = dict(task)
                    state["activeTask"]["status"] = "in_progress"
                    state["taskStack"] = stack[:index] + stack[index + 1 :]
                    return state

        return None

    @classmethod
    def _detect_task(cls, message: str) -> dict[str, Any] | None:
        normalized = (message or "").strip()

        for pattern, task_type, label in cls._TASK_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                return {
                    "taskId": str(uuid.uuid4()),
                    "type": task_type,
                    "label": label,
                    "objective": normalized[:200],
                    "status": "in_progress",
                    "currentVersion": 0,
                    "constraints": cls._extract_constraints(normalized),
                    "pending": [],
                }

        return None

    @classmethod
    def _infer_topic_from_message(cls, message: str) -> str:
        task = cls._detect_task(message)

        if task:
            return str(task.get("label") or "tarefa")

        trimmed = message.strip()[:80]

        return trimmed or "novo assunto"

    @classmethod
    def _extract_constraints(cls, message: str) -> list[str]:
        constraints: list[str] = []
        lowered = message.lower()

        if "sem totvs" in lowered or "sem protheus" in lowered:
            constraints.append("sem TOTVS/Protheus")

        if "genérico" in lowered or "generico" in lowered:
            constraints.append("genérico")

        if "txt" in lowered and "copiar" in lowered:
            constraints.append("formato txt para copiar")

        return constraints

    @classmethod
    def _detect_correction(cls, message: str) -> dict[str, Any] | None:
        match = cls._CORRECTION_RE.search(message.strip())

        if not match:
            return None

        wrong = match.group(1).strip()
        right = match.group(2).strip()

        if not wrong or not right:
            return None

        return {
            "type": "correction",
            "content": f"Usar «{right}» em vez de «{wrong}».",
            "priority": "high",
            "wrong": wrong,
            "right": right,
        }

    @staticmethod
    def _is_clear_context(lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in (
                "limpe o contexto",
                "limpar o contexto",
                "começar do zero",
                "comecar do zero",
            )
        )

    @staticmethod
    def _message_metadata(item: Any) -> dict:
        if isinstance(item, dict):
            meta = item.get("metadata")

            return meta if isinstance(meta, dict) else {}

        meta = getattr(item, "metadata", None)

        return meta if isinstance(meta, dict) else {}

    @staticmethod
    def _message_role(item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("role") or "").strip().lower()

        return str(getattr(item, "role", "") or "").strip().lower()
