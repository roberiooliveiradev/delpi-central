from uuid import UUID


class RestoreAdminGuidelineVersionUseCase:
    def __init__(self, *, repository, audit_repository):
        self.repository = repository
        self.audit_repository = audit_repository

    def execute(
        self,
        guideline_id: str,
        *,
        version: int,
        user_id: str | None,
    ) -> dict:
        if int(version) <= 0:
            raise ValueError("version must be positive")

        result = self.repository.restore_version(
            guideline_id,
            version=int(version),
            user_id=user_id,
        )

        if result is None:
            raise ValueError("version not found")

        self.audit_repository.log(
            action="chat.guideline.version.restored",
            context="admin",
            user_id=self._parse_user_id(user_id),
            metadata={
                "guidelineId": result["id"],
                "version": int(version),
            },
        )

        return result

    def _parse_user_id(self, user_id: str | None):
        if not user_id:
            return None

        try:
            return UUID(str(user_id))
        except ValueError:
            return None
