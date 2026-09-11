"""E2.S4 — map Turn Understanding goals → production operational kind."""

from __future__ import annotations

from app.domain.entities.turn_understanding import TurnUnderstanding
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ProductionOperationalIntentKind,
)


class TurnUnderstandingProductionIntentMapperService:
    """Derives ProductionOperationalIntentKind from TU prose (no OpenAPI)."""

    _TOKEN_RULES: tuple[tuple[ProductionOperationalIntentKind, tuple[str, ...]], ...] = (
        (
            ProductionOperationalIntentKind.LOSSES_RECORDS,
            ("registros de perda", "perda registrada", "lancamento de perda"),
        ),
        (
            ProductionOperationalIntentKind.CONSUMPTION_BY_ITEM,
            ("consumo do item", "consumo do produto", "consumo por item"),
        ),
        (
            ProductionOperationalIntentKind.ALLOCATION_GAPS,
            ("alocacao", "alocação", "gap de aloc"),
        ),
        (
            ProductionOperationalIntentKind.FINISHED_WITHOUT_CONSUMPTION,
            ("finalizada sem consumo", "terminada sem consumo"),
        ),
        (
            ProductionOperationalIntentKind.PLANNED_VS_REAL_TIME,
            ("planejado vs real", "tempo planejado versus", "previsto vs realizado"),
        ),
        (
            ProductionOperationalIntentKind.AVERAGE_PLANNED_TIME,
            ("tempo medio planejado", "tempo médio planejado"),
        ),
        (
            ProductionOperationalIntentKind.CONSUMPTION_BY_WORK_CENTER,
            ("consumo por centro", "consumo no centro"),
        ),
        (
            ProductionOperationalIntentKind.CONSUMPTION_VALIDATED,
            ("consumo validado", "consumo confirmado"),
        ),
        (
            ProductionOperationalIntentKind.WORK_CENTER_SUMMARY,
            ("resumo do centro", "centro de trabalho"),
        ),
        (
            ProductionOperationalIntentKind.ORDERS_FINISHED,
            ("ops finalizadas", "ordens finalizadas", "ops terminadas"),
        ),
        (
            ProductionOperationalIntentKind.ORDERS_OPEN,
            ("ops abertas", "ordens abertas", "op aberta", "ordens em aberto"),
        ),
        (
            ProductionOperationalIntentKind.SCHEDULE_TODAY,
            (
                "programacao de producao",
                "programação de produção",
                "programados",
                "programacao hoje",
                "programação hoje",
                "cronograma de producao",
                "cronograma de produção",
                "produzir hoje",
            ),
        ),
        (
            ProductionOperationalIntentKind.PURCHASES_RANKING,
            ("ranking de compra", "mais comprados", "compras ranking"),
        ),
        (
            ProductionOperationalIntentKind.CONSUMPTION,
            ("maior consumo", "consumo de mp", "consumo de materia", "consumo"),
        ),
        (
            ProductionOperationalIntentKind.LOSSES_TOP,
            ("maiores perdas", "top perdas", "perda", "refugo", "sucata"),
        ),
    )

    _GROUNDING: tuple[str, ...] = (
        "produc",
        "program",
        "cronograma",
        "consumo",
        "perda",
        "refugo",
        "sucata",
        "op ",
        "ops ",
        "ordem",
        "ordens",
        "aloc",
        "centro de trabalho",
        "schedule",
    )

    @classmethod
    def from_understanding(
        cls,
        contract: TurnUnderstanding | None,
    ) -> ProductionOperationalIntentKind | None:
        if contract is None or not contract.goals:
            return None

        user_goal = ChatMessageNormalizationService.normalize_for_matching(
            str(contract.user_goal or "")
        )
        if not cls._is_production_grounded(user_goal):
            return None

        # "agenda de produção" is intentionally not scheduleToday (parity w/ legacy).
        if "agenda" in user_goal and "program" not in user_goal:
            return None

        for goal in contract.goals:
            mapped = cls.from_goal_prose(str(goal.intent or ""))
            if mapped is not None:
                return mapped
        return cls.from_goal_prose(user_goal)

    @classmethod
    def from_goal_prose(cls, prose: str) -> ProductionOperationalIntentKind | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(prose)
        if not normalized:
            return None
        for kind, tokens in cls._TOKEN_RULES:
            if any(token in normalized for token in tokens):
                return kind
        return None

    @classmethod
    def from_message(cls, message: str) -> ProductionOperationalIntentKind | None:
        from app.domain.services.chat_turn_understanding_service import (
            ChatTurnUnderstandingService,
        )

        return cls.from_understanding(ChatTurnUnderstandingService.analyze(message))

    @classmethod
    def _is_production_grounded(cls, normalized: str) -> bool:
        return any(marker in normalized for marker in cls._GROUNDING)
