# app/domain/ports/shared_quality/comment_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.shared_quality.nonconformity_comment import (
    NonconformityComment,
)


class CommentRepositoryPort(ABC):
    @abstractmethod
    def create(self, comment: NonconformityComment) -> NonconformityComment:
        raise NotImplementedError

    @abstractmethod
    def list_by_nc(self, *, nc_type: str, nc_id: str) -> list[NonconformityComment]:
        raise NotImplementedError