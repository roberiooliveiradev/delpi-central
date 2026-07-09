"""Mapeamento visual Mermaid ↔ catálogo BPMN (paridade com o MFE transformometro)."""

from __future__ import annotations

from typing import Any

from tm_app.domain.diagram.bpmn_node_catalog import NODE_TYPES, catalog_spec

BPMN_MERMAID_CLASS_PREFIX = "bpmn_"

BPMN_NODE_LABELS: dict[str, str] = {
    "start": "Início",
    "start_message": "Início — mensagem",
    "start_timer": "Início — timer",
    "start_signal": "Início — sinal",
    "start_conditional": "Início — condicional",
    "start_multiple": "Início — múltiplo",
    "start_parallel": "Início — paralelo",
    "intermediate": "Intermediário",
    "intermediate_message_catch": "Intermediário — mensagem (catch)",
    "intermediate_timer": "Intermediário — timer",
    "intermediate_signal_catch": "Intermediário — sinal (catch)",
    "intermediate_conditional": "Intermediário — condicional",
    "intermediate_link_catch": "Intermediário — link (catch)",
    "intermediate_message_throw": "Intermediário — mensagem (throw)",
    "intermediate_signal_throw": "Intermediário — sinal (throw)",
    "intermediate_link_throw": "Intermediário — link (throw)",
    "intermediate_escalation_throw": "Intermediário — escalação",
    "intermediate_compensation_throw": "Intermediário — compensação",
    "end": "Fim",
    "end_message": "Fim — mensagem",
    "end_error": "Fim — erro",
    "end_terminate": "Fim — terminate",
    "end_signal": "Fim — sinal",
    "end_escalation": "Fim — escalação",
    "end_cancel": "Fim — cancelamento",
    "end_compensation": "Fim — compensação",
    "decision": "Decisão (XOR)",
    "gateway_parallel": "Paralelo (AND)",
    "gateway_inclusive": "Inclusivo (OR)",
    "gateway_complex": "Complexo",
    "gateway_event": "Baseado em evento",
    "process": "Atividade",
    "task_user": "Tarefa — usuário",
    "task_service": "Tarefa — serviço",
    "task_manual": "Tarefa — manual",
    "task_script": "Tarefa — script",
    "task_business_rule": "Tarefa — regra de negócio",
    "task_send": "Tarefa — enviar",
    "task_receive": "Tarefa — receber",
    "subprocess": "Subprocesso",
    "call_activity": "Call activity",
    "subprocess_ad_hoc": "Subprocesso ad-hoc",
    "subprocess_transaction": "Subprocesso transação",
    "subprocess_event": "Subprocesso por evento",
    "document": "Documento",
    "data_object": "Objeto de dados",
    "data": "Armazenamento",
    "comment": "Nota",
    "group": "Grupo",
    "boundary_timer": "Borda — timer",
    "boundary_message": "Borda — mensagem",
    "boundary_error": "Borda — erro",
    "boundary_signal": "Borda — sinal",
    "boundary_escalation": "Borda — escalação",
    "boundary_compensation": "Borda — compensação",
    "boundary_cancel": "Borda — cancelamento",
    "boundary_conditional": "Borda — condicional",
}

_SHAPE_KIND_BY_FAMILY: dict[str, str] = {
    "event_start": "stadium",
    "event_end": "stadium",
    "event_intermediate_catch": "circle",
    "event_intermediate_throw": "circle",
    "gateway": "rhombus",
    "task": "rectangle",
    "activity_subprocess": "rectangle",
    "activity_call": "subroutine",
    "activity_ad_hoc": "rectangle",
    "activity_transaction": "rectangle",
    "activity_event_subprocess": "rectangle",
    "artifact_document": "subroutine",
    "artifact_data_store": "cylinder",
    "artifact_data_object": "parallelogram",
    "artifact_comment": "comment",
    "artifact_group": "rectangle",
    "boundary": "circle",
}

