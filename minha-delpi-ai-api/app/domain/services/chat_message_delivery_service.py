"""Estado de entrega da mensagem assistant (persistência vs. efeito visual no cliente)."""

from __future__ import annotations

from typing import Any


class ChatMessageDeliveryService:
    STATUS_GENERATING = "generating"
    STATUS_READY = "ready"
    STATUS_FAILED = "failed"

    @classmethod
    def get_status(cls, metadata: dict | None) -> str | None:
        if not isinstance(metadata, dict):
            return None

        delivery = metadata.get("delivery")

        if not isinstance(delivery, dict):
            return None

        status = delivery.get("status")

        return str(status).strip() if status else None

    @classmethod
    def is_generating(cls, metadata: dict | None) -> bool:
        return cls.get_status(metadata) == cls.STATUS_GENERATING

    @classmethod
    def patch_metadata(
        cls,
        metadata: dict | None,
        *,
        status: str,
        playback_pending: bool | None = None,
    ) -> dict:
        merged = dict(metadata or {})
        delivery = dict(merged.get("delivery") or {})
        delivery["status"] = status

        if playback_pending is not None:
            delivery["playbackPending"] = bool(playback_pending)

        merged["delivery"] = delivery

        return merged

    @classmethod
    def generating_metadata(cls, base: dict | None = None) -> dict:
        return cls.patch_metadata(
            base,
            status=cls.STATUS_GENERATING,
            playback_pending=False,
        )

    @classmethod
    def ready_metadata(cls, base: dict | None = None, *, playback_pending: bool = True) -> dict:
        return cls.patch_metadata(
            base,
            status=cls.STATUS_READY,
            playback_pending=playback_pending,
        )

    @classmethod
    def session_has_pending_assistant(cls, messages: list[Any]) -> bool:
        if not messages:
            return False

        last = messages[-1]

        role = getattr(last, "role", None) or (last.get("role") if isinstance(last, dict) else None)

        if role == "assistant":
            metadata = getattr(last, "metadata", None) or (
                last.get("metadata") if isinstance(last, dict) else None
            )
            return cls.is_generating(metadata)

        if role == "user":
            return True

        return False

    @classmethod
    def client_response_metadata_keys(cls) -> tuple[str, ...]:
        return (
            "drawingAnalysisMode",
            "drawingAnalysis",
            "drawingAnalysisExport",
            "drawingAnalysisMetrics",
            "directResponse",
            "intelligence",
            "interactivity",
            "presentationFollowUpSuggestions",
        )

    @classmethod
    def client_metadata_for_response(cls, assistant_metadata: dict | None) -> dict | None:
        if not isinstance(assistant_metadata, dict):
            return None

        filtered = {
            key: assistant_metadata[key]
            for key in cls.client_response_metadata_keys()
            if assistant_metadata.get(key) is not None
        }

        return filtered or None
