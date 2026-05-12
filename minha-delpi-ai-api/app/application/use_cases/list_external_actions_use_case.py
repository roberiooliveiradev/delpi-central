class ListExternalActionsUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, provider_key: str | None = None) -> list[dict]:
        return self.repository.list_actions(provider_key=provider_key)
