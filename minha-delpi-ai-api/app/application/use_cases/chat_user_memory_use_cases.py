from uuid import UUID

_VALID_ACTIONS = {"forget": "forgotten", "restore": "active"}


def _as_uuid(value) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


class ListUserMemoryItemsUseCase:
    def __init__(self, repository=None):
        if repository is None:
            from app.infrastructure.persistence.postgres_memory_item_repository import (
                PostgresMemoryItemRepository,
            )

            repository = PostgresMemoryItemRepository()

        self.repository = repository

    def execute(
        self,
        *,
        user_id: str | None = None,
        scope: str | None = None,
        type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        items, total = self.repository.list_items(
            user_id=_as_uuid(user_id),
            scope=scope,
            type=type,
            status=status,
            limit=limit,
            offset=offset,
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}


class ReviewUserMemoryItemUseCase:
    """Esquecer/restaurar uma memória (playbook §43 — permitir apagar memória)."""

    def __init__(self, repository=None):
        if repository is None:
            from app.infrastructure.persistence.postgres_memory_item_repository import (
                PostgresMemoryItemRepository,
            )

            repository = PostgresMemoryItemRepository()

        self.repository = repository

    def execute(self, *, item_id: int, action: str, reviewer_id: str | None = None) -> dict:
        normalized = (action or "").strip().lower()

        if normalized not in _VALID_ACTIONS:
            raise ValueError("action must be one of: forget, restore")

        result = self.repository.set_status(
            item_id,
            status=_VALID_ACTIONS[normalized],
            reviewer_id=_as_uuid(reviewer_id),
        )

        if result is None:
            raise ValueError("memory item not found")

        return result
