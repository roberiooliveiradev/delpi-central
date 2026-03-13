# app/application/use_cases/system/search_tables_by_description_use_case.py

from app.application.dto.system.system_requests import SearchTablesByDescriptionRequest
from app.domain.ports.system.system_repository_port import SystemRepositoryPort
from app.core.exceptions import BusinessLogicError


class SearchTablesByDescriptionUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: SearchTablesByDescriptionRequest) -> dict:
        result = self._repository.search_table_by_description(
            description=request.description,
            page=request.page,
            page_size=request.limit,
        )

        if not result or not result.get("data"):
            raise BusinessLogicError(
                f"Nenhuma tabela encontrada para '{request.description}'."
            )

        return {
            "success": True,
            "message": f"{len(result['data'])} resultados encontrados para '{request.description}'",
            "page": result.get("page", request.page),
            "page_size": result.get("page_size", request.limit),
            "total_records": result.get("total_records", 0),
            "total_pages": result.get("total_pages", 1),
            "results": result["data"],
        }