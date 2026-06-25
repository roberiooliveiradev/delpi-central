from app.domain.services.quality_action_plans.pac_quality_knowledge_graph_service import (
    PacQualityKnowledgeGraphService,
)


def test_knowledge_graph_builds_product_failure_cause_action_chain():
    graph = PacQualityKnowledgeGraphService.build(
        [
            {
                "product_code": "90110001",
                "failure_mode": "oxidação",
                "root_cause": "Tratamento superficial incorreto",
                "action_description": "Revisar banho químico",
                "plan_count": 3,
                "effective_plan_count": 2,
            }
        ]
    )

    assert graph["summary"]["node_count"] >= 4
    assert graph["summary"]["edge_count"] >= 3
    node_types = {node["type"] for node in graph["nodes"]}
    assert "product" in node_types
    assert "failure_mode" in node_types
    assert "root_cause" in node_types
    assert "effective_action" in node_types


def test_knowledge_graph_skips_rows_without_product():
    graph = PacQualityKnowledgeGraphService.build(
        [{"product_code": "", "failure_mode": "trinca", "plan_count": 1, "effective_plan_count": 0}]
    )

    assert graph["nodes"] == []
    assert graph["edges"] == []
