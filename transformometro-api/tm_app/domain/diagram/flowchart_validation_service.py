from __future__ import annotations

from collections import deque
from typing import Any

from tm_app.domain.diagram.bpmn_node_catalog import (
    END_EVENT_TYPES,
    GATEWAY_TYPES,
    NON_FLOW_NODE_TYPES,
    START_EVENT_TYPES,
)


class FlowchartValidationService:
    """Validação estrutural e simulação por token (BPMN-lite) de flowchart_v1."""

    MAX_SIMULATION_STEPS = 500
    MAX_REPORTED_PATHS = 12

    def validate(self, flowchart: dict[str, Any]) -> dict[str, Any]:
        nodes = [n for n in (flowchart.get("nodes") or []) if isinstance(n, dict)]
        edges = [e for e in (flowchart.get("edges") or []) if isinstance(e, dict)]
        issues: list[dict[str, Any]] = []

        if not nodes:
            issues.append(self._issue("error", "empty_diagram", "Diagrama sem nós."))
            return {"valid": False, "issues": issues, "simulation": self._empty_simulation()}

        node_ids = {str(n["id"]) for n in nodes if n.get("id")}
        starts = [n for n in nodes if str(n.get("type")) in START_EVENT_TYPES]
        ends = {str(n["id"]) for n in nodes if str(n.get("type")) in END_EVENT_TYPES}

        if not starts:
            issues.append(
                self._issue("error", "missing_start", "Nenhum nó de início (start) encontrado.")
            )
        if not ends:
            issues.append(
                self._issue("warning", "missing_end", "Nenhum nó de fim (end) encontrado.")
            )
        if len(starts) > 1:
            issues.append(
                self._issue(
                    "warning",
                    "multiple_starts",
                    f"Múltiplos inícios ({len(starts)}); simulação parte de todos.",
                )
            )

        sequence_edges = [
            edge
            for edge in edges
            if str(edge.get("kind") or "sequence") == "sequence"
        ]
        incoming, outgoing = self._adjacency(node_ids, sequence_edges)

        for edge in edges:
            from_id = str(edge.get("from") or "")
            to_id = str(edge.get("to") or "")
            if from_id not in node_ids or to_id not in node_ids:
                issues.append(
                    self._issue(
                        "error",
                        "dangling_edge",
                        f"Aresta {edge.get('id')} referencia nó inexistente.",
                    )
                )

        reachable = self._reachable_from(starts, outgoing) if starts else set()
        for node in nodes:
            node_id = str(node.get("id"))
            if node_id not in reachable and starts:
                issues.append(
                    self._issue(
                        "warning",
                        "unreachable_node",
                        f"Nó «{node.get('label', node_id)}» não alcançável a partir do início.",
                        node_id=node_id,
                    )
                )

        for node in nodes:
            node_id = str(node.get("id"))
            node_type = str(node.get("type") or "process")
            out_count = len(outgoing.get(node_id, []))
            if node_type in GATEWAY_TYPES and out_count < 2:
                issues.append(
                    self._issue(
                        "warning",
                        "decision_needs_branches",
                        f"Gateway «{node.get('label', node_id)}» deveria ter ao menos 2 saídas.",
                        node_id=node_id,
                    )
                )
            if (
                node_type not in END_EVENT_TYPES
                and node_type not in NON_FLOW_NODE_TYPES
                and out_count == 0
                and node_id in reachable
            ):
                issues.append(
                    self._issue(
                        "warning",
                        "dead_end",
                        f"Nó «{node.get('label', node_id)}» não possui saídas.",
                        node_id=node_id,
                    )
                )

        simulation = self._simulate_tokens(nodes, sequence_edges, starts, ends, outgoing)
        if simulation.get("stuck_paths"):
            issues.append(
                self._issue(
                    "warning",
                    "simulation_stuck",
                    f"{len(simulation['stuck_paths'])} caminho(s) de simulação não chegam ao fim.",
                )
            )

        has_error = any(item["severity"] == "error" for item in issues)
        return {
            "valid": not has_error,
            "issues": issues,
            "simulation": simulation,
        }

    def _adjacency(
        self, node_ids: set[str], edges: list[dict[str, Any]]
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        incoming: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        for edge in edges:
            from_id = str(edge.get("from") or "")
            to_id = str(edge.get("to") or "")
            if from_id in node_ids and to_id in node_ids:
                outgoing[from_id].append(to_id)
                incoming[to_id].append(from_id)
        return incoming, outgoing

    def _reachable_from(
        self, starts: list[dict[str, Any]], outgoing: dict[str, list[str]]
    ) -> set[str]:
        seen: set[str] = set()
        queue = deque(str(n["id"]) for n in starts if n.get("id"))
        while queue:
            node_id = queue.popleft()
            if node_id in seen:
                continue
            seen.add(node_id)
            for target in outgoing.get(node_id, []):
                if target not in seen:
                    queue.append(target)
        return seen

    def _simulate_tokens(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        starts: list[dict[str, Any]],
        ends: set[str],
        outgoing: dict[str, list[str]],
    ) -> dict[str, Any]:
        if not starts:
            return self._empty_simulation()

        labels = {str(n["id"]): str(n.get("label") or n["id"]) for n in nodes if n.get("id")}
        edge_labels: dict[tuple[str, str], str] = {}
        for edge in edges:
            from_id = str(edge.get("from") or "")
            to_id = str(edge.get("to") or "")
            label = edge.get("label")
            if label:
                edge_labels[(from_id, to_id)] = str(label)

        completed: list[dict[str, Any]] = []
        stuck: list[dict[str, Any]] = []

        for start in starts:
            start_id = str(start.get("id") or "")
            if not start_id:
                continue
            path = [start_id]
            current = start_id
            steps = 0
            visited_stack: set[tuple[str, ...]] = set()

            while steps < self.MAX_SIMULATION_STEPS:
                steps += 1
                if current in ends:
                    completed.append(
                        {
                            "path_ids": list(path),
                            "path_labels": [labels.get(node_id, node_id) for node_id in path],
                            "steps": len(path) - 1,
                        }
                    )
                    break

                next_nodes = outgoing.get(current, [])
                if not next_nodes:
                    stuck.append(
                        {
                            "path_ids": list(path),
                            "path_labels": [labels.get(node_id, node_id) for node_id in path],
                            "reason": "sem_saida",
                        }
                    )
                    break

                signature = tuple(path[-8:])
                if signature in visited_stack:
                    stuck.append(
                        {
                            "path_ids": list(path),
                            "path_labels": [labels.get(node_id, node_id) for node_id in path],
                            "reason": "ciclo",
                        }
                    )
                    break
                visited_stack.add(signature)

                if len(next_nodes) > 1:
                    for branch in next_nodes[1 : self.MAX_REPORTED_PATHS]:
                        branch_path = path + [branch]
                        if branch in ends:
                            completed.append(
                                {
                                    "path_ids": branch_path,
                                    "path_labels": [
                                        labels.get(node_id, node_id) for node_id in branch_path
                                    ],
                                    "steps": len(branch_path) - 1,
                                    "branch": edge_labels.get((current, branch)),
                                }
                            )

                current = next_nodes[0]
                path.append(current)

        return {
            "completed_paths": completed[: self.MAX_REPORTED_PATHS],
            "stuck_paths": stuck[: self.MAX_REPORTED_PATHS],
            "completed_count": len(completed),
            "stuck_count": len(stuck),
        }

    @staticmethod
    def _empty_simulation() -> dict[str, Any]:
        return {
            "completed_paths": [],
            "stuck_paths": [],
            "completed_count": 0,
            "stuck_count": 0,
        }

    @staticmethod
    def _issue(
        severity: str,
        code: str,
        message: str,
        *,
        node_id: str | None = None,
    ) -> dict[str, Any]:
        item: dict[str, Any] = {"severity": severity, "code": code, "message": message}
        if node_id:
            item["node_id"] = node_id
        return item
