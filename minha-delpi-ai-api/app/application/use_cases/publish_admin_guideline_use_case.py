class PublishAdminGuidelineUseCase:
    def __init__(self, *, repository, audit_repository):
        self.repository = repository
        self.audit_repository = audit_repository

    def execute(self, guideline_id: str, *, user_id: str | None) -> dict:
        result = self.repository.publish(guideline_id, user_id=user_id)

        if result is None:
            raise ValueError("guideline not found")

        self.audit_repository.create(
            action="chat.guideline.published",
            context="admin",
            user_id=user_id,
            metadata={"guidelineId": result["id"]},
        )

        return result
