from __future__ import annotations

from typing import Any, Protocol


class LmpNonconformityUpdateRepository(Protocol):
    def update_record(
        self,
        *,
        record_id: str,
        status: str,
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
        updated_by: str | None = None,
    ) -> dict[str, Any] | None: ...


class UpdateLmpNonconformityUseCase:
    def __init__(self, repository: LmpNonconformityUpdateRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        record_id: str,
        status: str,
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
        updated_by: str | None = None,
    ) -> dict[str, Any] | None:
        return self._repository.update_record(
            record_id=record_id,
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
            products=products if products is not None else [],
            problem_tags=problem_tags if problem_tags is not None else [],
            updated_by=updated_by,
        )
