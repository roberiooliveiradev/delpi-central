"""Reexport compat — implementação em ``app.domain.services``."""

from app.domain.services.chat_text_correction_prompt_supplement_service import (
    ChatTextCorrectionPromptSupplementService,
)

__all__ = ["ChatTextCorrectionPromptSupplementService"]
