ALLOWED_CATEGORIES = {"behavior", "rag", "tools", "safety"}
ALLOWED_STATUSES = {"draft", "active", "archived"}


class SaveAdminGuidelineUseCase:
    def __init__(self, *, repository, audit_repository):
        self.repository = repository
        self.audit_repository = audit_repository

    def execute(self, payload: dict, *, user_id: str | None) -> dict:
        title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip()
        content = str(payload.get("content") or "").strip()
        category = str(payload.get("category") or "behavior").strip()
        status = str(payload.get("status") or "draft").strip()
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

        if not title:
            raise ValueError("title is required")

        if not content:
            raise ValueError("content is required")

        if category not in ALLOWED_CATEGORIES:
            raise ValueError("invalid category")

        if status not in ALLOWED_STATUSES:
            raise ValueError("invalid status")

        result = self.repository.create_or_update(
            guideline_id=payload.get("id"),
            title=title,
            description=description,
            content=content,
            category=category,
            status=status,
            metadata=metadata,
            user_id=user_id,
        )

        self.audit_repository.create(
            action="chat.guideline.saved",
            context="admin",
            user_id=user_id,
            metadata={"guidelineId": result["id"], "status": result["status"]},
        )

        return result
