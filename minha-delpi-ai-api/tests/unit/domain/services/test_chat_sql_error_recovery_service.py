from app.domain.services.chat_sql_error_recovery_service import (
    ChatSqlErrorRecoveryService,
)


SQL = """
SELECT RE.D4_OPER, OA.H8_OPER
FROM SC2010 OP
LEFT JOIN SD4010 RE ON RE.D4_OP = OP.C2_OP
LEFT JOIN SH8010 OA ON OA.H8_OP = RE.D4_OP AND OA.H8_OPER = RE.D4_OPER
"""


def test_parse_invalid_column_from_metadata():
    metadata = {
        "ok": False,
        "path": "/data/sql",
        "responsePreview": (
            '{"success": false, "message": "Invalid column name \'D4_OPER\'."}'
        ),
    }

    assert ChatSqlErrorRecoveryService.parse_invalid_column(metadata) == "D4_OPER"


def test_is_recoverable_sql_failure():
    metadata = {
        "ok": False,
        "path": "/data/sql",
        "responsePreview": "Invalid column name 'D4_OPER'.",
    }

    assert ChatSqlErrorRecoveryService.is_recoverable_sql_failure(metadata)


def test_is_recoverable_sql_failure_by_operation_id():
    metadata = {
        "ok": False,
        "path": "/internal/query",
        "operationId": "execute_readonly_sql",
        "actionId": "internal.data.execute_readonly_sql",
        "responsePreview": "Invalid column name 'D4_OPER'.",
    }

    assert ChatSqlErrorRecoveryService.is_recoverable_sql_failure(metadata)


def test_infer_table_for_qualified_column():
    table = ChatSqlErrorRecoveryService.infer_table_for_column(SQL, "D4_OPER")

    assert table == "SD4010"


def test_build_recovery_plan_replaces_invalid_column():
    schema_payload = {
        "columns": {
            "results": [
                {"X3_CAMPO": "D4_OP"},
                {"X3_CAMPO": "D4_OPERAC"},
                {"X3_CAMPO": "D4_FILIAL"},
            ]
        }
    }

    plan = ChatSqlErrorRecoveryService.build_recovery_plan(
        sql=SQL,
        invalid_column="D4_OPER",
        schema_payload=schema_payload,
    )

    assert plan is not None
    assert plan.replacement_column == "D4_OPERAC"
    assert "RE.D4_OPERAC" in plan.corrected_sql
    assert "RE.D4_OPER" not in plan.corrected_sql.upper().replace("D4_OPERAC", "")


def test_resolve_replacement_prefers_prefix_match():
    replacement = ChatSqlErrorRecoveryService.resolve_replacement_column(
        "D4_OPER",
        ["D4_OP", "D4_OPERAC", "D4_FILIAL"],
    )

    assert replacement == "D4_OPERAC"
