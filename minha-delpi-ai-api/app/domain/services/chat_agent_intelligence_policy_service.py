"""Políticas de inteligência por agente (piloto sandbox — Onda 11.3.3)."""

from __future__ import annotations


class ChatAgentIntelligencePolicyService:
    @staticmethod
    def agent_metadata(agent_context: dict | None) -> dict:
        if not isinstance(agent_context, dict):
            return {}

        metadata = agent_context.get("metadata")

        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def native_tool_calling_pilot_enabled(cls, agent_context: dict | None) -> bool:
        metadata = cls.agent_metadata(agent_context)
        intelligence = metadata.get("intelligence")

        if isinstance(intelligence, dict) and "nativeToolCallingEnabled" in intelligence:
            return cls._bool(intelligence.get("nativeToolCallingEnabled"))

        if "nativeToolCallingEnabled" in metadata:
            return cls._bool(metadata.get("nativeToolCallingEnabled"))

        return False

    @staticmethod
    def _bool(value) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}

        return bool(value)
