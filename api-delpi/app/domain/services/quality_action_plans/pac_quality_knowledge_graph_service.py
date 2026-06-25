"""Grafo produto ↔ modo falha ↔ causa ↔ ação eficaz (Onda 6.5)."""

from __future__ import annotations

from typing import Any

from app.domain.services.quality_action_plans.pac_knowledge_graph_content_service import (
    PacKnowledgeGraphContentService,
)


class PacQualityKnowledgeGraphService:
    @classmethod
    def build(cls, rows: list[dict[str, Any]]) -> dict[str, Any]:
        max_nodes = PacKnowledgeGraphContentService.limit_int("maxNodes", 120)
        max_edges = PacKnowledgeGraphContentService.limit_int("maxEdges", 240)

        nodes: dict[str, dict[str, Any]] = {}
        edges: dict[str, dict[str, Any]] = {}

        def _node(node_id: str, *, node_type: str, label: str) -> None:
            if node_id not in nodes and len(nodes) < max_nodes:
                nodes[node_id] = {"id": node_id, "type": node_type, "label": label}

        def _edge(
            edge_id: str,
            *,
            source: str,
            target: str,
            edge_type: str,
            weight: int,
            effective_count: int,
        ) -> None:
            if edge_id in edges or len(edges) >= max_edges:
                return
            edges[edge_id] = {
                "id": edge_id,
                "source": source,
                "target": target,
                "type": edge_type,
                "plan_count": weight,
                "effective_plan_count": effective_count,
            }

        for row in rows:
            product = str(row.get("product_code") or "").strip()
            failure = str(row.get("failure_mode") or "").strip()
            root_cause = str(row.get("root_cause") or "").strip()
            action = str(row.get("action_description") or "").strip()
            plan_count = int(row.get("plan_count") or 0)
            effective_count = int(row.get("effective_plan_count") or 0)

            if not product or plan_count <= 0:
                continue

            product_id = f"product:{product}"
            _node(product_id, node_type="product", label=product)

            if failure:
                failure_id = f"failure:{failure.lower()}"
                _node(failure_id, node_type="failure_mode", label=failure)
                _edge(
                    f"{product_id}->{failure_id}",
                    source=product_id,
                    target=failure_id,
                    edge_type="product_to_failure_mode",
                    weight=plan_count,
                    effective_count=effective_count,
                )

                if root_cause:
                    cause_id = f"cause:{root_cause.lower()[:120]}"
                    _node(cause_id, node_type="root_cause", label=root_cause[:120])
                    _edge(
                        f"{failure_id}->{cause_id}",
                        source=failure_id,
                        target=cause_id,
                        edge_type="failure_mode_to_root_cause",
                        weight=plan_count,
                        effective_count=effective_count,
                    )

                    if action:
                        action_id = f"action:{action.lower()[:120]}"
                        _node(action_id, node_type="effective_action", label=action[:120])
                        _edge(
                            f"{cause_id}->{action_id}",
                            source=cause_id,
                            target=action_id,
                            edge_type="root_cause_to_effective_action",
                            weight=plan_count,
                            effective_count=effective_count,
                        )

        return {
            "nodes": list(nodes.values()),
            "edges": list(edges.values()),
            "summary": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "source_row_count": len(rows),
            },
        }
