from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class PacPlanRevisionRepository(Protocol):
    def list_plan_revisions(
        self,
        plan_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]: ...

    def get_plan_revision(self, plan_id: str, revision_number: int) -> dict[str, Any] | None: ...

    def restore_plan_revision(
        self,
        plan_id: str,
        revision_number: int,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class ListPlanRevisionsRequest:
    plan_id: str
    page: int = 1
    page_size: int = 20


class ListPlanRevisionsUseCase:
    def __init__(self, repository: PacPlanRevisionRepository) -> None:
        self._repository = repository

    def execute(self, request: ListPlanRevisionsRequest) -> dict[str, Any]:
        page = max(request.page, 1)
        page_size = min(max(request.page_size, 1), 100)
        return self._repository.list_plan_revisions(
            request.plan_id,
            page=page,
            page_size=page_size,
        )


class GetPlanRevisionUseCase:
    def __init__(self, repository: PacPlanRevisionRepository) -> None:
        self._repository = repository

    def execute(self, plan_id: str, revision_number: int) -> dict[str, Any] | None:
        if revision_number < 1:
            raise ValueError("revision_number inválido.")
        return self._repository.get_plan_revision(plan_id, revision_number)


@dataclass(frozen=True)
class RestorePlanRevisionRequest:
    plan_id: str
    revision_number: int
    updated_by: str
    updated_by_name: str | None = None
    updated_by_email: str | None = None


class RestorePlanRevisionUseCase:
    def __init__(self, repository: PacPlanRevisionRepository) -> None:
        self._repository = repository

    def execute(self, request: RestorePlanRevisionRequest) -> dict[str, Any] | None:
        if request.revision_number < 1:
            raise ValueError("revision_number inválido.")
        if not (request.updated_by or "").strip():
            raise ValueError("updated_by é obrigatório.")
        return self._repository.restore_plan_revision(
            request.plan_id,
            request.revision_number,
            updated_by=request.updated_by,
            updated_by_name=request.updated_by_name,
            updated_by_email=request.updated_by_email,
        )
