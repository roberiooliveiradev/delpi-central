"""Compile typed Copilot ops into a dependency-ordered executable plan.

Declaration order may be arbitrary; execution order follows produces/consumes
(via explicit ``as`` / ``*Ref`` or implicit current slots).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)

RESOURCE_PLAYLIST = "playlist"
RESOURCE_SLIDE = "slide"
RESOURCE_SECTION = "section"

_REF_FIELDS = {
    RESOURCE_PLAYLIST: "playlistRef",
    RESOURCE_SLIDE: "slideRef",
    RESOURCE_SECTION: "sectionRef",
}


class PlanCompileError(ValueError):
    """Plan cannot be ordered or dependencies are unsatisfiable."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class CompiledPlan:
    ordered_ops: list[dict[str, Any]]
    dependency_order: list[str]
    alias_producers: dict[str, str] = field(default_factory=dict)
    compile_digest: str = ""

    def to_meta(self) -> dict[str, Any]:
        return {
            "orderedOps": self.ordered_ops,
            "dependencyOrder": self.dependency_order,
            "aliasKeys": sorted(self.alias_producers.keys()),
            "compileDigest": self.compile_digest,
        }


def _op_name(raw: dict[str, Any]) -> str:
    return str(raw.get("op") or "").strip()


def _alias(raw: dict[str, Any]) -> str | None:
    token = str(raw.get("as") or "").strip()
    return token or None


def _ref_for(raw: dict[str, Any], resource: str) -> str | None:
    field_name = _REF_FIELDS.get(resource)
    if not field_name:
        return None
    token = str(raw.get(field_name) or "").strip()
    return token or None


