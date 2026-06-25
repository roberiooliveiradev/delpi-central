"""Runtime e repositório — visão de documentos (test hooks)."""

from __future__ import annotations

from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort


def _load_vision_runtime() -> dict:
    from app.application.services.chat_platform_runtime_access import vision_settings

    return vision_settings()


def vision_runtime() -> dict:
    """Delega a `_vision_runtime` do módulo fachada (patchável em testes)."""
    from app.application.services import chat_document_vision_service as mod

    fn = getattr(mod, "_vision_runtime", None)

    if callable(fn):
        return fn()

    return _load_vision_runtime()


def _load_default_attachment_repository() -> ChatAttachmentRepositoryPort:
    from app.composition.repository_composer import make_chat_attachment_repository

    return make_chat_attachment_repository()


def default_attachment_repository() -> ChatAttachmentRepositoryPort:
    from app.application.services import chat_document_vision_service as mod

    fn = getattr(mod, "_default_attachment_repository", None)

    if callable(fn):
        return fn()

    return _load_default_attachment_repository()
