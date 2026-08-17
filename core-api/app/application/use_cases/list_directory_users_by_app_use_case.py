# app/application/use_cases/list_directory_users_by_app_use_case.py
"""Lista completa (paginada) de usuários com acesso a um app — não é typeahead."""

from __future__ import annotations

from typing import Any

from app.application.services.directory_user_eligibility_service import (
    DirectoryUserEligibilityService,
)
from app.application.unit_of_work import UnitOfWork


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "***"
    return f"{masked_local}@{domain}"


class ListDirectoryUsersByAppUseCase:
    """Varre o diretório com paginação real e devolve só quem tem acesso ao app."""

    MAX_PAGE_SIZE = 200
    SCAN_PAGE_SIZE = 100

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        app_id: str,
        page: int = 1,
        page_size: int = 100,
        mask_email: bool = True,
    ) -> dict[str, Any]:
        normalized_app = (app_id or "").strip()
        if not normalized_app:
            raise ValueError("app is required")

        safe_page = max(1, int(page or 1))
        safe_size = max(1, min(int(page_size or 100), self.MAX_PAGE_SIZE))
        eligibility = DirectoryUserEligibilityService(self.uow)

        matches: list[dict[str, str]] = []
        scan_page = 1
        while True:
            users, total = self.uow.users.list_paginated(
                q=None,
                page=scan_page,
                page_size=self.SCAN_PAGE_SIZE,
                sort="name",
                direction="asc",
            )
            if not users:
                break
            for user in users:
                if not eligibility.matches(user, app_id=normalized_app):
                    continue
                matches.append(
                    {
                        "id": str(user.id),
                        "name": user.name,
                        "email": _mask_email(user.email) if mask_email else user.email,
                    }
                )
            # Paginação real do universo de usuários (não typeahead page=1).
            if scan_page * self.SCAN_PAGE_SIZE >= int(total or 0):
                break
            if len(users) < self.SCAN_PAGE_SIZE:
                break
            scan_page += 1

        total_matches = len(matches)
        start = (safe_page - 1) * safe_size
        end = start + safe_size
        page_items = matches[start:end]
        return {
            "items": page_items,
            "page": safe_page,
            "pageSize": safe_size,
            "total": total_matches,
            "hasMore": end < total_matches,
        }
