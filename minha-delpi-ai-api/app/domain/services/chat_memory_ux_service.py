"""UX de memória de sessão — Playbook memória e contexto (Fase 8 / §35–36)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_manual_context_pin_service import ChatManualContextPinService
from app.domain.services.chat_user_preference_manager_service import (
    ChatUserPreferenceManagerService,
)


class ChatMemoryUxService:
    _INTROSPECT_RE = re.compile(
        r"\b(?:quais\s+informa[cç][oõ]es|qual\s+contexto|o\s+que\s+voc[eê]\s+est[aá]\s+usando|"
        r"mem[oó]ria\s+usada|contexto\s+ativo|o\s+que\s+lembra)\b",
        re.IGNORECASE,
    )
    _EDIT_PREF_RE = re.compile(
        r"\b(?:editar|alterar|mudar)\b.{0,20}\bprefer",
        re.IGNORECASE,
    )

    @classmethod
    def is_memory_introspection(cls, message: str | None) -> bool:
        return bool(cls._INTROSPECT_RE.search((message or "").strip()))

    @classmethod
    def is_edit_preference_request(cls, message: str | None) -> bool:
        return bool(cls._EDIT_PREF_RE.search((message or "").strip()))

    @classmethod
    def build_for_metadata(cls, snapshot: dict) -> dict[str, Any]:
        chips = cls.build_context_chips(snapshot)
        summary = cls.build_context_bar_summary(snapshot, chips=chips)

        return {
            "contextBar": {
                "items": chips,
                "summary": summary,
                "preferenceHint": cls.build_preference_hint(snapshot, chips=chips),
            },
            "usage": cls.build_usage_view(snapshot),
            "pinnedKinds": (
                ["context"] if any(chip.get("kind") == "context" for chip in chips) else []
            ),
        }

    @classmethod
    def build_context_chips(cls, snapshot: dict | None) -> list[dict[str, str]]:
        if not snapshot:
            return []

        chips: list[dict[str, str]] = []
        state = snapshot.get("conversationState") or {}
        topic = str(state.get("activeTopic") or "").strip()

        if topic:
            chips.append(
                {
                    "label": f"Assunto: {topic[:48]}",
                    "kind": "topic",
                    "value": topic[:120],
                }
            )

        task = state.get("activeTask")

        if isinstance(task, dict):
            label = str(task.get("label") or task.get("type") or "tarefa").strip()
            objective = str(task.get("objective") or label).strip()[:80]

            if objective:
                chips.append(
                    {
                        "label": f"Tarefa: {objective[:40]}",
                        "kind": "task",
                        "value": str(task.get("type") or label),
                    }
                )

        attachment = snapshot.get("lastAttachment")

        if isinstance(attachment, dict) and attachment.get("name"):
            name = str(attachment["name"]).strip()[:40]
            chips.append(
                {
                    "label": f"Anexo: {name}",
                    "kind": "attachment",
                    "value": str(attachment.get("id") or name),
                }
            )

        canvas = snapshot.get("canvas") or {}

        if isinstance(canvas, dict) and canvas.get("active") and not any(
            chip.get("kind") == "canvas" for chip in chips
        ):
            title = str(canvas.get("title") or "Lousa").strip()
            chips.append(
                {
                    "label": f"Lousa: {title[:40]}",
                    "kind": "canvas",
                    "value": "active",
                }
            )

        return chips

    @classmethod
    def build_context_bar_summary(
        cls,
        snapshot: dict | None,
        *,
        chips: list[dict[str, str]] | None = None,
    ) -> str | None:
        snap = snapshot or {}
        graph = snap.get("memoryGraph") or {}

        if isinstance(graph, dict) and graph.get("nodes"):
            labels = [
                str(node.get("label") or "")
                for node in graph.get("nodes") or []
                if isinstance(node, dict) and node.get("label")
            ]

            if labels:
                return " · ".join(labels[:6])

        items = chips if chips is not None else cls.build_context_chips(snap)

        if items:
            return " · ".join(chip["label"] for chip in items[:8])

        return None

    @classmethod
    def build_preference_hint(
        cls,
        snapshot: dict | None,
        *,
        chips: list[dict[str, str]] | None = None,
    ) -> str | None:
        snap = snapshot or {}
        labels = snap.get("preferencesAppliedLabels") or []

        if labels:
            return "Preferências: " + ", ".join(str(label) for label in labels[:4])

        if chips is None:
            chips = []

        pref_chip = next(
            (
                chip
                for chip in chips
                if chip.get("kind") in ("preference", "tone", "format", "email", "textCorrection")
            ),
            None,
        )

        if pref_chip:
            return f"Preferência ativa: {pref_chip.get('label')}"

        return None

    @classmethod
    def build_usage_view(cls, snapshot: dict | None) -> dict[str, Any]:
        snap = snapshot or {}
        state = snap.get("conversationState") or {}
        entities = dict(snap.get("lastEntities") or {})
        active = snap.get("activeEntities") or {}

        if isinstance(active, dict):
            entities.update({k: v for k, v in active.items() if v})

        preferences: list[str] = list(snap.get("preferencesAppliedLabels") or [])

        if not preferences:
            prefs = snap.get("userPreferences") or {}

            if isinstance(prefs, dict):
                preferences = ChatUserPreferenceManagerService._active_labels(prefs)

        semantic: list[dict[str, str]] = []

        for hit in snap.get("semanticMemoryHits") or []:
            if not isinstance(hit, dict):
                continue

            title = str(hit.get("title") or "").strip()

            if title:
                semantic.append({"title": title, "snippet": str(hit.get("snippet") or "")[:160]})

        episodic = snap.get("episodicMemory") or []
        recall = snap.get("episodicRecall")

        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        # Tudo que o chat capturou (produto/filial/etc.) é apresentado como
        # contexto unificado — sem uma seção separada de "entidades".
        user_context = ChatUserContextItemService.merge_context_labels(
            ChatUserContextItemService.entity_context_labels(entities),
            ChatUserContextItemService.items_for_usage_view(snap),
        )

        return {
            "layers": (snap.get("memoryContextDebug") or {}).get("layers") or [],
            "topic": state.get("activeTopic"),
            "task": (state.get("activeTask") or {}).get("label")
            if isinstance(state.get("activeTask"), dict)
            else None,
            "entities": entities,
            "preferences": preferences,
            "resolvedReferences": [
                str(item.get("text") or "")
                for item in (snap.get("resolvedReferences") or [])
                if isinstance(item, dict) and item.get("text")
            ][:6],
            "semanticHits": semantic[:4],
            "episodicCount": len(episodic) if isinstance(episodic, list) else 0,
            "episodicRecall": str(recall.get("summary") or "")[:200] if isinstance(recall, dict) else None,
            "userContextItems": user_context,
            "writeGated": bool(snap.get("memoryWriteGated")),
            "pinnable": ["product", "branch", "warehouse"],
        }

    @classmethod
    def build_direct_answer(cls, message: str | None, snapshot: dict | None) -> str | None:
        if not cls.is_memory_introspection(message):
            return None

        usage = cls.build_usage_view(snapshot)
        lines: list[str] = ["Nesta conversa estou usando:"]

        if usage.get("topic"):
            lines.append(f"- Assunto: {usage['topic']}.")

        if usage.get("task"):
            lines.append(f"- Tarefa: {usage['task']}.")

        for label in usage.get("userContextItems") or []:
            lines.append(f"- Contexto: {label}.")

        for pref in usage.get("preferences") or []:
            lines.append(f"- Preferência: {pref}.")

        for ref in usage.get("resolvedReferences") or []:
            lines.append(f"- Referência resolvida: {ref}.")

        if usage.get("semanticHits"):
            titles = ", ".join(
                str(item.get("title") or "") for item in usage["semanticHits"][:3]
            )
            lines.append(f"- Documentação/playbooks: {titles}.")

        if usage.get("episodicRecall"):
            lines.append(f"- Episódio recuperado: {usage['episodicRecall']}.")

        if len(lines) == 1:
            return (
                "Ainda não há contexto persistente nesta sessão além da mensagem atual. "
                "Você pode fixar produto, filial ou armazém com o botão + na barra de contexto."
            )

        if usage.get("writeGated"):
            lines.append(
                "- Observação: dados sensíveis detectados; não estou gravando novas memórias neste turno."
            )

        return "\n".join(lines)

    @classmethod
    def build_edit_preference_direct_answer(cls, message: str | None) -> str | None:
        if not cls.is_edit_preference_request(message):
            return None

        return (
            "Para alterar uma preferência, diga o que mudou — por exemplo: "
            "«daqui pra frente respostas curtas» ou «não use mais preferências de e-mail». "
            "Você também pode remover um chip na barra de contexto ou limpar tudo com o botão ×."
        )

    @classmethod
    def merge_pinned_overlay_chips(
        cls,
        overlay: dict | None,
        turn_chips: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        pinned = ChatManualContextPinService.chips_from_overlay(overlay)
        merged: dict[str, dict[str, str]] = {}

        for chip in pinned + turn_chips:
            if not isinstance(chip, dict):
                continue

            key = f"{chip.get('kind')}:{chip.get('value')}"
            merged[key] = {
                "label": str(chip.get("label") or ""),
                "kind": str(chip.get("kind") or ""),
                "value": str(chip.get("value") or ""),
            }

        return list(merged.values())
