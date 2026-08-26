"""SQL — lookup de usuário Protheus em SYS_USR."""

from __future__ import annotations

from app.domain.totvs.protheus_users import (
    PROTHEUS_USER_CODE_COLUMN,
    PROTHEUS_USER_EMAIL_COLUMN,
    PROTHEUS_USER_ID_COLUMN,
    PROTHEUS_USER_NAME_COLUMN,
    PROTHEUS_USER_TABLE,
)


def build_protheus_user_by_email_sql() -> str:
    return f"""
SELECT TOP 20
    RTRIM({PROTHEUS_USER_ID_COLUMN}) AS protheus_user_id,
    RTRIM({PROTHEUS_USER_CODE_COLUMN}) AS code,
    RTRIM({PROTHEUS_USER_NAME_COLUMN}) AS name,
    RTRIM({PROTHEUS_USER_EMAIL_COLUMN}) AS email
FROM {PROTHEUS_USER_TABLE} WITH (NOLOCK)
WHERE LTRIM(RTRIM(LOWER({PROTHEUS_USER_EMAIL_COLUMN}))) = LOWER(?)
"""
