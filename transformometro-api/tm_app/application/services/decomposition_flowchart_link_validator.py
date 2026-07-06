from __future__ import annotations

from typing import Any

from tm_app.domain.decomposition.decomposition_tree_v1 import tree_node_ids


class DecompositionFlowchartLinkValidator:
    def validate(
        self,
        *,
        tree: dict[str, Any],
        flowchart: dict[str, Any],
    ) -> dict[str, Any]:
        valid_ids = tree_node_ids(tree)
        warnings: list[dict[str, str]] = []

        for node in flowchart.get("nodes", []):
            if not isinstance(node, dict):
                continue
            meta = node.get("meta") or {}
            decomposition_id = meta.get("decomposition_id")
            if not decomposition_id:
                continue
            dec_id = str(decomposition_id)
            flow_id = str(node.get("id") or "")
            if dec_id not in valid_ids:
                warnings.append(
                    {
                        "severity": "warning",
                        "code": "invalid_decomposition_id",
                        "message": f"Nó de fluxo {flow_id} referencia decomposition_id inexistente: {dec_id}.",
                        "node_id": flow_id,
                        "decomposition_id": dec_id,
                    }
                )

        linked_tree_ids = {
            str((node.get("meta") or {}).get("decomposition_id"))
            for node in flowchart.get("nodes", [])
            if isinstance(node, dict) and (node.get("meta") or {}).get("decomposition_id")
        }
        orphan_pks = [
            node_id
            for node in tree.get("nodes", [])
            if isinstance(node, dict)
            and node.get("level") == "processo_chave"
            and not node.get("disabled")
            and str(node["id"]) not in linked_tree_ids
        ]

        for pk_id in orphan_pks[:10]:
            warnings.append(
                {
                    "severity": "info",
                    "code": "unlinked_processo_chave",
                    "message": f"Processo-chave {pk_id} sem vínculo no diagrama macro.",
                    "decomposition_id": pk_id,
                }
            )

        return {
            "valid": not any(w["severity"] == "warning" for w in warnings),
            "warnings": warnings,
        }
