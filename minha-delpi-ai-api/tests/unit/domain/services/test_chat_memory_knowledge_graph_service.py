from app.domain.services.chat_memory_knowledge_graph_service import (
    ChatMemoryKnowledgeGraphService,
)
from app.domain.services.chat_memory_ux_service import ChatMemoryUxService


def test_context_bar_omits_technical_external_action_and_dedupes_sql_topic():
    snapshot = {
        "conversationState": {
            "activeTopic": "SQL",
            "activeTask": {"type": "sql_task", "label": "SQL"},
        },
        "operationalFocus": {"productCode": "1008"},
        "lastAction": {
            "name": "external_action",
            "path": "/data/sql",
            "operationId": "execute_readonly_sql",
            "apiRouteDomain": "sql",
            "resultType": "table",
        },
    }

    graph = ChatMemoryKnowledgeGraphService.build(snapshot)
    labels = [str(node.get("label") or "") for node in graph.get("nodes") or []]

    assert "external_action" not in labels
    assert labels.count("SQL") == 1
    assert "1008" in labels
    assert any("sql" in label.casefold() for label in labels)

    summary = ChatMemoryUxService.build_context_bar_summary(
        {**snapshot, "memoryGraph": graph}
    )

    assert summary
    assert "external_action" not in summary
    assert summary.count("SQL") == 1
