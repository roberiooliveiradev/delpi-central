"""E2.S4 — production/KPI family cutover dials (default OFF) + TU mappers."""

from __future__ import annotations

from unittest.mock import patch

from app.domain.services.chat_conversational_intelligence_flag_service import (
    ChatConversationalIntelligenceFlagService,
)
from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)
from app.domain.services.chat_turn_understanding_service import ChatTurnUnderstandingService
from app.domain.services.turn_understanding_authority_shadow_service import (
    TurnUnderstandingAuthorityShadowService,
)
from app.domain.services.turn_understanding_kpi_intent_mapper_service import (
    TurnUnderstandingKpiIntentMapperService,
)
from app.domain.services.turn_understanding_production_intent_mapper_service import (
    TurnUnderstandingProductionIntentMapperService,
)


def test_production_and_kpi_dials_default_on_for_canary() -> None:
    assert ChatConversationalIntelligenceFlagService.production_family_cutover_enabled() is True
    assert ChatConversationalIntelligenceFlagService.kpi_family_cutover_enabled() is True
    assert ChatConversationalIntelligenceFlagService.product_family_cutover_enabled() is True


def test_production_mapper_schedule_today() -> None:
    kind = TurnUnderstandingProductionIntentMapperService.from_message(
        "programação de produção hoje"
    )
    assert kind == ProductionOperationalIntentKind.SCHEDULE_TODAY


def test_production_mapper_negative_agenda() -> None:
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message("agenda de produção")
        is None
    )


def test_production_mapper_sibling_orders_open() -> None:
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message("ops abertas")
        == ProductionOperationalIntentKind.ORDERS_OPEN
    )


def test_production_mapper_consumption_and_purchases() -> None:
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message(
            "Quais itens mais consumidos no mês?"
        )
        == ProductionOperationalIntentKind.CONSUMPTION
    )
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message(
            "Liste os produtos mais comprados em março"
        )
        == ProductionOperationalIntentKind.PURCHASES_RANKING
    )


def test_production_resolve_uses_mapper_on_canary() -> None:
    message = "programação de produção hoje"
    assert (
        ChatProductionOperationalIntentService.resolve(message)
        == ProductionOperationalIntentKind.SCHEDULE_TODAY
    )
    assert ChatProductionOperationalIntentService.resolve(
        message, force_legacy=True
    ) == ProductionOperationalIntentKind.SCHEDULE_TODAY


def test_production_mapper_membership_schedule_with_code() -> None:
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message(
            "O produto 90260255 está na programação de hoje?"
        )
        == ProductionOperationalIntentKind.SCHEDULE_TODAY
    )
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message(
            "O chicote 90261486 está programado hoje?"
        )
        == ProductionOperationalIntentKind.SCHEDULE_TODAY
    )


def test_production_mapper_ops_em_aberto() -> None:
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message(
            "Quais OPs em aberto hoje na filial 01?"
        )
        == ProductionOperationalIntentKind.ORDERS_OPEN
    )


def test_production_resolve_mapper_first_with_fallback() -> None:
    message = "O produto 90260255 está na programação de hoje?"
    assert (
        ChatProductionOperationalIntentService.resolve(message)
        == ProductionOperationalIntentKind.SCHEDULE_TODAY
    )
    # agenda: mapper None → fallback legado None
    assert ChatProductionOperationalIntentService.resolve("agenda de produção") is None


def test_kpi_mapper_meta_comercial_and_oee() -> None:
    meta = TurnUnderstandingKpiIntentMapperService.from_message(
        "qual a meta comercial deste mês"
    )
    assert meta is not None
    assert meta.path_token == "rol/summary"

    oee = TurnUnderstandingKpiIntentMapperService.from_message("como está o oee da fábrica")
    assert oee is not None
    assert oee.path_token == "oee"

    rol = TurnUnderstandingKpiIntentMapperService.from_message(
        "qual o rol financeiro do mes"
    )
    assert rol is not None
    assert rol.path_token == "/financial/rol"

    closing = TurnUnderstandingKpiIntentMapperService.from_message(
        "taxa de conversão de vendas"
    )
    assert closing is not None
    assert closing.path_token == "closing-rate"


def test_kpi_mapper_negative_product_code() -> None:
    assert (
        TurnUnderstandingKpiIntentMapperService.from_message(
            "estoque do produto 10080001"
        )
        is None
    )


def test_kpi_resolve_uses_mapper_on_canary() -> None:
    message = "qual o ebitda do último trimestre"
    live = ChatDepartmentKpiIntentService.resolve(message)
    legacy = ChatDepartmentKpiIntentService.resolve(message, force_legacy=True)
    assert live is not None and legacy is not None
    assert live.path_token == legacy.path_token == "ebitda"


def test_authority_shadow_candidates_production_kpi() -> None:
    contract = ChatTurnUnderstandingService.analyze("programação de produção hoje")
    shadow = TurnUnderstandingAuthorityShadowService.compare(
        "programação de produção hoje",
        contract,
    )
    assert shadow is not None
    assert shadow["cutoverProduction"] is True
    assert shadow["cutoverKpi"] is True
    assert shadow["candidateProductionKind"] == "SCHEDULE_TODAY"
    assert shadow["productionKind"] == "SCHEDULE_TODAY"


def test_dials_off_restore_legacy_parity() -> None:
    message = "programação de produção hoje"
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "production_family_cutover_enabled",
        return_value=False,
    ), patch.object(
        ChatConversationalIntelligenceFlagService,
        "kpi_family_cutover_enabled",
        return_value=False,
    ):
        assert ChatProductionOperationalIntentService.resolve(message) == (
            ChatProductionOperationalIntentService.resolve(message, force_legacy=True)
        )
        assert ChatDepartmentKpiIntentService.resolve(
            "qual o ebitda do último trimestre"
        ) == ChatDepartmentKpiIntentService.resolve(
            "qual o ebitda do último trimestre",
            force_legacy=True,
        )