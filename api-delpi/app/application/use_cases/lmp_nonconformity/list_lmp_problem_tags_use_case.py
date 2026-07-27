from __future__ import annotations

from typing import Any, Protocol


class LmpProblemTagCatalogRepository(Protocol):
    def list_problem_tag_catalog(self) -> list[dict[str, Any]]: ...


class ListLmpProblemTagsUseCase:
    def __init__(self, repository: LmpProblemTagCatalogRepository) -> None:
        self._repository = repository

    def execute(self) -> dict[str, Any]:
        items = self._repository.list_problem_tag_catalog()
        return {"items": items, "total": len(items)}
