"""Preferências de sessão unificadas — Playbook memória e contexto (Fase 3 / §13)."""

from __future__ import annotations

import re
from typing import Any


class ChatUserPreferenceManagerService:
    _REVOKE_RE = re.compile(
        r"\b(?:n[aã]o\s+use\s+mais\b.*\bprefer|remov(?:a|e)\b.*\bprefer|"
        r"limpe?\s+as\s+prefer|esque[cç]a\s+(?:as|essa|a)\s+prefer|"
        r"volte?\s+ao\s+normal|volte?\s+ao\s+padr[aã]o|"
        r"comportamento\s+padr[aã]o)\w*\b",
        re.IGNORECASE,
    )

    _LABELS: dict[str, str] = {
        "responseFormat:table": "Respostas em tabela",
        "responseFormat:topics": "Respostas em tópicos",
        "responseFormat:text": "Respostas em texto puro",
        "toolsPolicy:on_request": "Não usar ferramentas sem pedir",
        "tone:formal": "Tom formal",
        "tone:direct": "Tom direto",
        "tone:simple": "Linguagem simples",
        "answerLength:short": "Respostas curtas",
        "finalVersionOnly:true": "Só versão final (correção)",
        "email:alwaysSubject": "E-mail sempre com assunto",
        "email:blankSignature": "Assinatura em branco",
        "email:direct": "E-mails mais diretos",
        "text:deliver_final_only": "Texto: só versão final",
        "text:tone_formal": "Texto: tom formal",
        "text:email_direct": "E-mails textuais diretos",
        "correction:deliverFinalOnly": "Correção: só versão final",
        "correction:preserveStyle": "Correção: preservar estilo",
    }

    @classmethod
    def apply_to_snapshot(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        previous_messages: list[Any] | None = None,
    ) -> dict:
        result = dict(snapshot)
        normalized = (message or "").strip().lower()

        if cls._should_revoke(normalized):
            result["userPreferences"] = {}
            result["behaviorInstructions"] = {}
            result["emailPreferences"] = {}
            result["textCorrectionPreferences"] = {}
            result["textTaskPreferences"] = {}
            result["preferencesRevoked"] = True
            return result

        if result.get("preferencesTopicChanged"):
            loaded: dict[str, Any] = {"scope": "session"}
        else:
            loaded = cls._load_from_history(previous_messages)

        merged = cls._merge_from_snapshot_layers(result, message)
        combined = cls._deep_merge_prefs(loaded, merged)
        result["userPreferences"] = combined
        result["preferencesAppliedLabels"] = cls._active_labels(combined)

        return result

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        prefs = (snapshot or {}).get("userPreferences")

        if not isinstance(prefs, dict) or not prefs:
            return None

        labels = (snapshot or {}).get("preferencesAppliedLabels") or cls._active_labels(prefs)

        if not labels:
            return None

        lines = ["Preferências ativas do usuário nesta sessão:"]

        for label in labels:
            lines.append(f"- {label}")

        return "\n".join(lines)

    @classmethod
    def build_ack_direct_answer(cls, message: str | None) -> str | None:
        if cls._should_revoke((message or "").strip().lower()):
            return (
                "Combinado. Voltei ao comportamento padrão e esqueci as preferências "
                "que você tinha definido nesta conversa."
            )

        from app.domain.services.chat_behavior_instruction_service import (
            ChatBehaviorInstructionService,
        )
        from app.domain.services.chat_text_task_preference_service import (
            ChatTextTaskPreferenceService,
        )

        detected = ChatBehaviorInstructionService.detect(message)

        if detected.get("scope") == "session":
            return cls._ack_from_behavior(detected)

        text_ack = ChatTextTaskPreferenceService.build_ack_direct_answer(message)

        if text_ack:
            return text_ack

        from app.domain.services.chat_text_correction_preference_service import (
            ChatTextCorrectionPreferenceService,
        )

        correction_prefs = ChatTextCorrectionPreferenceService.detect(message)

        if correction_prefs:
            return "Combinado. Vou seguir essa preferência de correção nesta conversa."

        from app.domain.services.chat_email_preference_service import (
            ChatEmailPreferenceService,
        )

        email_prefs = ChatEmailPreferenceService.detect(message)

        if email_prefs:
            return "Combinado. Vou seguir essa preferência de e-mail nesta conversa."

        return None

    @classmethod
    def build_context_chips(cls, snapshot: dict | None) -> list[dict[str, str]]:
        chips: list[dict[str, str]] = []
        prefs = (snapshot or {}).get("userPreferences")

        if not isinstance(prefs, dict):
            return chips

        for label in (snapshot or {}).get("preferencesAppliedLabels") or []:
            chips.append(
                {
                    "label": label[:48],
                    "kind": "sessionPreference",
                    "value": "active",
                }
            )

        return chips[:6]

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        prefs = (snapshot or {}).get("userPreferences")

        if not isinstance(prefs, dict):
            return {}

        return {
            "scope": prefs.get("scope"),
            "activeCount": len((snapshot or {}).get("preferencesAppliedLabels") or []),
            "revoked": bool((snapshot or {}).get("preferencesRevoked")),
            "topicChanged": bool((snapshot or {}).get("preferencesTopicChanged")),
        }

    @classmethod
    def _merge_from_snapshot_layers(cls, snapshot: dict, message: str | None) -> dict[str, Any]:
        from app.domain.services.chat_behavior_instruction_service import (
            ChatBehaviorInstructionService,
        )
        from app.domain.services.chat_email_preference_service import (
            ChatEmailPreferenceService,
        )
        from app.domain.services.chat_text_correction_preference_service import (
            ChatTextCorrectionPreferenceService,
        )
        from app.domain.services.chat_text_task_preference_service import (
            ChatTextTaskPreferenceService,
        )

        behavior = dict(snapshot.get("behaviorInstructions") or {})
        behavior.update(ChatBehaviorInstructionService.detect(message))

        output: dict[str, Any] = {
            "scope": behavior.get("scope") or "session",
            "behavior": {
                key: value
                for key, value in behavior.items()
                if key != "scope" and value not in (None, "", {})
            },
        }

        email = ChatEmailPreferenceService.detect(
            message,
            working_memory=snapshot,
        )

        if email:
            output["email"] = email

        text_task = ChatTextTaskPreferenceService.detect(message, working_memory=snapshot)

        if text_task:
            output["textTask"] = text_task

        correction = ChatTextCorrectionPreferenceService.detect(
            message,
            working_memory=snapshot,
        )
        snap_correction = snapshot.get("textCorrectionPreferences") or {}

        if snap_correction:
            correction = {**dict(snap_correction), **correction}

        if correction:
            output["textCorrection"] = correction

        text_task_snap = snapshot.get("textTaskPreferences") or {}

        if text_task_snap:
            output["textTask"] = {
                **dict(output.get("textTask") or {}),
                **{k: bool(v) for k, v in text_task_snap.items() if v},
            }

        email_snap = snapshot.get("emailPreferences") or {}

        if email_snap:
            output["email"] = {**dict(output.get("email") or {}), **dict(email_snap)}

        return output

    @classmethod
    def _load_from_history(cls, previous_messages: list[Any] | None) -> dict[str, Any]:
        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)

            if cls._message_role(item) != "assistant":
                continue

            snap = metadata.get("contextSnapshot")

            if not isinstance(snap, dict):
                continue

            prefs = snap.get("userPreferences")

            if isinstance(prefs, dict) and prefs:
                loaded = dict(prefs)
                cls._hydrate_legacy_layers(loaded, snap)
                return loaded

        return {"scope": "session"}

    @classmethod
    def _hydrate_legacy_layers(cls, loaded: dict, snap: dict) -> None:
        if not loaded.get("textCorrection") and snap.get("textCorrectionPreferences"):
            loaded["textCorrection"] = dict(snap["textCorrectionPreferences"])

        if not loaded.get("textTask") and snap.get("textTaskPreferences"):
            loaded["textTask"] = {
                key: bool(value) for key, value in snap["textTaskPreferences"].items() if value
            }

        if not loaded.get("email") and snap.get("emailPreferences"):
            loaded["email"] = dict(snap["emailPreferences"])

    @classmethod
    def _deep_merge_prefs(cls, base: dict, incoming: dict) -> dict:
        merged = dict(base or {})

        for key, value in (incoming or {}).items():
            if key == "scope":
                merged["scope"] = value or merged.get("scope") or "session"
                continue

            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                layer = dict(merged[key])
                layer.update({k: v for k, v in value.items() if v})
                merged[key] = layer
            elif value:
                merged[key] = value

        return merged

    @classmethod
    def _active_labels(cls, prefs: dict[str, Any]) -> list[str]:
        labels: list[str] = []
        behavior = prefs.get("behavior") or {}

        if isinstance(behavior, dict):
            if behavior.get("responseFormat") == "table":
                labels.append(cls._LABELS["responseFormat:table"])

            if behavior.get("responseFormat") == "topics":
                labels.append(cls._LABELS["responseFormat:topics"])

            if behavior.get("responseFormat") == "text":
                labels.append(cls._LABELS["responseFormat:text"])

            if behavior.get("toolsPolicy") == "on_request":
                labels.append(cls._LABELS["toolsPolicy:on_request"])

            tone = behavior.get("tone")

            if tone == "formal":
                labels.append(cls._LABELS["tone:formal"])
            elif tone == "direct":
                labels.append(cls._LABELS["tone:direct"])
            elif tone == "simple":
                labels.append(cls._LABELS["tone:simple"])

            if behavior.get("answerLength") == "short":
                labels.append(cls._LABELS["answerLength:short"])

            if behavior.get("finalVersionOnly") == "true":
                labels.append(cls._LABELS["finalVersionOnly:true"])

        email = prefs.get("email") or {}

        if isinstance(email, dict):
            if email.get("threeSubjects"):
                labels.append("E-mail: sugerir assuntos")

            if email.get("blankSignature"):
                labels.append(cls._LABELS["email:blankSignature"])

            if email.get("shortEmails"):
                labels.append("E-mails curtos")

            if email.get("formalTone"):
                labels.append(cls._LABELS["tone:formal"])

        text = prefs.get("textTask") or {}

        if isinstance(text, dict):
            if text.get("deliver_final_only"):
                labels.append(cls._LABELS["text:deliver_final_only"])

            if text.get("tone_formal"):
                labels.append(cls._LABELS["text:tone_formal"])

            if text.get("email_direct"):
                labels.append(cls._LABELS["text:email_direct"])

        correction = prefs.get("textCorrection") or {}

        if isinstance(correction, dict):
            if correction.get("deliverFinalOnly"):
                labels.append(cls._LABELS["correction:deliverFinalOnly"])

            if correction.get("preserveStyle"):
                labels.append(cls._LABELS["correction:preserveStyle"])

        return labels

    @classmethod
    def _ack_from_behavior(cls, instructions: dict[str, str]) -> str:
        parts: list[str] = []

        if instructions.get("answerLength") == "short":
            parts.append("responder de forma curta")

        tone = instructions.get("tone")

        if tone == "formal":
            parts.append("usar tom formal")
        elif tone == "direct":
            parts.append("ser mais direto")
        elif tone == "simple":
            parts.append("usar linguagem simples")

        if instructions.get("responseFormat") == "table":
            parts.append("priorizar tabelas quando couber")

        if instructions.get("responseFormat") == "topics":
            parts.append("responder em tópicos")

        if instructions.get("responseFormat") == "text":
            parts.append("responder em texto puro, sem tabelas")

        if instructions.get("toolsPolicy") == "on_request":
            parts.append("não usar ferramentas/consultas sem você pedir")

        if instructions.get("finalVersionOnly") == "true":
            parts.append("entregar só a versão final quando for correção")

        if not parts:
            return "Combinado. Vou seguir essa preferência nesta conversa."

        joined = ", ".join(parts[:-1]) + (" e " + parts[-1] if len(parts) > 1 else parts[0])

        return f"Combinado. Nesta conversa, vou {joined}."

    @classmethod
    def _should_revoke(cls, normalized: str) -> bool:
        return bool(cls._REVOKE_RE.search(normalized))

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
