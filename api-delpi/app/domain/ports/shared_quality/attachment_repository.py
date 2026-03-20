# app/domain/ports/shared_quality/attachment_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.shared_quality.nonconformity_attachment import (
    NonconformityAttachment,
)


class AttachmentRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        attachment: NonconformityAttachment,
    ) -> NonconformityAttachment:
        raise NotImplementedError