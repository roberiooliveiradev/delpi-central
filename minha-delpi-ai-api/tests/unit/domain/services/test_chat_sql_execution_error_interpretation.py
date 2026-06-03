from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_error_handling_classifier import ChatErrorHandlingClassifier
from app.domain.services.chat_security_messaging_service import ChatSecurityMessagingService
from app.domain.services.chat_sql_execution_error_interpretation_service import (
    ChatSqlExecutionErrorInterpretationService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_interpret_invalid_object_with_table_name():
    error = (
        "500: ('42S02', \"[42S02] [Microsoft][ODBC Driver 18 for SQL Server]"
        "[SQL Server]Invalid object name 'sa1010'. (208) (SQLExecDirectW)\")"
    )

    interpretation = ChatSqlExecutionErrorInterpretationService.interpret(error)

    assert interpretation is not None
    assert interpretation.error_type == "sql_invalid_object"
    assert "sa1010" in interpretation.summary
    assert any("case-sensitive" in reason for reason in interpretation.reasons)


def test_has_logical_failure_on_success_false_payload():
    payload = {
        "success": False,
        "message": "500: ('42S02', \"Invalid object name 'SA1010'.\")",
    }

    assert ChatSqlExecutionErrorInterpretationService.has_logical_failure(
        payload,
        path="/data/sql",
    )


def test_extract_api_error_message_reads_nested_message():
    payload = {
        "success": False,
        "message": "erro sql",
    }

    assert ExecuteExternalActionUseCase._extract_api_error_message(payload) == "erro sql"


def test_presenter_hides_odbc_dump_for_sql_failure():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "success": False,
            "message": (
                "500: ('42S02', \"[42S02] Invalid object name 'sa1010'.\")"
            ),
        },
        path="/data/sql",
    )

    assert humanized["titulo"] == "Erro na consulta"
    assert "ODBC" not in humanized["linhas"][0]
    assert "sa1010" in humanized["linhas"][0]


def test_resolve_api_failure_for_sql_path():
    message = ChatSecurityMessagingService.resolve_api_failure(
        {
            "ok": False,
            "statusCode": 200,
            "error": "500: ('42S02', \"Invalid object name 'sa1010'.\")",
        },
        path="/data/sql",
    )

    assert "sa1010" in message
    assert "ODBC" not in message


def test_interpret_empty_body_sql_not_provided():
    error = "Empty body — SQL not provided."

    interpretation = ChatSqlExecutionErrorInterpretationService.interpret(error)

    assert interpretation is not None
    assert interpretation.error_type == "sql_missing_body"
    assert "sql" in interpretation.summary.lower()


def test_classifier_sql_missing_body_not_api_unavailable():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": False,
                "statusCode": 400,
                "path": "/data/sql",
                "actionId": "api_delpi.data.execute_readonly_sql",
                "error": "Empty body — SQL not provided.",
            },
        }
    ]

    classification = ChatErrorHandlingClassifier.classify(
        message="interprete o resultado da ultima consulta sql",
        answer="Erro na consulta",
        tool_calls=tool_calls,
    )

    assert classification is not None
    assert classification.error_type == "sql_missing_body"
    assert classification.api_failed is False


def test_classifier_sql_invalid_object_when_http_ok_but_success_false():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": False,
                "statusCode": 200,
                "path": "/data/sql",
                "actionId": "api_delpi.data.execute_readonly_sql",
                "error": (
                    "500: ('42S02', \"[42S02] Invalid object name 'sa1010'.\")"
                ),
            },
        }
    ]

    classification = ChatErrorHandlingClassifier.classify(
        message="execute select clientes",
        answer="Erro na consulta",
        tool_calls=tool_calls,
    )

    assert classification is not None
    assert classification.error_type == "sql_invalid_object"
    assert classification.api_failed is False
