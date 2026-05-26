class ListConsentsUseCase:
    def __init__(self, uow):
        self._uow = uow

    def execute(self, user_id: str) -> list:
        from uuid import UUID
        return self._uow.consents.list_by_user(UUID(user_id))
