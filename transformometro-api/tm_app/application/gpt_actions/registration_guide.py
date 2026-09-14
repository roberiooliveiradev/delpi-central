"""Registration guide for Custom GPT specialists (catalog payload).

Single source of field/enum guidance for guided process + improvement signup.
Enums come from tm_app.core.catalogs — do not duplicate literals here.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.gpt_actions.improvement_package_contract import (
    build_package_hints,
)
from tm_app.core.catalogs import (
    BENEFICIO_CALCULO_CATEGORIA,
    BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
    CENARIO_TIPO,
    FASE_MELHORIA,
    PRIORIDADE_MELHORIA,
    RECORRENCIAS,
    STATUS_INSTANCIA,
    STATUS_PROCESSO,
    TIPO_INVESTIMENTO,
)


def build_registration_guide() -> dict[str, Any]:
    """Structured guide returned inside gpt_get_catalog."""
    return {
        "concepts": {
            "process": (
                "Master process (processo-mestre): corporate initiative name. "
                "Not tied to a single unit until an instance exists."
            ),
            "instance": (
                "Operational improvement (melhoria): process × unit × department(s). "
                "API entity `instance` / field `instancia_id`."
            ),
            "revision": (
                "Calculable scenario with validity dates, measurement and costs. "
                "Types: baseline (before) or melhoria|automacao|correcao (after)."
            ),
            "measurement": (
                "Monthly operating metrics for one revision (upsert by revisao_id)."
            ),
            "investment": "One-time or recurring cost lines on a non-baseline revision.",
        },
        "registration_flow": [
            {
                "step": 1,
                "id": "resolve_scope",
                "ask": [
                    "Which unit (filial) and department(s) (setor)?",
                    "Is this a new master process or an existing one?",
                ],
                "actions": [
                    "Call gpt_get_catalog and reuse filiais/setores from access_scope.",
                    "Search process with gpt_search_records entity=process before creating.",
                ],
            },
            {
                "step": 2,
                "id": "process_and_instance",
                "ask": [
                    "Process name and short description of what changed.",
                    "Improvement title/summary, phase and priority if known.",
                ],
                "actions": [
                    "Create or reuse process, then instance (or use improvement package).",
                    "Always keep instancia_id for later revisions.",
                ],
            },
            {
                "step": 3,
                "id": "baseline",
                "ask": [
                    "As-is monthly volume, average time (min), rework/error rates, labor hourly cost.",
                    "Baseline version label (e.g. v1.0) and start date (YYYY-MM-DD).",
                ],
                "actions": [
                    "Create revision cenario_tipo=baseline with instancia_id.",
                    "Upsert measurement on that revisao_id.",
                    "Never activate a baseline as the operational current revision.",
                ],
            },
            {
                "step": 4,
                "id": "scenario",
                "ask": [
                    "To-be metrics after the improvement.",
                    "Scenario type: melhoria, automacao, or correcao.",
                    "Investment items (description, amount, type).",
                    "Whether to activate now and recalculate the dashboard.",
                ],
                "actions": [
                    "Create non-baseline revision with revisao_referencia_id = baseline (or prior active).",
                    "Upsert measurement + investments.",
                    "Prefer gpt_validate_improvement_package then gpt_commit_improvement_package.",
                    "Activate only the scenario revision when the user confirms.",
                ],
            },
            {
                "step": 5,
                "id": "governed_followups",
                "ask": [],
                "actions": [
                    "Diagrams and WBS/decomposition may be persisted via GPT only when the API surface supports the write and live manage authorization succeeds; always PREPARE → SHOW → CONFIRM → WRITE → VERIFY.",
                    "Point user to Minha DELPI UI for evidence uploads and meeting-minute handwritten signatures.",
                    "Offer gpt_analyze for KPIs after recalculate.",
                ],
            },
        ],
        "entity_schemas": {
            "process": {
                "required": ["nome_processo", "status_processo"],
                "optional": [
                    "descricao_processo",
                    "gestor_responsavel",
                    "objetivo_processo",
                    "codigo_processo",
                    "familia_processo",
                    "agrupador_ferramenta",
                    "filial_id",
                    "setor_id",
                    "todas_filiais_ativas",
                    "filial_ids",
                    "setor_ids",
                ],
                "enums": {"status_processo": list(STATUS_PROCESSO)},
                "defaults": {},
                "notes": [
                    "filial_id+setor_id on create also creates the first instance.",
                    "Otherwise create instance separately with processo_id.",
                ],
            },
            "instance": {
                "required": ["setor_ids"],
                "optional": [
                    "filial_id",
                    "todas_filiais_ativas",
                    "rotulo_instancia",
                    "status_instancia",
                    "resumo_melhoria",
                    "responsavel_local",
                    "fase_melhoria",
                    "data_alvo_go_live",
                    "prioridade",
                ],
                "enums": {
                    "fase_melhoria": list(FASE_MELHORIA),
                    "prioridade": list(PRIORIDADE_MELHORIA),
                    "status_instancia": list(STATUS_INSTANCIA),
                },
                "defaults": {
                    "fase_melhoria": "planejado",
                    "prioridade": "media",
                    "status_instancia": "ativo",
                    "todas_filiais_ativas": False,
                },
                "notes": [
                    "Need filial_id OR todas_filiais_ativas=true.",
                    "setor_ids must have at least one department.",
                    "Create body also needs processo_id in data.",
                ],
            },
            "revision": {
                "required": [
                    "processo_id",
                    "versao_revisao",
                    "cenario_tipo",
                    "data_inicio_vigencia",
                ],
                "optional": [
                    "instancia_id",
                    "revisao_ativa",
                    "revisao_referencia_id",
                    "beneficio_calculo_categoria",
                    "descricao_revisao",
                    "motivo_revisao",
                    "data_implantacao",
                    "data_fim_vigencia",
                    "observacoes",
                ],
                "enums": {
                    "cenario_tipo": list(CENARIO_TIPO),
                    "beneficio_calculo_categoria": list(BENEFICIO_CALCULO_CATEGORIA),
                },
                "defaults": {
                    "revisao_ativa": False,
                    "beneficio_calculo_categoria": BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
                },
                "notes": [
                    "Always pass instancia_id for guided flows.",
                    "baseline must NOT set revisao_referencia_id.",
                    "Non-baseline REQUIRES revisao_referencia_id.",
                    "Do not set revisao_ativa=true on create for baseline; use activate on scenario.",
                ],
            },
            "measurement": {
                "required": ["revisao_id"],
                "optional": [
                    "volume_mensal",
                    "tempo_medio_execucao_min",
                    "tempo_retrabalho_min",
                    "percentual_retrabalho",
                    "percentual_erro",
                    "quantidade_erros_mes",
                    "custo_hora_mao_obra",
                    "custo_unitario_erro",
                    "custo_unitario_retrabalho",
                    "custo_outros_desperdicios",
                    "base_referencia_mes",
                    "observacoes",
                ],
                "enums": {},
                "defaults": {
                    "volume_mensal": 0,
                    "tempo_medio_execucao_min": 0,
                    "tempo_retrabalho_min": 0,
                    "percentual_retrabalho": 0,
                    "percentual_erro": 0,
                    "quantidade_erros_mes": 0,
                    "custo_hora_mao_obra": 0,
                    "custo_unitario_erro": 0,
                    "custo_unitario_retrabalho": 0,
                    "custo_outros_desperdicios": 0,
                },
                "notes": [
                    "Upsert: create and update share the same payload shape.",
                    "Ask for as-is (baseline) and to-be (scenario) numbers separately.",
                ],
            },
            "investment": {
                "required": ["revisao_id", "tipo_investimento", "descricao_item"],
                "optional": [
                    "quantidade",
                    "valor_unitario",
                    "recorrencia",
                    "categoria_investimento",
                    "data_investimento",
                    "meses_vigencia",
                    "centro_custo",
                    "observacoes",
                ],
                "enums": {
                    "tipo_investimento": list(TIPO_INVESTIMENTO),
                    "recorrencia": list(RECORRENCIAS),
                },
                "defaults": {"quantidade": 1, "valor_unitario": 0, "recorrencia": "unico"},
                "notes": ["Usually attached to the scenario revision, not baseline."],
            },
        },
        "package_hints": build_package_hints(),
    }
