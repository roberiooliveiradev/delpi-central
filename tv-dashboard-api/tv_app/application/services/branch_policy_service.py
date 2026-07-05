from __future__ import annotations

from typing import Any

from tv_app.application.services.tv_dashboard_content_service import (
    allowed_branches,
    branch_rejection_message,
)


def validate_native_branch(config: dict[str, Any] | None) -> None:
    cfg = config or {}
    branch = cfg.get("branch")
    if branch is None or branch == "":
        return
    branch_code = str(branch).strip()
    if not branch_code:
        return
    allowed = allowed_branches()
    if not allowed:
        return
    if branch_code not in allowed:
        raise ValueError(branch_rejection_message())
