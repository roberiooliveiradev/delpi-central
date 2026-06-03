from app.domain.services.chat_error_handling_classifier import ChatErrorHandlingClassifier


def test_sql_syntax_error_not_classified_as_api_unavailable():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": False,
                "statusCode": 400,
                "path": "/data/sql",
                "actionId": "api_delpi.data.execute_readonly_sql",
                "error": (
                    "500: ('42000', \"[Microsoft][ODBC Driver 18 for SQL Server]"
                    "[SQL Server]Incorrect syntax near '='. (102) (SQLExecDirectW)\")"
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
    assert classification.error_type == "sql_syntax_error"
    assert classification.api_failed is False


def test_sql_invalid_object_not_classified_as_api_unavailable():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": False,
                "statusCode": 400,
                "path": "/data/sql",
                "actionId": "api_delpi.data.execute_readonly_sql",
                "error": (
                    "500: ('42S02', \"[42S02] [Microsoft][ODBC Driver 18 for SQL Server]"
                    "[SQL Server]Invalid object name 'sa1010'. (208) (SQLExecDirectW)\")"
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
