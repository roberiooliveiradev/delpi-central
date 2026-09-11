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

    # E11.S6 KEEP — ProductionOperationalIntentKind (semântico); pathTokens JSON removidos.
    _TOKEN_RULES: tuple[tuple[ProductionOperationalIntentKind, tuple[str, ...]], ...] = (
        (
            ProductionOperationalIntentKind.LOSSES_RECORDS,
            ("registros de perda", "perda registrada", "lancamento de perda"),
        ),
        (
            ProductionOperationalIntentKind.FINISHED_WITHOUT_CONSUMPTION,
            (
                "finalizadas sem consumo",
                "finalizada sem consumo",
                "ops finalizadas sem",
                "sem consumo",
            ),
        ),
        (
            ProductionOperationalIntentKind.CONSUMPTION_BY_ITEM,
            ("consumo real do item", "consumo do item", "consumo do produto", "consumo por item"),
        ),
        (
            ProductionOperationalIntentKind.ALLOCATION_GAPS,
            ("alocacao", "alocação", "gap de aloc", "sem empenho"),
        ),
        (
            ProductionOperationalIntentKind.PLANNED_VS_REAL_TIME,
            ("planejado vs real", "tempo planejado versus", "previsto vs realizado", "tempo planejado e tempo real"),
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
            (
                "ops abertas",
                "ordens abertas",
                "op aberta",
                "ordens em aberto",
                "ops em aberto",
                "op em aberto",
                "ops em aberto hoje",
            ),
        ),
        (
            ProductionOperationalIntentKind.SCHEDULE_TODAY,
            (
                "programacao de producao",
                "programação de produção",
                "programados",
                "programado",
                "na programacao",
                "na programação",
                "programacao hoje",
                "programação hoje",
                "cronograma de producao",
                "cronograma de produção",
                "produzir hoje",
            ),
        ),
        (
            ProductionOperationalIntentKind.PURCHASES_RANKING,
            (
                "ranking de compra",
                "mais comprados",
                "mais compras",
                "compras ranking",
                "produtos mais compras",
                "itens mais compras",
            ),
        ),
        (
            ProductionOperationalIntentKind.CONSUMPTION,
            (
                "maior consumo",
                "consumo de mp",
                "consumo de materia",
                "mais consumidos",
                "itens mais consumidos",
                "consumo",
            ),
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
        "consumid",
        "compra",
        "compras",
        "comprad",
        "perda",
        "refugo",
        "sucata",
        "op ",
        "ops ",
        "ordem",
        "ordens",
        "aloc",
        "empenho",
        "centro de trabalho",
        "schedule",
        "ct ",
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

        # Mirror legacy: product+OP status questions are not ORDERS_OPEN.
        if cls._looks_like_product_production_status(user_goal, contract):
            return None

        for goal in contract.goals:
            mapped = cls.from_goal_prose(str(goal.intent or ""), contract=contract)
            if mapped is not None:
                return mapped
        return cls.from_goal_prose(user_goal, contract=contract)

    @classmethod
    def from_goal_prose(
        cls,
        prose: str,
        *,
        contract: TurnUnderstanding | None = None,
    ) -> ProductionOperationalIntentKind | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(prose)
        if not normalized:
            return None

        for kind, tokens in cls._TOKEN_RULES:
            matched = False
            for token in tokens:
                needle = ChatMessageNormalizationService.normalize_for_matching(token)
                if needle and needle in normalized:
                    matched = True
                    break
            if not matched:
                continue

            if kind == ProductionOperationalIntentKind.ORDERS_FINISHED and "sem consumo" in normalized:
                continue

            if kind == ProductionOperationalIntentKind.CONSUMPTION_BY_ITEM:
                if not cls._has_product_code(contract, normalized):
                    continue

            if kind == ProductionOperationalIntentKind.CONSUMPTION and cls._has_product_code(
                contract, normalized
            ):
                # Prefer by-item when a code is present and prose looks item-scoped.
                if "item" in normalized or "produto" in normalized:
                    continue

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

    @classmethod
    def _has_product_code(
        cls,
        contract: TurnUnderstanding | None,
        normalized: str,
    ) -> bool:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        if contract is not None:
            for goal in contract.goals:
                if str(goal.entities.get("productCode") or "").strip():
                    return True
        return bool(ChatProductQueryIntentService.extract_product_code(normalized))

    @classmethod
    def _looks_like_product_production_status(
        cls,
        normalized: str,
        contract: TurnUnderstanding,
    ) -> bool:
        if not cls._has_product_code(contract, normalized):
            return False
        status_markers = ("iniciou", "status", "ja inici", "já inici", "producao?", "produção?")
        return any(marker in normalized for marker in status_markers) or (
            "op aberta" in normalized and "hoje" in normalized
        )
