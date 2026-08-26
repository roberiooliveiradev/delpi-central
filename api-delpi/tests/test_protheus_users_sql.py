from app.infrastructure.persistence.totvs.protheus_users.protheus_users_sql import (
    build_protheus_user_by_email_sql,
)


def test_protheus_user_by_email_sql_uses_sys_usr_email() -> None:
    sql = build_protheus_user_by_email_sql()
    assert "SYS_USR" in sql
    assert "USR_EMAIL" in sql
    assert "LOWER(?)" in sql
    assert "TOP 20" in sql
