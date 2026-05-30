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

SqlProductionMode = Literal["execute", "authoring"]


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
        if not ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        filial = cls._extract_filial(normalized)
        sql = cls._build_products_scheduled_today_sql(filial)
        title = "Produtos programados para produção hoje"

        if ChatSqlIntentService.is_authoring_request(message):
            return SqlProductionResolution(mode="authoring", sql=sql, title=title)

        return SqlProductionResolution(mode="execute", sql=sql, title=title)

    @classmethod
    def format_authoring_answer(cls, resolution: SqlProductionResolution) -> str:
        return (
            f"### {resolution.title}\n\n"
            "Consulta sugerida para `POST /data/sql` (somente leitura):\n\n"
            f"```sql\n{resolution.sql.strip()}\n```\n\n"
            "Para **executar** no Protheus, peça: «execute essa consulta» ou «traga os dados»."
        )

    @classmethod
    def _allowed_ids_include_sql_action(cls, allowed_action_ids: list[str]) -> bool:
        for action_id in allowed_action_ids:
            lowered = str(action_id or "").lower()
            if any(
                token in lowered
                for token in (
                    "execute_readonly",
                    "execute_sql",
                    "data_sql",
                    "/data/sql",
                    ".data.",
                )
            ):
                return True
        return False

    @classmethod
    def _extract_filial(cls, normalized: str) -> str:
        match = re.search(r"\bfilial\s*(\d{2})\b", normalized)
        if match:
            return match.group(1)

        match = re.search(r"\bf(?:ilial)?\s*(\d{2})\b", normalized)
        if match:
            return match.group(1)

        return "01"

    @classmethod
    def _build_products_scheduled_today_sql(cls, filial: str) -> str:
        branch = str(filial or "01").zfill(2)[:2]

        return f"""DECLARE @FILIAL CHAR(2) = '{branch}';
DECLARE @DATA DATE = CAST(GETDATE() AS DATE);
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