_CLASS_DEFS: dict[str, dict[str, str]] = {
    "bpmn_event_start": {"fill": "#ecfdf5", "stroke": "#16a34a", "color": "#15803d"},
    "bpmn_event_end": {"fill": "#fff", "stroke": "#dc2626", "color": "#b91c1c", "stroke-width": "3px"},
    "bpmn_event_intermediate": {"fill": "#fff", "stroke": "#64748b", "color": "#475569", "stroke-width": "2px"},
    "bpmn_event_intermediate_throw": {"fill": "#f8fafc", "stroke": "#ea580c", "color": "#c2410c"},
    "bpmn_gateway_exclusive": {"fill": "#fbbf24", "stroke": "#d97706", "color": "#78350f"},
    "bpmn_gateway_parallel": {"fill": "#7dd3fc", "stroke": "#0284c7", "color": "#0c4a6e"},
    "bpmn_gateway_inclusive": {"fill": "#c4b5fd", "stroke": "#7c3aed", "color": "#4c1d95"},
    "bpmn_gateway_complex": {"fill": "#fde68a", "stroke": "#ca8a04", "color": "#713f12"},
    "bpmn_gateway_event": {"fill": "#fbcfe8", "stroke": "#db2777", "color": "#831843"},
    "bpmn_task": {"fill": "#ecfdf5", "stroke": "#059669", "color": "#047857"},
    "bpmn_activity_subprocess": {"fill": "#ede9fe", "stroke": "#7c3aed", "color": "#6d28d9"},
    "bpmn_activity_call": {"fill": "#ede9fe", "stroke": "#7c3aed", "color": "#6d28d9", "stroke-width": "4px"},
    "bpmn_activity_ad_hoc": {"fill": "#f5f3ff", "stroke": "#9333ea", "color": "#7e22ce", "stroke-dasharray": "4 3"},
    "bpmn_activity_transaction": {"fill": "#d1fae5", "stroke": "#059669", "color": "#047857", "stroke-width": "4px"},
    "bpmn_activity_event_subprocess": {"fill": "#ffedd5", "stroke": "#ea580c", "color": "#c2410c", "stroke-dasharray": "6 4"},
    "bpmn_artifact_document": {"fill": "#fef3c7", "stroke": "#d97706", "color": "#b45309"},
    "bpmn_artifact_data_object": {"fill": "#f8fafc", "stroke": "#64748b", "color": "#334155"},
    "bpmn_artifact_data_store": {"fill": "#dbeafe", "stroke": "#2563eb", "color": "#1d4ed8"},
    "bpmn_artifact_comment": {"fill": "#f0f9ff", "stroke": "#089bdb", "color": "#0c4a6e", "stroke-dasharray": "5 3"},
    "bpmn_artifact_group": {"fill": "#f8fafc", "stroke": "#94a3b8", "color": "#475569", "stroke-dasharray": "8 4"},
    "bpmn_boundary": {"fill": "#fff7ed", "stroke": "#ea580c", "color": "#c2410c", "stroke-width": "3px"},
}


def _visual_group(node_type: str) -> str:
    spec = catalog_spec(node_type)
    shape = spec.get("shape", "task")
    if shape == "gateway":
        if node_type == "gateway_parallel":
            return "bpmn_gateway_parallel"
        if node_type == "gateway_inclusive":
            return "bpmn_gateway_inclusive"
        if node_type == "gateway_complex":
            return "bpmn_gateway_complex"
        if node_type == "gateway_event":
            return "bpmn_gateway_event"
        return "bpmn_gateway_exclusive"
    if shape == "event_start":
        return "bpmn_event_start"
    if shape == "event_end":
        return "bpmn_event_end"
    if shape == "event_intermediate_throw":
        return "bpmn_event_intermediate_throw"
    if shape == "event_intermediate_catch":
        return "bpmn_event_intermediate"
    if shape == "boundary":
        return "bpmn_boundary"
    if shape == "activity_call":
        return "bpmn_activity_call"
    if shape == "activity_ad_hoc":
        return "bpmn_activity_ad_hoc"
    if shape == "activity_transaction":
        return "bpmn_activity_transaction"
    if shape == "activity_event_subprocess":
        return "bpmn_activity_event_subprocess"
    if shape == "activity_subprocess":
        return "bpmn_activity_subprocess"
    if shape == "artifact_document":
        return "bpmn_artifact_document"
    if shape == "artifact_data_object":
        return "bpmn_artifact_data_object"
    if shape == "artifact_data_store":
        return "bpmn_artifact_data_store"
    if shape == "artifact_comment":
        return "bpmn_artifact_comment"
    if shape == "artifact_group":
        return "bpmn_artifact_group"
    return "bpmn_task"


def bpmn_mermaid_class_for_type(node_type: str) -> str:
    return f"{BPMN_MERMAID_CLASS_PREFIX}{node_type if node_type in NODE_TYPES else 'process'}"


def mermaid_shape_kind_for_type(node_type: str) -> str:
    spec = catalog_spec(node_type)
    return _SHAPE_KIND_BY_FAMILY.get(spec.get("shape", "task"), "rectangle")


def format_mermaid_node_line(node_type: str, mermaid_id: str, label: str) -> str:
    text = label.replace('"', "'").replace("\n", " ").strip()
    kind = mermaid_shape_kind_for_type(node_type)
    if kind == "stadium" or kind == "circle":
        body = f'{mermaid_id}(("{text}"))'
    elif kind == "rhombus":
        body = f'{mermaid_id}{{"{text}"}}'
    elif kind == "subroutine":
        body = f'{mermaid_id}[["{text}"]]'
    elif kind in {"parallelogram", "comment"}:
        body = f'{mermaid_id}[/"{text}"/]'
    elif kind == "cylinder":
        body = f'{mermaid_id}[("{text}")]'
    else:
        body = f'{mermaid_id}["{text}"]'
    return f"{body}:::{bpmn_mermaid_class_for_type(node_type)}"


