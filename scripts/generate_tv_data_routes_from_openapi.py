#!/usr/bin/env python3
"""Gera catálogo TV (tv_data_routes.json) a partir do OpenAPI baseline api-delpi.

Fonte de verdade (como o registry operacional do chat):
  api-delpi openapi → openapi_baseline.json (v2: parameters + xDelpi)
  → generate --write → tv_data_routes.json
  → overlays em tv_data_route_overlays.json (TV-only)

Campos do OpenAPI (sempre regenerados / mergeados):
  operationId, path, httpMethod, paramSchema, paramStrategy (inferido),
  metaShape (x-delpi.shape quando houver)

Overlays TV (preservados / arquivo overlays):
  valueFields, seriesField, tableFields, tvConstraints, fixedQueryParams,
  defaultParams, label, description, category, allowedDisplayModes,
  paramStrategy (se explícito), ajustes pontuais de paramSchema
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_BASELINE_PATH = ROOT / "api-delpi" / "app" / "content" / "openapi_baseline.json"
TV_ROUTES_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"
TV_OVERLAYS_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_route_overlays.json"

# Overlay / preservação manual (não vêm do OpenAPI puro).
OVERLAY_KEYS = frozenset(
    {
        "valueFields",
        "seriesField",
        "defaultParams",
        "tvConstraints",
        "allowedDisplayModes",
        "paramStrategy",
        "fixedQueryParams",
        "tableFields",
        "description",
        "label",
        "category",
        "paramSchema",  # merge profundo com schema OpenAPI
    }
)

TAG_TO_CATEGORY: dict[str, str] = {
    "Agendamento": "scheduling",
    "Auditoria 5S": "quality",
    "Clientes": "commercial",
    "Comercial": "commercial",
    "Compras operacionais": "supplies",
    "Cultura DELPI": "strategic",
    "Dashboard": "system",
    "Engenharia": "engineering",
    "Financeiro": "financial",
    "Health": "system",
    "Inspeções de Entrada": "quality",
    "Kaizen — cadastro": "quality",
    "PAC Qualidade — inteligência": "quality",
    "PAC Qualidade — padrões de solução": "quality",
    "PAC Qualidade — planos de ação": "quality",
    "Pedidos de Venda em Aberto": "commercial",
    "Produção": "production",
    "Produção operacional": "production",
    "Propostas Comerciais": "commercial",
    "Qualidade": "quality",
    "Qualidade — PPM": "quality",
    "Quality Labels": "quality",
    "Quality Labels (público)": "quality",
    "Recursos Humanos": "hr",
    "Suprimentos": "supplies",
    "products": "products",
    "sales": "commercial",
    "system": "system",
}

PATH_SEGMENT_TO_CATEGORY: dict[str, str] = {
    "commercial": "commercial",
    "production": "production",
    "quality": "quality",
    "supplies": "supplies",
    "products": "products",
    "financial": "financial",
    "financeiro": "financial",
    "hr": "hr",
    "scheduling": "scheduling",
    "engineering": "engineering",
    "engenharia": "engineering",
    "strategic": "strategic",
    "system": "system",
    "dashboard": "system",
}

PARAM_LABELS_PT: dict[str, str] = {
    "active": "Ativo",
    "adjustment_percent": "Ajuste (%)",
    "area_id": "Área",
    "audit_status": "Status da auditoria",
    "branch": "Filial",
    "branch_code": "Código da filial",
    "branches": "Filiais",
    "catalog_version": "Versão do catálogo",
    "centroCusto": "Centro de custo",
    "code": "Código",
    "code_exact": "Código exato",
    "codigo": "Código",
    "codigoOperador": "Código do operador",
    "codigo_peca": "Código da peça",
    "competence": "Competência",
    "cost_center": "Centro de custo",
    "customer": "Cliente",
    "customer_name": "Nome do cliente",
    "customer_reference": "Referência do cliente",
    "customer_segment": "Segmento",
    "dataFim": "Data fim",
    "dataInicio": "Data início",
    "data_final": "Data final",
    "data_inicial": "Data inicial",
    "date": "Data",
    "date_end": "Data fim",
    "date_from": "Data início",
    "date_start": "Data início",
    "date_to": "Data fim",
    "department": "Departamento",
    "department_id": "Departamento",
    "descricao": "Descrição",
    "descricao_peca": "Descrição da peça",
    "description": "Descrição",
    "details_limit": "Limite de detalhes",
    "direction": "Direção",
    "efficiency_bands": "Faixas de eficiência",
    "employee": "Colaborador",
    "eventTypes": "Tipos de evento",
    "evidence_type": "Tipo de evidência",
    "failure_mode": "Modo de falha",
    "file_kind": "Tipo de arquivo",
    "filename": "Nome do arquivo",
    "filial": "Filial",
    "filial_id": "ID da filial",
    "finished_product_code": "Código do produto acabado",
    "format": "Formato",
    "from": "De",
    "granularity": "Granularidade",
    "group_by": "Agrupar por",
    "group_code": "Código do grupo",
    "has_revision": "Com revisão",
    "has_variant": "Com variante",
    "history_limit": "Limite do histórico",
    "id": "ID",
    "include_completed": "Incluir concluídos",
    "include_qtd_pi": "Incluir quantidade PI",
    "include_test_products": "Incluir produtos de teste",
    "incluir_bloqueados": "Incluir bloqueados",
    "inspection_id": "Inspeção",
    "inspector": "Inspetor",
    "invoice_number": "Número da nota",
    "issue_date_end": "Data de emissão (fim)",
    "issue_date_start": "Data de emissão (início)",
    "item_code": "Código do item",
    "legacy": "Modo legado",
    "limit": "Limite",
    "linked_sort_by": "Ordenar vínculos por",
    "linked_sort_dir": "Direção da ordenação dos vínculos",
    "listing_type": "Tipo de listagem",
    "location": "Localização",
    "loss_type": "Tipo de perda",
    "lot": "Lote",
    "max_depth": "Profundidade máxima",
    "max_size_bytes": "Tamanho máximo (bytes)",
    "min_plans": "Mínimo de planos",
    "min_size_bytes": "Tamanho mínimo (bytes)",
    "modified_from": "Modificado a partir de",
    "modified_to": "Modificado até",
    "months": "Meses",
    "name": "Nome",
    "name_process": "Nome do processo",
    "nonconformity_scope": "Escopo de NC",
    "offset": "Deslocamento",
    "op": "Ordem de produção",
    "operation_id": "Operação",
    "operator_code": "Código do operador",
    "orderBy": "Ordenar por",
    "orderDir": "Direção da ordenação",
    "overdue_only": "Somente atrasados",
    "owner_user_id": "Responsável",
    "page": "Página",
    "pageSize": "Tamanho da página",
    "page_size": "Tamanho da página",
    "periodDays": "Período (dias)",
    "plan_id": "Plano",
    "price_source": "Fonte de preço",
    "problem_category": "Categoria do problema",
    "product": "Produto",
    "product_code": "Código do produto",
    "product_group": "Grupo de produto",
    "product_prefix": "Prefixo do produto",
    "product_type": "Tipo de produto",
    "production_order": "Ordem de produção",
    "q": "Busca",
    "raw_material_code": "Código da matéria-prima",
    "recurso": "Recurso",
    "reference_date": "Data de referência",
    "resource_id": "Recurso",
    "result": "Resultado",
    "revision": "Revisão",
    "root_cause_category": "Categoria da causa raiz",
    "savings_type": "Tipo de economia",
    "search": "Busca",
    "section": "Seção",
    "sector_name": "Setor",
    "senso_order": "Ordem do senso",
    "severity": "Severidade",
    "shift": "Turno",
    "sort": "Ordenação",
    "sort_by": "Ordenar por",
    "sort_dir": "Direção da ordenação",
    "status": "Status",
    "status_ok_only": "Somente status OK",
    "stock_method": "Método de estoque",
    "store": "Loja",
    "start_date": "Data início",
    "end_date": "Data fim",
    "strict_idd_period": "Período IDD estrito",
    "summary_only": "Somente resumo",
    "supplier": "Fornecedor",
    "supplier_code": "Código do fornecedor",
    "supplier_store": "Loja do fornecedor",
    "template_key": "Chave do template",
    "title": "Título",
    "tm": "TM",
    "to": "Até",
    "top_limit": "Limite do ranking",
    "top_n": "Top N",
    "type": "Tipo",
    "view": "Visão",
    "warehouse": "Armazém",
    "work_center": "Centro de trabalho",
}

# Explicações curtas no inspetor (DeckField hint) — complementam o OpenAPI.
PARAM_HINTS_PT: dict[str, str] = {
    "active": "Filtra apenas registros ativos (sim) ou inativos (não).",
    "adjustment_percent": "Percentual de ajuste aplicado no cálculo.",
    "area_id": "Identificador da área (ex.: auditoria 5S).",
    "audit_status": "Status da auditoria no fluxo (aberta, concluída etc.).",
    "branch": "Código da filial no Protheus (ex.: 01 ou 02). Vazio usa o consolidado da rota, quando permitido.",
    "branch_code": "Código da filial no Protheus (ex.: 01 ou 02).",
    "branches": "Lista de filiais (CSV). Vazio = todas as filiais permitidas.",
    "catalog_version": "Versão do catálogo a consultar.",
    "centroCusto": "Código do centro de custo no Protheus.",
    "code": "Código do registro a filtrar.",
    "code_exact": "Busca pelo código exato (sem correspondência parcial).",
    "codigo": "Código do registro a filtrar.",
    "codigoOperador": "Código do operador no Protheus.",
    "codigo_peca": "Código da peça no cadastro de ferramentas.",
    "competence": "Competência no formato AAAA-MM (mês de referência).",
    "cost_center": "Código do centro de custo no Protheus.",
    "customer": "Código ou identificador do cliente.",
    "customer_name": "Nome (ou parte do nome) do cliente.",
    "customer_reference": "Referência do cliente no pedido ou cadastro.",
    "customer_segment": "Filtra clientes: weg (WEG) ou new_business (novos negócios). Vazio = todos os segmentos.",
    "dataFim": "Data final do período (AAAA-MM-DD).",
    "dataInicio": "Data inicial do período (AAAA-MM-DD).",
    "data_final": "Data final do período consultado (AAAA-MM-DD).",
    "data_inicial": "Data inicial do período consultado (AAAA-MM-DD).",
    "date": "Data de referência (AAAA-MM-DD).",
    "date_end": "Data final do período consultado (AAAA-MM-DD).",
    "date_from": "Data inicial do período consultado (AAAA-MM-DD).",
    "date_start": "Data inicial do período consultado (AAAA-MM-DD).",
    "date_to": "Data final do período consultado (AAAA-MM-DD).",
    "department": "Identificador ou nome do departamento.",
    "department_id": "Identificador do departamento no painel IDD.",
    "descricao": "Descrição (ou parte dela) para filtrar.",
    "descricao_peca": "Descrição da peça no cadastro.",
    "description": "Descrição (ou parte dela) para filtrar.",
    "details_limit": "Máximo de linhas de detalhe retornadas.",
    "direction": "Direção da ordenação: asc (crescente) ou desc (decrescente).",
    "efficiency_bands": "Faixas de eficiência em CSV (ex.: ok, low, verify).",
    "employee": "Código ou matrícula do colaborador.",
    "eventTypes": "Tipos de evento a incluir (CSV).",
    "evidence_type": "Tipo de evidência anexa ao registro.",
    "failure_mode": "Modo de falha associado à NC ou PAC.",
    "file_kind": "Tipo/categoria do arquivo.",
    "filename": "Filtro parcial pelo nome do arquivo.",
    "filial": "Código da filial no Protheus (ex.: 01 ou 02).",
    "filial_id": "Identificador da filial no cadastro. Prefira o código curto (01, 02) quando a rota aceitar branch.",
    "finished_product_code": "Código do produto acabado (PA).",
    "format": "Formato de saída ou apresentação do dado.",
    "from": "Início do intervalo (data ou valor).",
    "granularity": "Como agrupar os pontos da série: day (dia), week (semana), month (mês) ou year (ano).",
    "group_by": "Como agregar o resultado (geral, filial, produto etc.).",
    "group_code": "Código do grupo de produto/material.",
    "has_revision": "Filtra arquivos que possuem sufixo de revisão.",
    "has_variant": "Filtra arquivos que possuem sufixo de variante.",
    "history_limit": "Máximo de pontos no histórico retornado.",
    "id": "Identificador único do registro.",
    "include_completed": "Inclui itens já concluídos no resultado.",
    "include_qtd_pi": "Inclui quantidade de produto intermediário (PI) no resultado.",
    "include_test_products": "Inclui produtos de teste no resultado.",
    "incluir_bloqueados": "Inclui registros bloqueados na listagem.",
    "inspection_id": "Identificador da inspeção.",
    "inspector": "Código ou nome do inspetor.",
    "invoice_number": "Número da nota fiscal.",
    "issue_date_end": "Fim do filtro pela data de emissão do documento (AAAA-MM-DD).",
    "issue_date_start": "Início do filtro pela data de emissão do documento (AAAA-MM-DD).",
    "item_code": "Código do item/material no Protheus.",
    "legacy": "Usa comportamento legado da API (campos/alias antigos).",
    "limit": "Máximo de registros retornados pela API (ranking ou listagem truncada).",
    "linked_sort_by": "Campo de ordenação dos itens vinculados.",
    "linked_sort_dir": "Direção da ordenação dos vínculos: asc ou desc.",
    "listing_type": "Filtro de tipo da listagem (ex.: Todos, LMP, Amostra).",
    "location": "Localização / endereço de estoque no Protheus.",
    "loss_type": "Tipo de perda a considerar: refugo, scrap ou ambos.",
    "lot": "Número do lote.",
    "max_depth": "Profundidade máxima da hierarquia/estrutura retornada.",
    "max_size_bytes": "Tamanho máximo do arquivo em bytes.",
    "min_plans": "Quantidade mínima de planos para incluir no resultado.",
    "min_size_bytes": "Tamanho mínimo do arquivo em bytes.",
    "modified_from": "Data/hora mínima de modificação (ISO).",
    "modified_to": "Data/hora máxima de modificação (ISO).",
    "months": "Quantidade de meses no intervalo analisado.",
    "name": "Nome (ou parte do nome) para filtrar.",
    "name_process": "Nome do processo Transforma Mais.",
    "nonconformity_scope": "Escopo das não conformidades consideradas.",
    "offset": "Quantos registros pular antes de retornar a página (paginação por deslocamento).",
    "op": "Número da ordem de produção (OP).",
    "operation_id": "Identificador da operação.",
    "operator_code": "Código(s) do operador (CSV).",
    "orderBy": "Campo usado para ordenar o ranking (ex.: horas, custo).",
    "orderDir": "Direção da ordenação: asc (crescente) ou desc (decrescente).",
    "overdue_only": "Lista apenas itens atrasados.",
    "owner_user_id": "Usuário responsável pelo registro.",
    "page": "Número da página na listagem paginada.",
    "pageSize": "Quantidade de linhas por página.",
    "page_size": "Quantidade de linhas por página.",
    "periodDays": "Quantos dias para trás entram no cálculo (ex.: 30 = último mês até hoje).",
    "plan_id": "Identificador do plano de ação.",
    "price_source": "Origem do preço usado no cálculo.",
    "problem_category": "Categoria do problema reportado.",
    "product": "Código ou identificador do produto.",
    "product_code": "Código do produto no Protheus (ex.: 90xxxxxx).",
    "product_group": "Grupo de produto no Protheus.",
    "product_prefix": "Prefixo do código de produto para filtrar famílias.",
    "product_type": "Filtra por tipo: PA (acabado) ou PI (intermediário).",
    "production_order": "Ordem(ns) de produção (CSV).",
    "q": "Texto livre de busca (código, nome ou descrição).",
    "raw_material_code": "Código da matéria-prima.",
    "recurso": "Código do recurso de produção.",
    "reference_date": "Data de referência usada no cálculo (AAAA-MM-DD).",
    "resource_id": "Identificador do recurso de agendamento.",
    "result": "Resultado da inspeção ou avaliação.",
    "revision": "Número ou código da revisão.",
    "root_cause_category": "Categoria da causa raiz.",
    "savings_type": "Tipo de economia (Kaizen).",
    "search": "Texto livre de busca.",
    "section": "Seção ou bloco do formulário/checklist.",
    "sector_name": "Nome do setor.",
    "senso_order": "Ordem do senso na auditoria 5S.",
    "severity": "Nível de severidade.",
    "shift": "Turno de produção.",
    "sort": "Critério de ordenação da listagem.",
    "sort_by": "Campo usado para ordenar a listagem.",
    "sort_dir": "Direção da ordenação: asc (crescente) ou desc (decrescente).",
    "status": "Status do registro no fluxo.",
    "status_ok_only": "Retorna apenas registros com status OK.",
    "stock_method": "Método de valorização/consulta de estoque.",
    "store": "Código da loja do cliente.",
    "start_date": "Início do intervalo (AAAA-MM-DD). Em rotas com Período (dias), o sistema pode calcular automaticamente.",
    "end_date": "Fim do intervalo (AAAA-MM-DD). Em rotas com Período (dias), o sistema pode calcular automaticamente.",
    "strict_idd_period": "Exige período estrito no cálculo do IDD.",
    "summary_only": "Quando ativo, retorna só o resumo sem a lista detalhada.",
    "supplier": "Código ou nome do fornecedor.",
    "supplier_code": "Código do fornecedor no Protheus.",
    "supplier_store": "Loja do fornecedor.",
    "template_key": "Chave do modelo/template usado.",
    "title": "Título (ou parte dele) para filtrar.",
    "tm": "Código TM (Transforma Mais).",
    "to": "Fim do intervalo (data ou valor).",
    "top_limit": "Quantidade máxima de itens no ranking.",
    "top_n": "Quantidade de itens no Top N.",
    "type": "Tipo do registro a filtrar.",
    "view": "Modo de visualização dos dados retornados.",
    "warehouse": "Código do armazém/estoque.",
    "work_center": "Código do centro de trabalho (CT) no Protheus. Vazio = todos os centros.",
}

KNOWN_PARAM_ENUMS: dict[str, list[Any]] = {
    "granularity": ["day", "week", "month", "year"],
    "customer_segment": ["weg", "new_business"],
    "loss_type": ["refugo", "scrap", "both"],
    "product_type": ["PA", "PI"],
    "sort_dir": ["asc", "desc"],
    "direction": ["asc", "desc"],
    "orderDir": ["asc", "desc"],
    "linked_sort_dir": ["asc", "desc"],
    "stock_method": ["auto", "hybrid", "estimated", "official_closure"],
}

KNOWN_PARAM_DEFAULTS: dict[str, Any] = {
    "granularity": "day",
}


def enrich_param_schema_entry(name: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Aplica label, hint, enum e default canônicos TV sobre o campo OpenAPI."""
    enriched = dict(entry)
    if name in PARAM_LABELS_PT:
        enriched["label"] = PARAM_LABELS_PT[name]
    hint = PARAM_HINTS_PT.get(name) or str(enriched.get("description") or "").strip()
    if hint:
        enriched["description"] = hint
    if name in KNOWN_PARAM_ENUMS and not enriched.get("enum"):
        enriched["enum"] = list(KNOWN_PARAM_ENUMS[name])
    # Período em dias: input numérico livre — nunca enum/select.
    if name == "periodDays":
        enriched.pop("enum", None)
    if name in KNOWN_PARAM_DEFAULTS and enriched.get("default") is None:
        enriched["default"] = KNOWN_PARAM_DEFAULTS[name]
        # Com default TV, não bloquear preview se o campo vier vazio na UI.
        enriched["optional"] = True
    return enriched


