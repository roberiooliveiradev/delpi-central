"""Smoke live credentials — no versioned defaults (E11.S8 / RQ11-09)."""

from __future__ import annotations

import os
import sys


def require_smoke_credentials(
    *,
    user_env: str = "SMOKE_USER",
    password_env: str = "SMOKE_PASSWORD",
) -> tuple[str, str]:
    """Return (user, password) or exit with a clear error when env is missing."""
    user = os.environ.get(user_env, "").strip()
    password = os.environ.get(password_env, "").strip()
    if not user or not password:
        print(
            f"Missing required env: {user_env} and {password_env} "
            "(versioned defaults removed in E11.S8).",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return user, password
