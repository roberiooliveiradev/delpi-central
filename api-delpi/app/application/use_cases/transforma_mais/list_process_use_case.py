# app/application/use_cases/transforma_mais/list_process_use_case.py

from typing import List

from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.domain.entities.transforma_mais.process import Process
from app.domain.ports.transforma_mais.process_query_port import ProcessQueryRepositoryPort


class ListProcessUseCase:
    """
    Caso de uso responsável por orquestrar a listagem de processos.
    """

    def __init__(self, repository: ProcessQueryRepositoryPort):
        self.repository = repository

    def execute(self, request: ProcessRequest) -> List[Process]:
        return self.repository.list_process(request)