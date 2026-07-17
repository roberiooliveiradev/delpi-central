"""Resolução determinística de queryName → sourceId e DAG de consultas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from tv_app.application.services.data.m_query.m_compiler import (
    MCompileRequest,
    MCompileResult,
    MQueryCompiler,
)
from tv_app.application.services.tv_dashboard_content_service import m_query_setting


@dataclass(frozen=True, slots=True)
class QueryNode:
    source_id: str
    query_name: str
    block: dict[str, Any]
    compile_result: MCompileResult | None
    dependencies: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QueryGraph:
    nodes: tuple[QueryNode, ...]
    ordered_source_ids: tuple[str, ...]
    diagnostics: tuple[dict[str, Any], ...]

    @property
    def valid(self) -> bool:
        return not any(item.get("severity") == "error" for item in self.diagnostics)

    def bindings(self) -> tuple[dict[str, Any], ...]:
        return tuple({"name": node.query_name, "sourceId": node.source_id} for node in self.nodes)


def _query_name(block: dict[str, Any]) -> str:
    binding = block.get("dataBinding")
    return str(
        block.get("queryName")
        or (binding.get("queryName") if isinstance(binding, dict) else "")
        or block.get("id")
        or ""
    ).strip()


def _diagnostic(code: str, message: str, *, source_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "severity": "error", "message": message}
    if source_id:
        payload["sourceId"] = source_id
    return payload


class MQueryDependencyService:
    def __init__(self, compiler: MQueryCompiler | None = None) -> None:
        self._compiler = compiler or MQueryCompiler()

    def resolve(
        self,
        blocks: Iterable[dict[str, Any]],
        *,
        target_step_by_source: dict[str, str | None] | None = None,
    ) -> QueryGraph:
        candidates = [
            block
            for block in blocks
            if isinstance(block, dict) and str(block.get("type") or "") == "data_source"
        ]
        diagnostics: list[dict[str, Any]] = []
        name_to_source: dict[str, str] = {}
        source_to_block: dict[str, dict[str, Any]] = {}
        for block in candidates:
            source_id = str(block.get("id") or "").strip()
            query_name = _query_name(block)
            if not source_id or not query_name:
                diagnostics.append(
                    _diagnostic(
                        "m.query_identity_required",
                        "Toda consulta precisa de id e queryName.",
                        source_id=source_id or None,
                    )
                )
                continue
            if query_name in name_to_source:
                diagnostics.append(
                    _diagnostic(
                        "m.duplicate_query_name",
                        f'A consulta "{query_name}" foi declarada mais de uma vez.',
                        source_id=source_id,
                    )
                )
            name_to_source[query_name] = source_id
            source_to_block[source_id] = block

        bindings = tuple(
            {"name": name, "sourceId": source_id} for name, source_id in name_to_source.items()
        )
        nodes: list[QueryNode] = []
        for query_name, source_id in name_to_source.items():
            block = source_to_block[source_id]
            transform = block.get("dataTransform")
            compiled: MCompileResult | None = None
            dependencies: tuple[str, ...] = ()
            if isinstance(transform, dict) and transform.get("version") == 2:
                compiled = self._compiler.compile(
                    MCompileRequest(
                        profile=str(transform.get("language") or "m-delpi-v1"),
                        script=str(transform.get("script") or ""),
                        query_bindings=bindings,
                        target_step_name=(target_step_by_source or {}).get(source_id),
                        culture=str(m_query_setting("defaultCulture", "pt-BR")),
                    )
                )
                diagnostics.extend(
                    {**item.to_dict(), "sourceId": source_id} for item in compiled.diagnostics
                )
                if query_name in compiled.referenced_queries:
                    diagnostics.append(
                        _diagnostic(
                            "m.query_cycle",
                            f'A consulta "{query_name}" referencia a si própria.',
                            source_id=source_id,
                        )
                    )
                dependencies = tuple(
                    name_to_source[name]
                    for name in compiled.referenced_queries
                    if name in name_to_source and name_to_source[name] != source_id
                )
            nodes.append(QueryNode(source_id, query_name, block, compiled, dependencies))

        dependencies_by_id = {node.source_id: set(node.dependencies) for node in nodes}
        ordered: list[str] = []
        ready = sorted(source_id for source_id, deps in dependencies_by_id.items() if not deps)
        while ready:
            source_id = ready.pop(0)
            ordered.append(source_id)
            for candidate_id, deps in dependencies_by_id.items():
                if source_id in deps:
                    deps.remove(source_id)
                    if not deps and candidate_id not in ordered and candidate_id not in ready:
                        ready.append(candidate_id)
                        ready.sort()
        unresolved = sorted(source_id for source_id in dependencies_by_id if source_id not in ordered)
        if unresolved:
            diagnostics.append(
                _diagnostic(
                    "m.query_cycle",
                    "Foi detectado um ciclo entre consultas: " + ", ".join(unresolved) + ".",
                )
            )
        return QueryGraph(tuple(nodes), tuple(ordered), tuple(diagnostics))
