"""Reexport compat — implementação em ``app.domain.services``."""

from app.domain.services.chat_action_label_service import ChatActionLabelService

__all__ = ["ChatActionLabelService"]
