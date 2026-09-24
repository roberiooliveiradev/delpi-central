"""Canonical GPT record write fields for Custom GPT OpenAPI.

Fields must be explicit for Builder constructibility. Descriptions kept short
for OpenAPI ≤100 KiB budget; full contracts live in gpt_get_catalog.
"""

from __future__ import annotations

from typing import Any


def openapi_record_data_properties() -> dict[str, Any]:
    """Create/update fields under changes{} / data{} across entities."""
    return {
    "nome_processo": {
        "type": "string",
        "description": "Required when entity=process (create)"
    },
    "status_processo": {
        "type": "string",
        "description": "Required when entity=process"
    },
    "codigo_processo": {
        "type": "string",
        "description": "Business process code"
    },
    "descricao_processo": {
        "type": "string",
        "description": "On process update: omit keeps current; None clears"
    },
    "gestor_responsavel": {
        "type": "string",
        "description": "On process update: omit keeps current; None clears"
    },
    "objetivo_processo": {
        "type": "string",
        "description": "On process update: omit keeps current; None clears"
    },
    "familia_processo": {
        "type": "string"
    },
    "agrupador_ferramenta": {
        "type": "string"
    },
    "filial_ids": {
        "type": "array",
        "items": {
            "type": "string"
        },
        "description": "Process scope units (when not todas_filiais_ativas)"
    },
    "processo_id": {
        "type": "string",
        "description": "Parent/process id when creating instance/revision"
    },
    "instancia_id": {
        "type": "string"
    },
    "revisao_id": {
        "type": "string"
    },
    "recurso_compartilhado_id": {
        "type": "string",
        "description": "Required when entity=resource_cost (create) or entity=r"
    },
    "recurso_id": {
        "type": "string",
        "description": "Alias of recurso_compartilhado_id for resource_cost cre"
    },
    "filial_id": {
        "type": "string",
        "description": "Required for entity=instance unless todas_filiais_ativa"
    },
    "todas_filiais_ativas": {
        "type": "boolean",
        "default": False,
        "description": "When True, instance applies to all active units; do not"
    },
    "setor_ids": {
        "type": "array",
        "items": {
            "type": "string"
        },
        "description": "Required for entity=instance (at least one)"
    },
    "setor_id": {
        "type": "string",
        "description": "Legacy single-department shortcut"
    },
    "status_instancia": {
        "type": "string"
    },
    "rotulo_instancia": {
        "type": "string"
    },
    "responsavel_local": {
        "type": "string"
    },
    "data_alvo_go_live": {
        "type": "string"
    },
    "resumo_melhoria": {
        "type": "string"
    },
    "fase_melhoria": {
        "type": "string"
    },
    "prioridade": {
        "type": "string"
    },
    "versao_revisao": {
        "type": "string"
    },
    "cenario_tipo": {
        "type": "string"
    },
    "data_inicio_vigencia": {
        "type": "string",
        "format": "date",
        "description": "Revision or resource_cost start date (YYYY-MM-DD)"
    },
    "data_fim_vigencia": {
        "type": "string",
        "format": "date",
        "nullable": True,
        "description": "Omit = open/unset on create; null = clear on update; date = set",
    },
    "revisao_referencia_id": {
        "type": "string"
    },
    "beneficio_calculo_categoria": {
        "type": "string"
    },
    "descricao_revisao": {
        "type": "string"
    },
    "motivo_revisao": {
        "type": "string"
    },
    "data_implantacao": {
        "type": "string",
        "format": "date"
    },
    "revisao_ativa": {
        "type": "boolean"
    },
    "confirm_vigencia_change": {
        "type": "boolean",
        "description": "Required True when changing revision vigência and measu"
    },
    "observacoes": {
        "type": "string"
    },
    "volume_mensal": {
        "type": "number"
    },
    "tempo_medio_execucao_min": {
        "type": "number"
    },
    "tempo_retrabalho_min": {
        "type": "number"
    },
    "percentual_retrabalho": {
        "type": "number"
    },
    "percentual_erro": {
        "type": "number"
    },
    "quantidade_erros_mes": {
        "type": "number"
    },
    "custo_hora_mao_obra": {
        "type": "number"
    },
    "custo_unitario_erro": {
        "type": "number"
    },
    "custo_unitario_retrabalho": {
        "type": "number"
    },
    "custo_outros_desperdicios": {
        "type": "number"
    },
    "base_referencia_mes": {
        "type": "string"
    },
    "tipo_investimento": {
        "type": "string"
    },
    "descricao_item": {
        "type": "string"
    },
    "quantidade": {
        "type": "number"
    },
    "valor_unitario": {
        "type": "number"
    },
    "recorrencia": {
        "type": "string",
        "description": "Investment or shared_resource recurrence (e"
    },
    "categoria_investimento": {
        "type": "string"
    },
    "data_investimento": {
        "type": "string",
        "format": "date"
    },
    "meses_vigencia": {
        "type": "integer"
    },
    "centro_custo": {
        "type": "string"
    },
    "nome_recurso": {
        "type": "string"
    },
    "tipo_custo": {
        "type": "string"
    },
    "valor_total_recorrente": {
        "type": "number",
        "description": "Legacy catalog total; prefer entity=resource_cost for v"
    },
    "criterio_rateio": {
        "type": "string"
    },
    "escopo_recurso": {
        "type": "string"
    },
    "base_competencia": {
        "type": "string"
    },
    "status_recurso": {
        "type": "string"
    },
    "categoria_recurso": {
        "type": "string"
    },
    "fornecedor": {
        "type": "string"
    },
    "codigo_recurso": {
        "type": "string"
    },
    "valor_mensal": {
        "type": "number",
        "minimum": 0,
        "description": "Monthly cost for entity=resource_cost"
    },
    "vigente_desde": {
        "type": "string",
        "format": "date",
        "description": "Used by UI reajuste flows; prefer data_inicio_vigencia "
    },
    "ativo": {
        "type": "boolean"
    },
    "data_inicio_uso": {
        "type": "string",
        "format": "date"
    },
    "data_fim_uso": {
        "type": "string",
        "format": "date"
    },
    "peso_rateio": {
        "type": "number"
    },
    "codigo_filial": {
        "type": "string"
    },
    "nome_filial": {
        "type": "string"
    },
    "status_filial": {
        "type": "string"
    },
    "codigo_setor": {
        "type": "string"
    },
    "nome_setor": {
        "type": "string"
    },
    "status_setor": {
        "type": "string"
    },
    "filiais": {
        "type": "array",
        "items": {
            "type": "string"
        },
        "description": "Unit codes for entity=department"
    },
    "unit_code": {
        "type": "string",
        "description": "Filial code for entity=meeting_minute (01|02; zero-padd"
    },
    "title": {
        "type": "string",
        "description": "Title for entity=meeting_minute or entity=process_docum"
    },
    "content_md": {
        "type": "string",
        "description": "Markdown body for entity=process_document"
    },
    "meeting_type": {
        "type": "string",
        "enum": [
            "ordinary",
            "extraordinary",
            "workshop",
            "follow_up",
            "kickoff",
            "other"
        ],
        "description": "Meeting type for entity=meeting_minute (default ordinar"
    },
    "meeting_date": {
        "type": "string",
        "format": "date",
        "description": "Required on meeting_minute create"
    },
    "start_time": {
        "type": "string",
        "description": "Optional HH:MM or HH:MM:SS (not 14h30)"
    },
    "end_time": {
        "type": "string",
        "description": "Optional HH:MM or HH:MM:SS (not 14h30)"
    },
    "location": {
        "type": "string"
    },
    "responsible_user_id": {
        "type": "string",
        "description": "Optional UUID"
    },
    "responsible_name": {
        "type": "string"
    },
    "chair_name": {
        "type": "string"
    },
    "secretary_name": {
        "type": "string"
    },
    "agenda_html": {
        "type": "string"
    },
    "body_html": {
        "type": "string"
    },
    "decisions_html": {
        "type": "string"
    },
    "pending_html": {
        "type": "string"
    },
    "observations_html": {
        "type": "string"
    },
    "participants": {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": True,
            "properties": {},
            "x-delpi-gpt-opaque-object": True,
            "description": "Meeting-minute participant row. Entity-specific bag; signature capture remains UI-only."
        },
        "description": "Participants for entity=meeting_minute"
    },
    "signers": {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": True,
            "properties": {},
            "x-delpi-gpt-opaque-object": True,
            "description": "Meeting-minute signer row. Signature capture remains UI-only."
        },
        "description": "Signers for entity=meeting_minute (signature capture re"
    },
    "conteudo": {
        "type": "object",
        "additionalProperties": True,
        "properties": {},
        "x-delpi-gpt-opaque-object": True,
        "description": "Document payload (diagram flowchart or decomposition tr"
    },
    "node_ids": {
        "type": "array",
        "items": {
            "type": "string"
        },
        "description": "Scope node ids for instance diagram/decomposition scope"
    },
    "inherit_all": {
        "type": "boolean"
    },
    "include_boundary_edges": {
        "type": "boolean"
    },
    "include_descendants": {
        "type": "boolean"
    },
    "modo": {
        "type": "string",
        "description": "Impact×effort matrix mode (entity=impact_effort_matrix)"
    },
    "inputs_manuais": {
        "type": "object",
        "additionalProperties": True,
        "properties": {},
        "x-delpi-gpt-opaque-object": True,
        "description": "Impact×effort matrix manual inputs"
    },
    "overrides": {
        "type": "object",
        "additionalProperties": True,
        "properties": {},
        "x-delpi-gpt-opaque-object": True,
        "description": "Impact×effort matrix overrides"
    }
}


# Contract gate: fields that must stay visible to Custom GPT for write actions.
REQUIRED_GPT_RECORD_WRITE_FIELDS: frozenset[str] = frozenset(
    {
        "valor_mensal",
        "recurso_compartilhado_id",
        "nome_recurso",
        "tipo_custo",
        "tipo_investimento",
        "descricao_item",
        "valor_unitario",
        "quantidade",
        "peso_rateio",
        "ativo",
        "custo_hora_mao_obra",
        "percentual_retrabalho",
        "confirm_vigencia_change",
        "todas_filiais_ativas",
        "nome_processo",
        "conteudo",
        "meeting_date",
        "unit_code",
        "title",
        "codigo_filial",
        "setor_id",
        "filiais",
    }
)