def mermaid_class_def_lines(used_classes: set[str]) -> list[str]:
    groups: set[str] = set()
    for class_name in used_classes:
        if not class_name.startswith(BPMN_MERMAID_CLASS_PREFIX):
            continue
        node_type = class_name[len(BPMN_MERMAID_CLASS_PREFIX) :]
        if node_type not in NODE_TYPES:
            continue
        groups.add(_visual_group(node_type))

    lines: list[str] = []
    for group in sorted(groups):
        style = _CLASS_DEFS.get(group)
        if not style:
            continue
        parts = [f"fill:{style['fill']}", f"stroke:{style['stroke']}"]
        if style.get("color"):
            parts.append(f"color:{style['color']}")
        if style.get("stroke-width"):
            parts.append(f"stroke-width:{style['stroke-width']}")
        if style.get("stroke-dasharray"):
            parts.append(f"stroke-dasharray:{style['stroke-dasharray']}")
        lines.append(f"    classDef {group} {','.join(parts)}")
    return lines


def mermaid_edge_syntax(
    from_id: str,
    to_id: str,
    kind: str = "sequence",
    label: str | None = None,
) -> str:
    escaped = label.replace('"', "'").replace("\n", " ").strip() if label else None
    if kind == "message_flow":
        return (
            f'    {from_id} -.->|"{escaped}"| {to_id}'
            if escaped
            else f"    {from_id} -.-> {to_id}"
        )
    if kind == "association":
        return (
            f'    {from_id} -.-|"{escaped}"| {to_id}'
            if escaped
            else f"    {from_id} -.- {to_id}"
        )
    return f'    {from_id} -->|"{escaped}"| {to_id}' if escaped else f"    {from_id} --> {to_id}"


def build_bpmn_catalog_for_api() -> dict[str, Any]:
    node_types = []
    for node_type in sorted(NODE_TYPES):
        spec = catalog_spec(node_type)
        node_types.append(
            {
                "id": node_type,
                "label": BPMN_NODE_LABELS.get(node_type, node_type),
                "category": _category_for(node_type, spec),
                "shape": spec.get("shape"),
                "bpmn_tag": spec.get("bpmn_tag"),
                "bpmn_event_definition": spec.get("bpmn_event_definition"),
                "participates_in_flow": spec.get("participates_in_flow", True),
                "mermaid": {
                    "class": bpmn_mermaid_class_for_type(node_type),
                    "visual_group": _visual_group(node_type),
                    "shape_kind": mermaid_shape_kind_for_type(node_type),
                    "example": f"    {format_mermaid_node_line(node_type, 'exemplo', BPMN_NODE_LABELS.get(node_type, node_type))}",
                },
            }
        )

    return {
        "format": "transformometro_bpmn_catalog_v1",
        "format_version": 1,
        "node_types": node_types,
        "edge_kinds": [
            {"id": "sequence", "label": "Fluxo de sequência", "mermaid": "A --> B"},
            {"id": "message_flow", "label": "Fluxo de mensagem", "mermaid": "A -.-> B"},
            {"id": "association", "label": "Associação", "mermaid": "A -.- B"},
        ],
        "mermaid_conventions": {
            "header": "flowchart TD",
            "swimlane_syntax": 'subgraph lane_id ["Nome da faixa"] ... end',
            "type_class_suffix": ":::bpmn_{node_type}",
            "round_trip": "Use sempre a classe :::bpmn_<tipo> em cada nó para round-trip fiel com o canvas.",
            "source_of_truth": "flowchart_v1 (JSON) é a fonte de verdade; Mermaid é vista/exportação derivada.",
        },
        "ai_guidance": {
            "summary": (
                "Para gerar diagramas compatíveis com o Transformômetro, use flowchart TD, "
                "subgraphs para faixas, classes :::bpmn_<tipo> em todos os nós e arestas "
                "--> / -.-> / -.- conforme o tipo de conexão."
            ),
        },
    }


def _category_for(node_type: str, spec: dict[str, Any]) -> str:
    shape = spec.get("shape", "")
    if shape == "event_start":
        return "events_start"
    if shape in {"event_intermediate_catch", "event_intermediate_throw"}:
        return "events_intermediate"
    if shape == "event_end":
        return "events_end"
    if shape == "gateway":
        return "gateways"
    if shape == "task":
        return "tasks"
    if shape.startswith("activity_"):
        return "activities"
    if shape == "boundary":
        return "boundary"
    return "artifacts"
