from uuid import UUID

class ArchiveAdminGuidelineUseCase:
    def __init__(self, *, repository, audit_repository):
        self.repository = repository
        self.audit_repository = audit_repository

    def execute(self, guideline_id: str, *, user_id: str | None) -> dict:
        result = self.repository.archive(guideline_id, user_id=user_id)

        if result is None:
            raise ValueError("guideline not found")

        self.audit_repository.log(
            action="chat.guideline.archived",
            context="admin",
            user_id=_parse_user_id(user_id),
            metadata={"guidelineId": result["id"]},
        )

        return result


def _parse_user_id(user_id: str | None):
    if not user_id:
        return None

    try:
        return UUID(str(user_id))
    except ValueError:
        return None