def normalize_route_param_schema(route: dict[str, Any]) -> dict[str, Any]:
    """Reaplica enrich após merge (remove enums obsoletos herdados do catálogo)."""
    schema = route.get("paramSchema")
    if not isinstance(schema, dict) or not schema:
        return route
    updated = dict(route)
    updated["paramSchema"] = {
        key: enrich_param_schema_entry(key, value if isinstance(value, dict) else {})
        for key, value in schema.items()
    }
    return updated


def strip_fixed_params_from_schema(route: dict[str, Any]) -> dict[str, Any]:
    """Remove do inspetor parâmetros já fixados no catálogo (ex.: granularity=day)."""
    fixed = route.get("fixedQueryParams")
    schema = route.get("paramSchema")
    if not isinstance(fixed, dict) or not isinstance(schema, dict):
        return route
    next_schema = {key: value for key, value in schema.items() if key not in fixed}
    updated = dict(route)
    if next_schema:
        updated["paramSchema"] = next_schema
    else:
        updated.pop("paramSchema", None)
    return updated


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def format_operation_id_label(operation_id: str) -> str:
    text = re.sub(r"^(get|list|search)_", "", operation_id, flags=re.IGNORECASE)
    text = text.replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else operation_id


def humanize_param_label(name: str, description: str | None = None) -> str:
    if name in PARAM_LABELS_PT:
        return PARAM_LABELS_PT[name]
    desc = (description or "").strip()
    if desc and len(desc) <= 48:
        return desc
    return name.replace("_", " ").strip().capitalize() or name


