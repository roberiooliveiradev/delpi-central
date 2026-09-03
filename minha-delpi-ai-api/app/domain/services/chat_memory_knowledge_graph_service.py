"""Grafo leve de contexto ativo — Playbook Fase 7 (nós/arestas no snapshot)."""

from __future__ import annotations

from typing import Any


class ChatMemoryKnowledgeGraphService:
    _DISPLAY_ENTITY_KEYS = frozenset({"productCode", "branch", "warehouse", "period"})

    @classmethod
    def _entity_graph_label(cls, key: str, value: str) -> str:
        token = str(value or "").strip()

        if not token:
            return ""

        if key == "productCode":
            return token

        return f"{key}={token}"

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict) -> dict:
        result = dict(snapshot)
        graph = cls.build(result)
        result["memoryGraph"] = graph
        return result

    @classmethod
    def build(cls, snapshot: dict) -> dict[str, Any]:
        nodes: list[dict[str, str]] = []
        edges: list[dict[str, str]] = []
        state = snapshot.get("conversationState") or {}
        topic = str(state.get("activeTopic") or "").strip()
        task = state.get("activeTask") if isinstance(state.get("activeTask"), dict) else {}
        entities = dict(snapshot.get("operationalFocus") or {})
        active = snapshot.get("operationalFocus") or {}

        if isinstance(active, dict):
            entities.update({k: v for k, v in active.items() if v})

        if topic:
            nodes.append({"id": "topic", "type": "topic", "label": topic[:80]})

        task_node_id = None
        task_label = ""

        if task:
            task_id = str(task.get("type") or task.get("label") or "task")
            task_node_id = f"task:{task_id}"
            task_label = str(task.get("label") or task_id).strip()[:80]
            # Evita «SQL · SQL» quando tópico e tarefa repetem o mesmo rótulo.
            if task_label and task_label.casefold() != topic.casefold():
                nodes.append(
                    {
                        "id": task_node_id,
                        "type": "task",
                        "label": task_label,
                    }
                )
            elif task_label and not topic:
                nodes.append(
                    {
                        "id": task_node_id,
                        "type": "task",
                        "label": task_label,
                    }
                )

            if topic and any(node.get("id") == task_node_id for node in nodes):
                edges.append({"from": "topic", "to": task_node_id, "kind": "active_task"})

        for key, value in entities.items():
            if key not in cls._DISPLAY_ENTITY_KEYS:
                continue

            label = cls._entity_graph_label(key, str(value))

            if not label:
                continue

            node_id = f"entity:{key}"
            nodes.append({"id": node_id, "type": "entity", "label": label})

            if task_node_id and any(node.get("id") == task_node_id for node in nodes):
                edges.append(
                    {
                        "from": task_node_id,
                        "to": node_id,
                        "kind": "uses_entity",
                    }
                )

        last_action = snapshot.get("lastAction")

        if isinstance(last_action, dict):
            action_label = cls._user_facing_action_label(last_action)

            if action_label:
                nodes.append(
                    {
                        "id": "action:last",
                        "type": "action",
                        "label": action_label[:60],
                    }
                )

                if entities.get("productCode"):
                    edges.append(
                        {
                            "from": "action:last",
                            "to": "entity:productCode",
                            "kind": "last_query",
                        }
                    )

        recall = snapshot.get("episodicRecall")

        if isinstance(recall, dict) and recall.get("episodeId"):
            nodes.append(
                {
                    "id": f"episode:{recall['episodeId']}",
                    "type": "episode",
                    "label": str(recall.get("topic") or "episódio")[:60],
                }
            )

            if topic:
                edges.append(
                    {
                        "from": "topic",
                        "to": f"episode:{recall['episodeId']}",
                        "kind": "recalled_episode",
                    }
                )

        semantic_hits = snapshot.get("semanticMemoryHits") or []

        for index, hit in enumerate(semantic_hits[:3]):
            if not isinstance(hit, dict):
                continue

            node_id = f"doc:{index}"
            nodes.append(
                {
                    "id": node_id,
                    "type": "document",
                    "label": str(hit.get("title") or "fonte")[:60],
                }
            )

            if topic:
                edges.append({"from": "topic", "to": node_id, "kind": "semantic_hit"})

        return {
            "nodes": nodes[:20],
            "edges": edges[:30],
            "nodeCount": len(nodes),
            "edgeCount": len(edges),
        }

    @classmethod
    def _user_facing_action_label(cls, last_action: dict[str, Any]) -> str:
        """Rótulo amigável para a barra de contexto — sem `external_action` técnico."""
        domain = str(
            last_action.get("apiRouteDomain")
            or last_action.get("parameterStrategy")
            or ""
        ).strip()
        result_type = str(last_action.get("resultType") or "").strip()
        operation_id = str(
            last_action.get("operationId") or last_action.get("operation_id") or ""
        ).strip()
        path = str(last_action.get("path") or "").strip()
        name = str(last_action.get("name") or "").strip()

        if domain and domain.casefold() not in {"external_action", "generic"}:
            label = domain.replace("_", " ").strip()
            if result_type and result_type.casefold() not in {label.casefold(), "table"}:
                return f"{label} · {result_type}"
            return label.capitalize() if label.isalpha() else label

        if operation_id and "sql" in operation_id.casefold():
            return "Consulta SQL"

        if path and "/sql" in path.casefold():
            return "Consulta SQL"

        if name and name.casefold() not in {"external_action", "execute_external_action"}:
            return name[:60]

        return ""

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        graph = (snapshot or {}).get("memoryGraph")

        if not isinstance(graph, dict) or not graph.get("nodes"):
            return None

        labels = [
            str(node.get("label") or "")
            for node in graph.get("nodes") or []
            if isinstance(node, dict) and node.get("label")
        ]

        if not labels:
            return None

        return "Contexto ativo (grafo): " + " · ".join(labels[:6])

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        graph = (snapshot or {}).get("memoryGraph") or {}

        return {
            "nodeCount": graph.get("nodeCount") or 0,
            "edgeCount": graph.get("edgeCount") or 0,
        }
