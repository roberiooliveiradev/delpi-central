from app.application.services.chat_presentation_interactivity_service import (
    ChatPresentationInteractivityService,
)


def test_sql_tool_call_gets_sql_follow_up_chips():
    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/data/sql",
                    "sensitivity": "sql",
                    "presentation": {
                        "type": "table",
                        "title": "Produtos com estoque abaixo do mínimo",
                    },
                },
            }
        ]
    )

    labels = [item["label"] for item in suggestions]

    assert "Ver SQL" in labels
    assert "Filtrar por filial" in labels