def resolve_category(operation: dict[str, Any]) -> str:
    tags = operation.get("tags") or []
    if isinstance(tags, list) and tags:
        tag = str(tags[0]).strip()
        if tag in TAG_TO_CATEGORY:
            return TAG_TO_CATEGORY[tag]
    path = str(operation.get("path") or "").strip()
    segment = path.strip("/").split("/")[0].lower() if path else ""
    return PATH_SEGMENT_TO_CATEGORY.get(segment, "other")


def infer_allowed_display_modes(operation: dict[str, Any]) -> list[str]:
    path = str(operation.get("path") or "").lower()
    operation_id = str(operation.get("operationId") or "").lower()
    haystack = f"{path} {operation_id}"
    if "series" in haystack or haystack.endswith("/series"):
        return ["line_chart", "auto"]
    if any(token in haystack for token in ("/search", "list_", "_list", "/items", "/proposals")):
        return ["table", "auto"]
    if "hierarchy" in haystack or "structure" in haystack:
        return ["table", "auto"]
    return ["kpi", "auto"]


def infer_meta_shape(operation: dict[str, Any]) -> str:
    x_delpi = operation.get("xDelpi") if isinstance(operation.get("xDelpi"), dict) else {}
    shape = str(x_delpi.get("shape") or "").strip()
    if shape:
        return shape
    path = str(operation.get("path") or "").lower()
    operation_id = str(operation.get("operationId") or "").lower()
    haystack = f"{path} {operation_id}"
    if any(token in haystack for token in ("/search", "list_", "_list", "/items", "/proposals")):
        return "paged_list"
    if "hierarchy" in haystack or "structure" in haystack:
        return "hierarchy"
    return "scalar"


