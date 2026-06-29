from uuid import UUID

from app.application.services.directory_user_eligibility_service import (
    DirectoryUserEligibilityService,
)
from app.application.unit_of_work import UnitOfWork


def _mask_email(email: str) -> str:
    """Mascara o email para minimizar exposição de dados (LGPD Art. 6, III)."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "***"
    return f"{masked_local}@{domain}"


class SearchDirectoryUsersUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        query: str | None,
        limit: int = 10,
        app_id: str | None = None,
        permission_code: str | None = None,
        exclude_user_id: str | None = None,
        browse: bool = False,
        mask_email: bool = True,
    ) -> list[dict]:
        normalized = (query or "").strip()

        if len(normalized) < 2 and not browse:
            return []

        safe_limit = max(1, min(limit, 20))
        exclude_id = UUID(exclude_user_id) if exclude_user_id else None
        eligibility = DirectoryUserEligibilityService(self.uow)

        fetch_size = min(max(safe_limit * 5, safe_limit + 1), 50)
        users, _ = self.uow.users.list_paginated(
            q=normalized if len(normalized) >= 2 else None,
            page=1,
            page_size=fetch_size,
            sort="name",
            direction="asc",
        )

        results: list[dict] = []

        for user in users:
            if exclude_id is not None and user.id == exclude_id:
                continue
            if not eligibility.matches(
                user,
                app_id=app_id,
                permission_code=permission_code,
            ):
                continue

            results.append(
                {
                    "id": str(user.id),
                    "name": user.name,
                    "email": _mask_email(user.email) if mask_email else user.email,
                }
            )

            if len(results) >= safe_limit:
                break

        return results
