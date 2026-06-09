"""Consultas SQL de produção conhecidas — fast path operacional (POST /data/sql)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.chat_sql_production_schedule_date_service import (
    ChatSqlProductionScheduleDateService,
    ResolvedProductionScheduleDate,
)

SqlProductionMode = Literal["execute", "authoring"]

_BRANCH_BREAKDOWN_TERMS = (
    "por filial",
    "por filiais",
    "agrupado por filial",
    "agrupada por filial",
    "em cada filial",
    "todas as filiais",
    "todas filiais",
    "cada filial",
    "detalhe por filial",
    "detalhar por filial",
)

_DEFAULT_BRANCHES = ("01", "02")


@dataclass(frozen=True)
class SqlProductionResolution:
    mode: SqlProductionMode
    sql: str
    title: str


class ChatSqlProductionQueryService:
    """Resolve perguntas de produção para SQL parametrizado (sem LLM/RAG lento)."""

    @classmethod
    def can_fast_path(cls, message: str | None, allowed_action_ids: list[str] | None) -> bool:
        if not allowed_action_ids:
            return False

        resolution = cls.resolve(message)

        if not resolution:
            return False

        if resolution.mode == "authoring":
            return True

        return cls._allowed_ids_include_sql_action(allowed_action_ids)

    @classmethod
    def resolve(cls, message: str | None) -> SqlProductionResolution | None:
        if not ChatSqlOperationalIntentService.requires_production_sql_knowledge(message):
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        branch = cls._extract_branch_code(normalized)
        include_all_branches = cls.wants_branch_breakdown(normalized) and branch is None
        schedule_date = ChatSqlProductionScheduleDateService.resolve(message)
        sql = cls._build_products_scheduled_sql(
            schedule_date,
            branch=branch or "01",
            include_all_branches=include_all_branches,
        )
        title = schedule_date.title

        if include_all_branches:
            title = ExternalActionResponseContentService.format(
                "productionSchedule",
                "titleByBranchBreakdown",
                default=f"{title} por filial",
                label=schedule_date.label,
            )

        if ChatSqlIntentService.is_authoring_request(message):
            return SqlProductionResolution(mode="authoring", sql=sql, title=title)

        return SqlProductionResolution(mode="execute", sql=sql, title=title)

    @classmethod
    def wants_branch_breakdown(cls, normalized: str) -> bool:
        return any(term in normalized for term in _BRANCH_BREAKDOWN_TERMS)

    @classmethod
    def format_authoring_answer(cls, resolution: SqlProductionResolution) -> str:
        intro = ExternalActionResponseContentService.get(
            "productionSchedule",
            "authoringIntro",
        )
        hint = ExternalActionResponseContentService.get(
            "productionSchedule",
            "authoringExecuteHint",
        )
        return (
            f"### {resolution.title}\n\n"
            f"{intro}\n\n"
            f"```sql\n{resolution.sql.strip()}\n```\n\n"
            f"{hint}"
        )

    @classmethod
    def expand_production_sql_by_branch(cls, sql: str) -> str:
        """Expande consulta SC2010 de filial única para todas as filiais + coluna FILIAL."""
        if not re.search(r"\bSC2010\b", str(sql or ""), flags=re.I):
            return sql

        if re.search(r"\bOP\.C2_FILIAL\s+IN\s*\(", str(sql or ""), flags=re.I):
            return sql

        schedule_date = ChatSqlProductionScheduleDateService.infer_from_sql(sql)

        if schedule_date is None:
            schedule_date = ChatSqlProductionScheduleDateService.resolve(None)

        return cls._build_products_scheduled_sql(
            schedule_date,
            branch="01",
            include_all_branches=True,
        )

    @classmethod
    def _allowed_ids_include_sql_action(cls, allowed_action_ids: list[str]) -> bool:
        return ExternalActionSqlCapabilityService.allowed_action_ids_include_sql(
            allowed_action_ids
        )

    @classmethod
    def _extract_branch_code(cls, normalized: str) -> str | None:
        match = re.search(r"\bfilial\s*(\d{2})\b", normalized)

        if match:
            return match.group(1)

        match = re.search(r"\bf(?:ilial)?\s*(\d{2})\b", normalized)

        if match:
            return match.group(1)

        return None

    @classmethod
    def _build_products_scheduled_sql(
        cls,
        schedule_date: ResolvedProductionScheduleDate,
        *,
        branch: str,
        include_all_branches: bool = False,
    ) -> str:
        if include_all_branches:
            branches = ", ".join(f"'{code}'" for code in _DEFAULT_BRANCHES)

            return f"""{schedule_date.sql_date_declaration}