def map_openapi_type(param: dict[str, Any]) -> str:
    type_name = str(param.get("type") or "").strip().lower()
    if type_name in {"integer", "int", "number"}:
        return "integer" if type_name != "number" else "number"
    if type_name == "boolean":
        return "boolean"
    return "string"


def build_param_schema_from_openapi(
    parameters: list[dict[str, Any]] | None,
) -> tuple[dict[str, Any], str]:
    """Converte parameters do baseline → paramSchema TV + paramStrategy."""
    params = [p for p in (parameters or []) if isinstance(p, dict) and p.get("name")]
    names = {str(p["name"]) for p in params}
    has_date_range = "start_date" in names and "end_date" in names
    strategy = "date_range" if has_date_range else "direct"
    schema: dict[str, Any] = {}

    if has_date_range:
        schema["periodDays"] = enrich_param_schema_entry(
            "periodDays",
            {
                "type": "integer",
                "default": 30,
                "label": PARAM_LABELS_PT["periodDays"],
                "optional": True,
            },
        )

    for param in params:
        name = str(param["name"])
        if has_date_range and name in {"start_date", "end_date"}:
            continue
        entry: dict[str, Any] = {
            "type": map_openapi_type(param),
            "optional": not bool(param.get("required")),
            "label": humanize_param_label(name, param.get("description")),
        }
        if param.get("default") is not None:
            entry["default"] = param["default"]
        if isinstance(param.get("enum"), list) and param["enum"]:
            entry["enum"] = list(param["enum"])
        openapi_desc = str(param.get("description") or "").strip()
        if openapi_desc:
            entry["description"] = openapi_desc
        schema[name] = enrich_param_schema_entry(name, entry)

    return schema, strategy


