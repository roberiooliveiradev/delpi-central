# app/application/use_cases/lmp/get_lmp_use_case.py
from typing import List
from app.application.models.page import Page
from app.domain.entities.lmp.lmp import LMP
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort


class GetLMPUseCase:

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetLMPRequest) -> dict:
        return self._repository.get_lmp(request).to_dict()


