"""Metadata de resposta para diagnóstico e feedback — Playbook 10."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_feedback_context_service import ChatFeedbackContextService


class ChatResponseMetadataService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        workspace_context: dict[str, Any] | None = None,
        session_id: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        snapshot = ChatFeedbackContextService.snapshot_from_assistant_metadata(
            metadata,
            session_id=session_id,
            agent_id=str(workspace.get("agentId") or "") or None,
            agent_name=str(workspace.get("agent") or workspace.get("agentName") or "") or None,
            duration_ms=duration_ms,
        )

        metadata["responseMetadata"] = snapshot

        admin_debug = metadata.get("adminDebug")

        if isinstance(admin_debug, dict):
            admin_debug.setdefault("responseQuality", {})
            quality = admin_debug["responseQuality"]

            if isinstance(quality, dict):
                quality.update(
                    {
                        "intent": snapshot.get("intent"),
                        "subIntent": snapshot.get("subIntent"),
                        "confidence": snapshot.get("confidence"),
                        "toolPath": snapshot.get("toolPath"),
                        "presentation": snapshot.get("presentationType"),
                        "durationMs": snapshot.get("durationMs"),
                        # Playbook §30 — eficiência da resposta
                        "directAnswer": snapshot.get("directAnswer"),
                        "fallback": snapshot.get("fallback"),
                        "toolSkipped": snapshot.get("toolSkipped"),
                        "ragSkipped": snapshot.get("ragSkipped"),
                        "llmSkipped": snapshot.get("llmSkipped"),
                        "simpleTurn": snapshot.get("simpleTurn"),
                    }
                )
