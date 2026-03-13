# app/application/use_cases/system/search_columns_by_description_use_case.py

from app.application.dto.system.system_requests import SearchColumnsByDescriptionRequest
from app.domain.ports.system.system_repository_port import SystemRepositoryPort
from app.core.exceptions import BusinessLogicError


class SearchColumnsByDescriptionUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: SearchColumnsByDescriptionRequest) -> dict:
        result = self._repository.search_columns_by_description(
            description=request.description,
            page=request.page,
            page_size=request.limit,
        )

        if not result or not result.get("data"):
            raise BusinessLogicError(
                f"Nenhuma coluna encontrada para a descrição '{request.description}'."
            )

        return {
            "success": True,
            "message": f"{len(result['data'])} colunas encontradas para '{request.description}'",
            "page": result.get("page", request.page),
            "page_size": result.get("page_size", request.limit),
            "total_records": result.get("total_records", 0),
            "total_pages": result.get("total_pages", 1),
            "results": result["data"],
        }