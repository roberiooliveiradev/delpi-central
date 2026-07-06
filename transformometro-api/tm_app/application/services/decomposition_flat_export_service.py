from __future__ import annotations

import csv
import io
from typing import Any


class DecompositionFlatExportService:
    """Gera linhas flat no formato planilha legado (Departamento × Processo-chave × Sub-tarefas)."""

    COLUMNS = (
        "departamento",
        "macroprocesso",
        "num_processo_chave",
        "processo_chave",
        "num_sub_tarefa",
        "sub_tarefas",
        "node_id",
        "highlight",
    )

    def build_rows(
        self,
        *,
        tree: dict[str, Any],
        macroprocesso: str,
        departamento: str = "",
        overlay: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        nodes = [n for n in tree.get("nodes", []) if isinstance(n, dict) and not n.get("disabled")]
        by_id = {str(n["id"]): n for n in nodes if n.get("id")}
        overrides = (overlay or {}).get("node_overrides") or {}

        def merged_label(node_id: str, field: str = "label") -> str:
            node = by_id.get(node_id, {})
            override = overrides.get(node_id) or {}
            value = override.get(field) if field in override else node.get(field)
            return str(value or "").strip()

        def highlight_of(node_id: str) -> str:
            override = overrides.get(node_id) or {}
            return str(override.get("highlight") or by_id.get(node_id, {}).get("highlight") or "")

        processos_chave = sorted(
            [n for n in nodes if n.get("level") == "processo_chave"],
            key=lambda n: int(n.get("ordem") or 0),
        )

        rows: list[dict[str, str]] = []
        for pk in processos_chave:
            pk_id = str(pk["id"])
            leaves = self._collect_export_leaves(pk_id, nodes)
            if not leaves:
                rows.append(
                    self._row(
                        departamento=departamento,
                        macroprocesso=macroprocesso,
                        pk=pk,
                        leaf=None,
                        pk_id=pk_id,
                        merged_label=merged_label,
                        highlight_of=highlight_of,
                    )
                )
                continue
            for leaf in leaves:
                rows.append(
                    self._row(
                        departamento=departamento,
                        macroprocesso=macroprocesso,
                        pk=pk,
                        leaf=leaf,
                        pk_id=pk_id,
                        merged_label=merged_label,
                        highlight_of=highlight_of,
                    )
                )
        return rows

    def to_csv(self, rows: list[dict[str, str]]) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(self.COLUMNS), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return buffer.getvalue()

    def _collect_export_leaves(
        self,
        pk_id: str,
        nodes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        children = [n for n in nodes if str(n.get("parent_id") or "") == pk_id]
        sub_tarefas = [n for n in children if n.get("level") == "sub_tarefa"]
        if sub_tarefas:
            return sorted(sub_tarefas, key=lambda n: int(n.get("ordem") or 0))
        tarefas = [n for n in children if n.get("level") == "tarefa"]
        leaves: list[dict[str, Any]] = []
        for tarefa in sorted(tarefas, key=lambda n: int(n.get("ordem") or 0)):
            t_id = str(tarefa["id"])
            st_children = [
                n
                for n in nodes
                if str(n.get("parent_id") or "") == t_id and n.get("level") == "sub_tarefa"
            ]
            if st_children:
                leaves.extend(sorted(st_children, key=lambda n: int(n.get("ordem") or 0)))
            else:
                leaves.append(tarefa)
        return leaves

    def _row(
        self,
        *,
        departamento: str,
        macroprocesso: str,
        pk: dict[str, Any],
        leaf: dict[str, Any] | None,
        pk_id: str,
        merged_label,
        highlight_of,
    ) -> dict[str, str]:
        leaf_id = str(leaf["id"]) if leaf else pk_id
        return {
            "departamento": departamento,
            "macroprocesso": macroprocesso,
            "num_processo_chave": str(pk.get("ordem") or ""),
            "processo_chave": merged_label(pk_id),
            "num_sub_tarefa": str(leaf.get("ordem") or "") if leaf and leaf.get("level") != "processo_chave" else "",
            "sub_tarefas": merged_label(leaf_id) if leaf else merged_label(pk_id),
            "node_id": leaf_id,
            "highlight": highlight_of(leaf_id),
        }
