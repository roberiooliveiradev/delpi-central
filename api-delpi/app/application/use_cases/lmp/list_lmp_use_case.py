# app/application/use_cases/lmp/list_lmp_use_case.py
from typing import List
from app.application.models.page import Page
from app.domain.entities.lmp.lmp import LMP
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort


class ListLMPUseCase:

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: ListLMPRequest) -> Page[LMP]:

        rows: List[LMP] = self._repository.list_lmps(request)

        total = len(rows)

        if not request.page_size:
            return Page(
                items=rows,
                total=total,
                page=1,
                page_size=total
            )

        page = request.page or 1

        start = (page - 1) * request.page_size
        end = start + request.page_size

        paginated = rows[start:end]

        return Page(
            items=paginated,
            total=total,
            page=page,
            page_size=request.page_size
        )