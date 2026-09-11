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


def test_production_and_kpi_dials_default_off() -> None:
    assert ChatConversationalIntelligenceFlagService.production_family_cutover_enabled() is False
    assert ChatConversationalIntelligenceFlagService.kpi_family_cutover_enabled() is False
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


def test_production_resolve_parity_when_dial_off() -> None:
    message = "programação de produção hoje"
    assert ChatProductionOperationalIntentService.resolve(message) == (
        ChatProductionOperationalIntentService.resolve(message, force_legacy=True)
    )


def test_production_resolve_uses_mapper_when_dial_on() -> None:
    message = "programação de produção hoje"
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "production_family_cutover_enabled",
        return_value=True,
    ):
        assert (
            ChatProductionOperationalIntentService.resolve(message)
            == ProductionOperationalIntentKind.SCHEDULE_TODAY
        )


def test_kpi_mapper_rol_and_closing_rate() -> None:
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


def test_kpi_resolve_parity_when_dial_off() -> None:
    message = "qual o ebitda do último trimestre"
    assert ChatDepartmentKpiIntentService.resolve(message) == (
        ChatDepartmentKpiIntentService.resolve(message, force_legacy=True)
    )


def test_authority_shadow_candidates_production_kpi() -> None:
    contract = ChatTurnUnderstandingService.analyze("programação de produção hoje")
    shadow = TurnUnderstandingAuthorityShadowService.compare(
        "programação de produção hoje",
        contract,
    )
    assert shadow is not None
    assert shadow["cutoverProduction"] is False
    assert shadow["cutoverKpi"] is False
    assert shadow["candidateProductionKind"] == "SCHEDULE_TODAY"
    assert shadow["productionKind"] == "SCHEDULE_TODAY"
