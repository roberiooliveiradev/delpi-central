class ListAdminGuidelineVersionsUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, guideline_id: str) -> list[dict]:
        return self.repository.list_versions(guideline_id)
