from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.comment_repository import CommentRepositoryPort


class ListInternalNcCommentsUseCase:
    def __init__(
        self,
        nonconformity_repository: InternalNonconformityRepositoryPort,
        comment_repository: CommentRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._comment_repository = comment_repository

    def execute(self, nonconformity_id: str):
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        nc = self._nonconformity_repository.get_by_id(nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade interna não encontrada.")

        return self._comment_repository.list_by_nc(
            nc_type="internal_nonconformity",
            nc_id=nc.id,
        )