def compile_presentation_plan(
    *,
    ops: list[Any],
    target: dict[str, Any] | None = None,
) -> CompiledPlan:
    """Validate, build dependency graph, topo-sort, check satisfiability."""
    typed: list[dict[str, Any]] = []
    for raw in ops or []:
        if not isinstance(raw, dict):
            raise PlanCompileError(
                "Cada op deve ser um objeto tipado com campo op.",
                code="INVALID_CHANGE",
            )
        name = _op_name(raw)
        if not name:
            raise PlanCompileError(
                "Op sem campo op.",
                code="INVALID_CHANGE",
            )
        if name not in TvCopilotContentService.allowed_ops():
            raise PlanCompileError(
                TvCopilotContentService.message("unknownOp", op=name or "?"),
                code="UNSUPPORTED_CAPABILITY",
            )
        typed.append(dict(raw))

    if not typed:
        raise PlanCompileError(
            TvCopilotContentService.message("noOps"),
            code="INVALID_CHANGE",
        )

    alias_producers: dict[str, str] = {}
    for item in typed:
        alias = _alias(item)
        if not alias:
            continue
        produces = TvCopilotContentService.operation_produces(_op_name(item))
        if not produces:
            raise PlanCompileError(
                f"Op {_op_name(item)!r} não produz recurso; não use as={alias!r}.",
                code="INVALID_REF",
            )
        if alias in alias_producers:
            raise PlanCompileError(
                f"Alias duplicado no plano: {alias!r}.",
                code="INVALID_REF",
            )
        alias_producers[alias] = produces[0]

    # Implicit resource producers (last producer of each resource kind by index).
    n = len(typed)
    # Edge: consumer index depends on producer index → producer must come first.
    # Graph for Kahn: edge producer → consumer means producer before consumer.
    indegree = [0] * n
    adjacency: list[list[int]] = [[] for _ in range(n)]

    last_producer_idx: dict[str, int] = {}
    alias_index: dict[str, int] = {}

    for idx, item in enumerate(typed):
        name = _op_name(item)
        alias = _alias(item)
        if alias:
            alias_index[alias] = idx
        for resource in TvCopilotContentService.operation_produces(name):
            last_producer_idx[resource] = idx

    # Rebuild last_producer in declaration order for implicit deps during edge build:
    # For each consumer, find producer: explicit ref alias, else nearest prior producer
    # of that resource in declaration order (stable), else target seed (no edge).

    declaration_producers: dict[str, list[int]] = {
        RESOURCE_PLAYLIST: [],
        RESOURCE_SLIDE: [],
        RESOURCE_SECTION: [],
        "block": [],
        "dataSource": [],
    }
    for idx, item in enumerate(typed):
        for resource in TvCopilotContentService.operation_produces(_op_name(item)):
            declaration_producers.setdefault(resource, []).append(idx)

    target_obj = target if isinstance(target, dict) else {}
    seeded = {
        RESOURCE_PLAYLIST: bool(str(target_obj.get("playlistId") or "").strip()),
        RESOURCE_SLIDE: bool(str(target_obj.get("slideId") or "").strip()),
        RESOURCE_SECTION: bool(str(target_obj.get("sectionId") or "").strip()),
    }

    def _add_edge(producer: int, consumer: int) -> None:
        if producer == consumer:
            return
        if consumer not in adjacency[producer]:
            adjacency[producer].append(consumer)
            indegree[consumer] += 1

    for idx, item in enumerate(typed):
        name = _op_name(item)
        for resource in TvCopilotContentService.operation_consumes(name):
            ref = _ref_for(item, resource)
            producer_idx: int | None = None
            if ref:
                if ref in alias_index:
                    producer_idx = alias_index[ref]
                    produced = alias_producers.get(ref)
                    if produced and produced != resource:
                        raise PlanCompileError(
                            f"Ref {ref!r} produz {produced!r}, não {resource!r}.",
                            code="INVALID_REF",
                        )
                elif _looks_like_uuid(ref) or ref.startswith("syn:"):
                    # External / synthetic id — no plan edge.
                    producer_idx = None
                else:
                    raise PlanCompileError(
                        f"Ref desconhecida: {ref!r} (use as de uma op produtora "
                        f"ou UUID autoritativo).",
                        code="INVALID_REF",
                    )
            else:
                # Implicit: nearest producer of resource declared before this op
                # in declaration order; if none, any producer in the plan (edge
                # from that producer) so topo-sort places create before consume.
                priors = [p for p in declaration_producers.get(resource, []) if p < idx]
                if priors:
                    producer_idx = priors[-1]
                else:
                    candidates = declaration_producers.get(resource, [])
                    if candidates:
                        producer_idx = candidates[0]
                    elif seeded.get(resource):
                        producer_idx = None
                    else:
                        raise PlanCompileError(
                            f"Op {name!r} consome {resource!r} sem produtor no "
                            f"plano e sem {resource}Id no target.",
                            code="DEPENDENCY_UNSATISFIABLE",
                        )
            if producer_idx is not None:
                _add_edge(producer_idx, idx)

    # Kahn topo-sort (stable: among zero-indegree, lowest declaration index).
    ready = [i for i in range(n) if indegree[i] == 0]
    ready.sort()
    ordered_idx: list[int] = []
    while ready:
        i = ready.pop(0)
        ordered_idx.append(i)
        for j in sorted(adjacency[i]):
            indegree[j] -= 1
            if indegree[j] == 0:
                ready.append(j)
                ready.sort()

    if len(ordered_idx) != n:
        raise PlanCompileError(
            "Ciclo de dependência entre ops do plano.",
            code="DEPENDENCY_CYCLE",
        )

    ordered_ops = [typed[i] for i in ordered_idx]
    requirements = TvCopilotContentService.plan_resource_requirements(
        ordered_ops, target_obj
    )
    if not requirements["satisfiable"]:
        details = requirements["unsatisfied"]
        raise PlanCompileError(
            "Plano com dependências não satisfeitas: "
            + ", ".join(
                f"{item['op']}→{item['resource']}" for item in details[:5]
            ),
            code="DEPENDENCY_UNSATISFIABLE",
        )

    dependency_order = [_op_name(op) for op in ordered_ops]
    digest_src = {
        "ops": ordered_ops,
        "aliases": alias_producers,
        "target": {
            "playlistId": str(target_obj.get("playlistId") or "").strip() or None,
            "slideId": str(target_obj.get("slideId") or "").strip() or None,
        },
    }
    import hashlib
    import json

    digest_payload = json.dumps(
        digest_src, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    compile_digest = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()

    return CompiledPlan(
        ordered_ops=ordered_ops,
        dependency_order=dependency_order,
        alias_producers=alias_producers,
        compile_digest=compile_digest,
    )


def _looks_like_uuid(value: str) -> bool:
    text = str(value or "").strip()
    if len(text) != 36:
        return False
    parts = text.split("-")
    if len(parts) != 5:
        return False
    return all(part.isalnum() for part in parts)
