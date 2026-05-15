class CompareAdminGuidelineVersionsUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(
        self,
        guideline_id: str,
        *,
        from_version: int,
        to_version: int,
    ) -> dict:
        if int(from_version) <= 0 or int(to_version) <= 0:
            raise ValueError("versions must be positive")

        result = self.repository.compare_versions(
            guideline_id,
            from_version=int(from_version),
            to_version=int(to_version),
        )

        if result is None:
            raise ValueError("version not found")

        return result