def infer_value_fields(operation_id: str) -> list[str]:
    """Heurística leve: operationId com _pct → campo homônimo + value."""
    oid = operation_id.strip()
    if "_pct" not in oid.lower():
        return []
    field = re.sub(r"^(get|list|search)_", "", oid, flags=re.IGNORECASE)
    if not field:
        return []
    return [field, "value"]


def merge_param_schema(
    openapi_schema: dict[str, Any],
    *overlays: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = {key: dict(value) if isinstance(value, dict) else value for key, value in openapi_schema.items()}
    for overlay in overlays:
        if not overlay:
            continue
        for key, value in overlay.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
    return merged


def build_base_route(operation: dict[str, Any]) -> dict[str, Any]:
    operation_id = str(operation.get("operationId") or "").strip()
    summary = str(operation.get("summary") or "").strip()
    description = str(operation.get("description") or "").strip()
    param_schema, param_strategy = build_param_schema_from_openapi(operation.get("parameters"))
    route: dict[str, Any] = {
        "operationId": operation_id,
        "httpMethod": "GET",
        "label": summary or format_operation_id_label(operation_id),
        "category": resolve_category(operation),
        "path": str(operation.get("path") or "").strip(),
        "allowedDisplayModes": infer_allowed_display_modes(operation),
        "metaShape": infer_meta_shape(operation),
    }
    if description:
        route["description"] = description
    if param_schema:
        route["paramSchema"] = param_schema
        route["paramStrategy"] = param_strategy
        if param_strategy == "date_range":
            route["defaultParams"] = {"periodDays": 30}
    value_fields = infer_value_fields(operation_id)
    if value_fields:
        route["valueFields"] = value_fields
    return route


def apply_overlay(base: dict[str, Any], overlay: dict[str, Any] | None) -> dict[str, Any]:
    if not overlay:
        return base
    merged = dict(base)
    for key, value in overlay.items():
        if key not in OVERLAY_KEYS or value in (None, "", [], {}):
            continue
        if key == "paramSchema" and isinstance(value, dict):
            merged["paramSchema"] = merge_param_schema(merged.get("paramSchema") or {}, value)
        elif key == "defaultParams" and isinstance(value, dict):
            merged["defaultParams"] = {**(merged.get("defaultParams") or {}), **value}
        else:
            merged[key] = value
    return merged


def merge_with_existing(base: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    """Preserva curadoria do catálogo atual (labels PT, valueFields manuais, etc.)."""
    if not existing:
        return base
    merged = dict(base)
    for key in OVERLAY_KEYS:
        if key == "paramSchema":
            continue
        value = existing.get(key)
        if value not in (None, "", [], {}):
            if key == "defaultParams" and isinstance(value, dict):
                merged["defaultParams"] = {**(merged.get("defaultParams") or {}), **value}
            else:
                merged[key] = value
    existing_schema = existing.get("paramSchema")
    if isinstance(existing_schema, dict) and existing_schema:
        merged["paramSchema"] = merge_param_schema(merged.get("paramSchema") or {}, existing_schema)
    return merged


def load_openapi_get_operations(baseline_path: Path) -> list[dict[str, Any]]:
    payload = load_json(baseline_path)
    operations = payload.get("operations") or []
    if not isinstance(operations, list):
        return []
    result: list[dict[str, Any]] = []
    for item in operations:
        if not isinstance(item, dict):
            continue
        if str(item.get("method") or "").upper() != "GET":
            continue
        if item.get("deprecated"):
            continue
        operation_id = str(item.get("operationId") or "").strip()
        if operation_id:
            result.append(item)
    result.sort(key=lambda op: (str(op.get("path") or ""), str(op.get("operationId") or "")))
    return result


def load_existing_routes(routes_path: Path) -> dict[str, dict[str, Any]]:
    if not routes_path.is_file():
        return {}
    payload = load_json(routes_path)
    raw = payload.get("routes") or []
    indexed: dict[str, dict[str, Any]] = {}
    if not isinstance(raw, list):
        return indexed
    for item in raw:
        if isinstance(item, dict):
            op = str(item.get("operationId") or "").strip()
            if op:
                indexed[op] = dict(item)
    return indexed


def load_overlays(overlays_path: Path) -> dict[str, dict[str, Any]]:
    if not overlays_path.is_file():
        return {}
    payload = load_json(overlays_path)
    raw = payload.get("overlays") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict) and str(key).strip()
    }


