"""Monta requests mínimos a partir do OpenAPI do app de teste."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from tests.support.route_smoke_mocks import smoke_ids

_IDS = smoke_ids()

_EMPTY_FLOW = {
    "format": "flowchart_v1",
    "format_version": 1,
    "nodes": [],
    "edges": [],
}
_EMPTY_TREE = {
    "format": "decomposition_tree_v1",
    "format_version": 1,
    "nodes": [],
}
_EMPTY_FLOW_OVERLAY = {
    "format": "flowchart_overlay_v1",
    "format_version": 1,
    "modo": "full_scope",
    "node_overrides": {},
    "edge_overrides": {},
    "removed_node_ids": [],
    "removed_edge_ids": [],
    "extra_nodes": [],
    "extra_edges": [],
}
_EMPTY_TREE_OVERLAY = {
    "format": "decomposition_overlay_v1",
    "format_version": 1,
    "node_overrides": {},
    "disabled_node_ids": [],
    "extra_nodes": [],
}

# Bodies mínimos por operationId (schemas/validators reais).
_BODY_OVERRIDES: dict[str, Any] = {
    "create_filial": {
        "codigo_filial": "99",
        "nome_filial": "Smoke Filial",
        "status_filial": "ativo",
    },
    "update_filial": {"nome_filial": "Smoke Filial", "status_filial": "ativo"},
    "create_setor": {
        "setor_id": "SMOKE",
        "nome_setor": "Smoke Setor",
        "status_setor": "ativo",
        "filiais": ["01"],
    },
    "update_setor": {
        "nome_setor": "Smoke Setor",
        "codigo_setor": "SMOKE",
        "status_setor": "ativo",
        "filiais": ["01"],
    },
    "create_processo": {
        "nome_processo": "Smoke Processo",
        "status_processo": "ativo",
        "familia_processo": "producao",
    },
    "update_processo": {
        "nome_processo": "Smoke Processo",
        "status_processo": "ativo",
        "familia_processo": "producao",
    },
    "create_processo_instancia": {
        "filial_id": "01",
        "setor_id": _IDS["setor_id"],
        "setor_ids": [_IDS["setor_id"]],
        "status_instancia": "ativo",
    },
    "update_instancia": {
        "setor_ids": [_IDS["setor_id"]],
        "status_instancia": "ativo",
        "rotulo_instancia": "Smoke",
    },
    "duplicate_instancia": {
        "filial_id": "01",
        "setor_id": _IDS["setor_id"],
        "setor_ids": [_IDS["setor_id"]],
    },
    "duplicate_processo": {},
    "create_revisao": {
        "processo_id": _IDS["processo_id"],
        "versao_revisao": "v1",
        "cenario_tipo": "baseline",
        "data_inicio_vigencia": "2026-01-01",
        "revisao_ativa": False,
    },
    "update_revisao": {
        "processo_id": _IDS["processo_id"],
        "versao_revisao": "v1",
        "cenario_tipo": "baseline",
        "data_inicio_vigencia": "2026-01-01",
        "revisao_ativa": False,
        "confirm_vigencia_change": True,
    },
    "duplicate_revisao": {"versao_revisao": "v2"},
    "activate_revisao": {},
    "upsert_medicao": {
        "revisao_id": _IDS["revisao_id"],
        "volume_mensal": 10,
        "tempo_medio_execucao_min": 5,
    },
    "create_investimento": {
        "revisao_id": _IDS["revisao_id"],
        "tipo_investimento": "unico",
        "descricao_item": "Capex smoke",
        "quantidade": 1,
        "valor_unitario": 1000,
        "recorrencia": "unico",
    },
    "update_investimento": {
        "tipo_investimento": "unico",
        "descricao_item": "Capex smoke",
        "quantidade": 1,
        "valor_unitario": 1000,
        "recorrencia": "unico",
    },
    "create_recurso": {
        "nome_recurso": "Recurso smoke",
        "tipo_custo": "fixo",
        "recorrencia": "mensal",
        "criterio_rateio": "igualitario",
        "base_competencia": "mensal_cheio",
        "status_recurso": "ativo",
        "escopo_recurso": "empresa",
        "valor_total_recorrente": 100,
    },
    "update_recurso": {
        "nome_recurso": "Recurso smoke",
        "tipo_custo": "fixo",
        "recorrencia": "mensal",
        "criterio_rateio": "igualitario",
        "base_competencia": "mensal_cheio",
        "status_recurso": "ativo",
        "escopo_recurso": "empresa",
        "valor_total_recorrente": 100,
    },
    "create_recurso_custo": {
        "valor_mensal": 100.0,
        "data_inicio_vigencia": "2026-01-01",
    },
    "update_recurso_custo": {
        "valor_mensal": 100.0,
        "data_inicio_vigencia": "2026-01-01",
    },
    "reajuste_recurso_custo": {
        "valor_mensal": 110.0,
        "vigente_desde": "2026-02-01",
    },
    "create_vinculo": {
        "revisao_id": _IDS["revisao_id"],
        "recurso_compartilhado_id": _IDS["recurso_id"],
        "ativo": True,
        "peso_rateio": 1.0,
    },
    "update_vinculo": {"ativo": True, "peso_rateio": 1.0},
    "put_processo_diagrama": {"conteudo": _EMPTY_FLOW},
    "put_processo_diagrama_bpmn_xml": {
        "xml": '<?xml version="1.0"?><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"></definitions>'
    },
    "post_processo_diagrama_validacao": {"conteudo": _EMPTY_FLOW},
    "put_revisao_diagrama_overlay": {"conteudo": _EMPTY_FLOW_OVERLAY},
    "put_processo_decomposicao": {"conteudo": _EMPTY_TREE},
    "put_revisao_decomposicao_overlay": {"conteudo": _EMPTY_TREE_OVERLAY},
    "post_sugerir_rascunho_decomposicao": {},
    "post_validar_vinculos_fluxo": {},
    "put_instancia_contexto": {
        "conteudo": {
            "format": "instancia_contexto_v1",
            "format_version": 1,
            "observacoes_rollout": None,
            "responsavel_local": None,
            "contato": None,
            "node_notes": {},
            "links": [],
            "meta": {},
        }
    },
    "put_instancia_diagrama_escopo": {
        "node_ids": [],
        "inherit_all": True,
        "include_boundary_edges": False,
    },
    "put_instancia_decomposicao_escopo": {
        "node_ids": [],
        "inherit_all": True,
        "include_descendants": True,
    },
    "put_revisao_matriz_impacto_esforco": {
        "modo": "auto",
        "inputs_manuais": {},
        "overrides": {},
    },
    "post_presenca": {
        "entity_type": "processo",
        "entity_id": _IDS["processo_id"],
        "section_key": "cadastro",
        "mode": "viewing",
    },
    "delete_presenca": None,  # query params
    "post_travar": {
        "entity_type": "processo",
        "entity_id": _IDS["processo_id"],
        "section_key": "cadastro",
    },
    "post_liberar": {
        "entity_type": "processo",
        "entity_id": _IDS["processo_id"],
        "section_key": "cadastro",
    },
    "recalcular_dashboard": {},
    "import_preview": {
        "mode": "merge",
        "import_format": "auto",
        "data": {"version": 1, "entities": {}},
    },
    "import_apply": {
        "mode": "merge",
        "import_format": "auto",
        "data": {"version": 1, "entities": {}},
    },
}

_QUERY_OVERRIDES: dict[str, dict[str, str]] = {
    "get_presenca": {
        "entity_type": "processo",
        "entity_id": _IDS["processo_id"],
    },
    "delete_presenca": {
        "entity_type": "processo",
        "entity_id": _IDS["processo_id"],
        "section_key": "cadastro",
    },
}


def fill_path(path: str) -> str:
    out = path
    for key, value in _IDS.items():
        out = out.replace("{" + key + "}", quote(value, safe=""))
    while "{" in out and "}" in out:
        start = out.index("{")
        end = out.index("}", start)
        out = out[:start] + "00000000-0000-0000-0000-000000000000" + out[end + 1 :]
    return out


def _resolve_ref(ref: str, components: dict[str, Any]) -> dict[str, Any]:
    name = ref.rsplit("/", 1)[-1]
    schemas = (components or {}).get("schemas") or {}
    return schemas.get(name) or {}


def _example_for_schema(schema: dict[str, Any], components: dict[str, Any], depth: int = 0) -> Any:
    if depth > 6:
        return None
    if not schema:
        return {}
    if "$ref" in schema:
        return _example_for_schema(_resolve_ref(schema["$ref"], components), components, depth + 1)
    if "anyOf" in schema or "oneOf" in schema:
        options = schema.get("anyOf") or schema.get("oneOf") or []
        for opt in options:
            if isinstance(opt, dict) and opt.get("type") != "null":
                return _example_for_schema(opt, components, depth + 1)
        return None
    if "allOf" in schema:
        merged: dict[str, Any] = {}
        for part in schema["allOf"]:
            val = _example_for_schema(part, components, depth + 1)
            if isinstance(val, dict):
                merged.update(val)
        return merged
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        props = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        out: dict[str, Any] = {}
        for key, prop in props.items():
            if required and key not in required:
                continue
            out[key] = _example_for_schema(prop, components, depth + 1)
        return out
    if schema_type == "array":
        item = _example_for_schema(schema.get("items") or {}, components, depth + 1)
        return [item] if item is not None else []
    if schema_type == "integer":
        return 1
    if schema_type == "number":
        return 1.0
    if schema_type == "boolean":
        return True
    if schema_type == "string":
        enum = schema.get("enum")
        if enum:
            return enum[0]
        fmt = schema.get("format")
        if fmt == "uuid":
            return _IDS["processo_id"]
        if fmt == "date":
            return "2026-01-01"
        return "smoke"
    return None


def body_for_operation(oid: str, op: dict[str, Any], components: dict[str, Any]) -> Any | None:
    if oid in _BODY_OVERRIDES:
        return _BODY_OVERRIDES[oid]
    rb = op.get("requestBody")
    if not rb:
        return None
    content = rb.get("content") or {}
    if "application/json" in content:
        schema = (content["application/json"] or {}).get("schema") or {}
        return _example_for_schema(schema, components)
    return None


def query_for_operation(oid: str) -> dict[str, str] | None:
    return _QUERY_OVERRIDES.get(oid)


def is_multipart(op: dict[str, Any]) -> bool:
    rb = op.get("requestBody") or {}
    content = rb.get("content") or {}
    return "multipart/form-data" in content


def looks_binary_path(path: str) -> bool:
    lower = path.lower().rstrip("/")
    if "import" in lower:
        return False
    return (
        lower.endswith("/export.csv")
        or lower.endswith("/export.xls")
        or lower.endswith("/export")
        or lower.endswith("/export/package")
        or lower.endswith("/arquivo")
    )


def load_openapi_operations(app) -> dict[str, dict[str, Any]]:
    schema = app.openapi()
    components = schema.get("components") or {}
    out: dict[str, dict[str, Any]] = {}
    for path, methods in (schema.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if not isinstance(op, dict):
                continue
            oid = str(op.get("operationId") or "").strip()
            if not oid:
                continue
            out[oid] = {
                "operationId": oid,
                "method": method.upper(),
                "path": path,
                "op": op,
                "components": components,
            }
    return out
