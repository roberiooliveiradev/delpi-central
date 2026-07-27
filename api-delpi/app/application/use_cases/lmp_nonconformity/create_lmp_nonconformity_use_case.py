from __future__ import annotations

from typing import Any, Protocol


class LmpNonconformityCreateRepository(Protocol):
    def create_record(
        self,
        *,
        status: str = "open",
        sale_number: str | None = None,
        customer_name: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        problem_tags: list[str] | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]: ...


class CreateLmpNonconformityUseCase:
    def __init__(self, repository: LmpNonconformityCreateRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        status: str = "open",
        sale_number: str | None = None,
        customer_name: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        problem_tags: list[str] | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        return self._repository.create_record(
            status=status,
            sale_number=sale_number,
            customer_name=customer_name,
            launch_date=launch_date,
            last_revision_date=last_revision_date,
            executed_by=executed_by,
            released_by=released_by,
            defect_description=defect_description,
            corrective_actions=corrective_actions,
            technical_opinion=technical_opinion,
            products=products,
            problem_tags=problem_tags,
            created_by=created_by,
        )