def extract_overlay_from_route(route: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    """Extrai só o que difere do base OpenAPI (para seed de overlays)."""
    overlay: dict[str, Any] = {}
    for key in OVERLAY_KEYS:
        if key == "paramSchema":
            continue
        value = route.get(key)
        if value in (None, "", [], {}):
            continue
        if value != base.get(key):
            overlay[key] = value
    route_schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
    base_schema = base.get("paramSchema") if isinstance(base.get("paramSchema"), dict) else {}
    schema_diff: dict[str, Any] = {}
    for key, value in route_schema.items():
        if key not in base_schema or base_schema.get(key) != value:
            schema_diff[key] = value
    if schema_diff:
        overlay["paramSchema"] = schema_diff
    return overlay


def seed_overlays_from_catalog(
    *,
    baseline_path: Path,
    routes_path: Path,
    overlays_path: Path,
) -> dict[str, dict[str, Any]]:
    existing = load_existing_routes(routes_path)
    overlays: dict[str, dict[str, Any]] = {}
    for operation in load_openapi_get_operations(baseline_path):
        operation_id = str(operation.get("operationId") or "").strip()
        base = build_base_route(operation)
        route = existing.get(operation_id)
        if not route:
            continue
        overlay = extract_overlay_from_route(route, base)
        # Só persiste overlays com conteúdo TV-relevante (não só label/description genéricos).
        tv_keys = {
            "valueFields",
            "seriesField",
            "tableFields",
            "tvConstraints",
            "fixedQueryParams",
            "paramStrategy",
            "defaultParams",
            "paramSchema",
        }
        if any(key in overlay for key in tv_keys):
            # Mantém label/description/category se já curados junto.
            overlays[operation_id] = overlay
    payload = {
        "version": 1,
        "description": (
            "Overlays TV por operationId — valueFields, tvConstraints, paramStrategy, "
            "labels curados. Mergeados sobre o schema gerado do OpenAPI."
        ),
        "overlays": dict(sorted(overlays.items())),
    }
    overlays_path.parent.mkdir(parents=True, exist_ok=True)
    overlays_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return overlays


def generate_routes(
    *,
    baseline_path: Path,
    routes_path: Path,
    overlays_path: Path | None = None,
) -> list[dict[str, Any]]:
    existing = load_existing_routes(routes_path)
    overlays = load_overlays(overlays_path or TV_OVERLAYS_PATH)
    generated: list[dict[str, Any]] = []
    for operation in load_openapi_get_operations(baseline_path):
        operation_id = str(operation.get("operationId") or "").strip()
        base = build_base_route(operation)
        with_existing = merge_with_existing(base, existing.get(operation_id))
        with_overlay = apply_overlay(with_existing, overlays.get(operation_id))
        normalized = normalize_route_param_schema(with_overlay)
        generated.append(strip_fixed_params_from_schema(normalized))
    return generated


def write_routes(routes_path: Path, routes: list[dict[str, Any]]) -> None:
    payload = {"routes": routes}
    routes_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=OPENAPI_BASELINE_PATH)
    parser.add_argument("--routes", type=Path, default=TV_ROUTES_PATH)
    parser.add_argument("--overlays", type=Path, default=TV_OVERLAYS_PATH)
    parser.add_argument("--write", action="store_true", help="Grava tv_data_routes.json")
    parser.add_argument("--check", action="store_true", help="Falha se o catálogo divergir do gerador")
    parser.add_argument(
        "--seed-overlays",
        action="store_true",
        help="Extrai overlays TV do catálogo atual para tv_data_route_overlays.json",
    )
    args = parser.parse_args()

    if not args.baseline.is_file():
        print(f"OpenAPI baseline ausente: {args.baseline}", file=sys.stderr)
        return 1

    if args.seed_overlays:
        overlays = seed_overlays_from_catalog(
            baseline_path=args.baseline,
            routes_path=args.routes,
            overlays_path=args.overlays,
        )
        print(f"Gravados {len(overlays)} overlays em {args.overlays}")
        if not args.write and not args.check:
            return 0

    generated = generate_routes(
        baseline_path=args.baseline,
        routes_path=args.routes,
        overlays_path=args.overlays,
    )

    if args.write:
        write_routes(args.routes, generated)
        with_schema = sum(1 for item in generated if item.get("paramSchema"))
        with_values = sum(1 for item in generated if item.get("valueFields"))
        print(
            f"Gravado {len(generated)} rotas em {args.routes} "
            f"(paramSchema={with_schema}, valueFields={with_values})"
        )
        return 0

    if args.check:
        if not args.routes.is_file():
            print(f"Catálogo TV ausente: {args.routes}", file=sys.stderr)
            return 1
        stored = load_json(args.routes).get("routes") or []
        if stored != generated:
            print(
                f"Drift detectado — stored={len(stored)} generated={len(generated)}. "
                "Rode com --write para sincronizar.",
                file=sys.stderr,
            )
            return 1
        print(f"OK — catálogo sincronizado ({len(generated)} rotas GET).")
        return 0

    print(json.dumps({"count": len(generated), "routes": generated[:3]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
