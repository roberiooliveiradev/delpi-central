# app/application/use_cases/external_nc/list_external_nc_comments_use_case.py
from __future__ import annotations

from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.comment_repository import (
    CommentRepositoryPort,
)


class ListExternalNcCommentsUseCase:
    def __init__(
        self,
        repository: ExternalNonconformityRepositoryPort,
        comment_repository: CommentRepositoryPort,
    ) -> None:
        self._repository = repository
        self._comment_repository = comment_repository

    def execute(self, nonconformity_id: str):
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        entity = self._repository.get_by_id(nonconformity_id.strip())
        if entity is None:
            raise ValueError("Não conformidade externa não encontrada.")

        return self._comment_repository.list_by_nc(
            nc_type="external_nonconformity",
            nc_id=entity.id,
        )