SELECT
    OP.C2_FILIAL AS FILIAL,
    OP.C2_PRODUTO AS COD_PRODUTO,
    P.B1_DESC AS DESCRICAO_PRODUTO,
    OP.C2_QUANT AS QTD_PLANEJADA,
    OP.C2_UM AS UNIDADE,
    OA.H8_DTINI AS DATA_INICIO_OPERACAO
FROM SC2010 OP WITH (NOLOCK)
LEFT JOIN SD4010 RE WITH (NOLOCK)
    ON RE.D4_OP = OP.C2_OP
   AND RE.D4_FILIAL = OP.C2_FILIAL
   AND RE.D_E_L_E_T_ = ''
LEFT JOIN SH8010 OA WITH (NOLOCK)
    ON OA.H8_OP = RE.D4_OP
   AND OA.H8_OPER = RE.D4_OPERAC
   AND OA.H8_FILIAL = RE.D4_FILIAL
   AND OA.D_E_L_E_T_ = ''
LEFT JOIN SB1010 P WITH (NOLOCK)
    ON P.B1_COD = OP.C2_PRODUTO
   AND P.D_E_L_E_T_ = ''
WHERE OP.C2_FILIAL IN ({branches})
  AND RE.D4_FILIAL = OP.C2_FILIAL
  AND OA.H8_FILIAL = OP.C2_FILIAL
  AND OP.C2_PRIOR = '500'
  AND CAST(OA.H8_DTINI AS DATE) = @DATA
  AND OP.D_E_L_E_T_ = ''
  AND P.B1_TIPO = 'PA'
GROUP BY
    OP.C2_FILIAL,
    OP.C2_PRODUTO,
    P.B1_DESC,
    OP.C2_QUANT,
    OP.C2_UM,
    OA.H8_DTINI
ORDER BY OP.C2_FILIAL ASC, OP.C2_PRODUTO ASC"""

        branch_code = str(branch or "01").zfill(2)[:2]

        return f"""DECLARE @FILIAL CHAR(2) = '{branch_code}';
{schedule_date.sql_date_declaration}
SELECT
    OP.C2_PRODUTO AS COD_PRODUTO,
    P.B1_DESC AS DESCRICAO_PRODUTO,
    OP.C2_QUANT AS QTD_PLANEJADA,
    OP.C2_UM AS UNIDADE,
    OA.H8_DTINI AS DATA_INICIO_OPERACAO
FROM SC2010 OP WITH (NOLOCK)
LEFT JOIN SD4010 RE WITH (NOLOCK)
    ON RE.D4_OP = OP.C2_OP
   AND RE.D4_FILIAL = OP.C2_FILIAL
   AND RE.D_E_L_E_T_ = ''
LEFT JOIN SH8010 OA WITH (NOLOCK)
    ON OA.H8_OP = RE.D4_OP
   AND OA.H8_OPER = RE.D4_OPERAC
   AND OA.H8_FILIAL = RE.D4_FILIAL
   AND OA.D_E_L_E_T_ = ''
LEFT JOIN SB1010 P WITH (NOLOCK)
    ON P.B1_COD = OP.C2_PRODUTO
   AND P.D_E_L_E_T_ = ''
WHERE OP.C2_FILIAL = @FILIAL
  AND RE.D4_FILIAL = @FILIAL
  AND OA.H8_FILIAL = @FILIAL
  AND OP.C2_PRIOR = '500'
  AND CAST(OA.H8_DTINI AS DATE) = @DATA
  AND OP.D_E_L_E_T_ = ''
  AND P.B1_TIPO = 'PA'
GROUP BY
    OP.C2_PRODUTO,
    P.B1_DESC,
    OP.C2_QUANT,
    OP.C2_UM,
    OA.H8_DTINI
ORDER BY OP.C2_PRODUTO ASC"""
