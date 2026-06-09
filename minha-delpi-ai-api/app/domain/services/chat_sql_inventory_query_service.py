"""Consultas SQL de estoque agregado — fast path (POST /data/sql)."""

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
from app.domain.services.chat_sql_intent_vocabulary_service import (
    ChatSqlIntentVocabularyService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)

SqlInventoryMode = Literal["execute", "authoring"]


@dataclass(frozen=True)
class SqlInventoryResolution:
    mode: SqlInventoryMode
    sql: str
    title: str


class ChatSqlInventoryQueryService:
    """Template SB2010+SB1010 para listas de estoque (ex.: abaixo do mínimo)."""

    @classmethod
    def _below_minimum_markers(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "operationalIntent",
            "inventoryAggregateMarkers",
        )

    @classmethod
    def can_fast_path(cls, message: str | None, allowed_action_ids: list[str] | None) -> bool:
        if not allowed_action_ids:
            return False

        resolution = cls.resolve(message)

        if not resolution:
            return False

        if resolution.mode == "authoring":
            return True

        return ExternalActionSqlCapabilityService.allowed_action_ids_include_sql(
            allowed_action_ids
        )

    @classmethod
    def resolve(cls, message: str | None) -> SqlInventoryResolution | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or not cls._looks_like_below_minimum_stock(normalized):
            return None

        if not ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            return None

        filial = cls._extract_filial(normalized)
        top = cls._extract_top(normalized)
        sql = cls._build_below_minimum_sql(filial=filial, top=top)
        title = "Produtos com estoque abaixo do mínimo"

        if ChatSqlIntentService.is_authoring_request(message):
            return SqlInventoryResolution(mode="authoring", sql=sql, title=title)

        return SqlInventoryResolution(mode="execute", sql=sql, title=title)

    @classmethod
    def format_authoring_answer(cls, resolution: SqlInventoryResolution) -> str:
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
    def _looks_like_below_minimum_stock(cls, normalized: str) -> bool:
        return any(marker in normalized for marker in cls._below_minimum_markers())

    @classmethod
    def _extract_filial(cls, normalized: str) -> str | None:
        match = re.search(r"\bfilial\s*(\d{2})\b", normalized)

        if match:
            return match.group(1)

        match = re.search(r"\bf(?:ilial)?\s*(\d{2})\b", normalized)

        if match:
            return match.group(1)

        if "todas as filiais" in normalized or "todas filiais" in normalized:
            return None

        return None

    @classmethod
    def _extract_top(cls, normalized: str) -> int:
        match = re.search(r"\btop\s*(\d{1,3})\b", normalized)

        if match:
            return min(int(match.group(1)), 500)

        match = re.search(r"\b(\d{1,2})\s+produtos?\b", normalized)

        if match:
            return min(int(match.group(1)), 500)

        return 200

    @classmethod
    def _build_below_minimum_sql(cls, *, filial: str | None, top: int) -> str:
        branch_filter = ""

        if filial:
            branch = str(filial).zfill(2)[:2]
            branch_filter = f"\n  AND SB2.B2_FILIAL = '{branch}'"

        return f"""SELECT TOP {int(top)}
    SB2.B2_COD AS product_code,
    RTRIM(SB1.B1_DESC) AS product_description,
    SB2.B2_FILIAL AS branch,
    RTRIM(SB2.B2_LOCAL) AS warehouse,
    SB2.B2_QATU AS current_quantity,
    COALESCE(NULLIF(SBZ.BZ_ESTSEG, 0), NULLIF(SB1.B1_EMIN, 0)) AS minimum_stock,
    (SB2.B2_QATU - SB2.B2_QEMP - ISNULL(SB2.B2_RESERVA, 0)) AS available_quantity
FROM SB2010 SB2
INNER JOIN SB1010 SB1
    ON SB1.B1_COD = SB2.B2_COD
    AND SB1.D_E_L_E_T_ = ''
LEFT JOIN SBZ010 SBZ
    ON SBZ.BZ_COD = SB2.B2_COD
    AND SBZ.BZ_FILIAL = SB2.B2_FILIAL
    AND SBZ.D_E_L_E_T_ = ''
WHERE SB2.D_E_L_E_T_ = ''
  AND COALESCE(NULLIF(SBZ.BZ_ESTSEG, 0), NULLIF(SB1.B1_EMIN, 0)) > 0
  AND SB2.B2_QATU < COALESCE(NULLIF(SBZ.BZ_ESTSEG, 0), NULLIF(SB1.B1_EMIN, 0)){branch_filter}
ORDER BY
    SB2.B2_FILIAL,
    SB2.B2_QATU ASC,
    SB2.B2_COD"""
