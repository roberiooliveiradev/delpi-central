from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)


def test_resolve_consumption_intent() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Quais itens mais consumidos no mês?"
    )
    assert kind == ProductionOperationalIntentKind.CONSUMPTION


def test_resolve_purchases_ranking_intent() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Liste os produtos mais comprados em março"
    )
    assert kind == ProductionOperationalIntentKind.PURCHASES_RANKING


def test_resolve_schedule_today_intent() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Quais produtos estão programados para produzir hoje?"
    )
    assert kind == ProductionOperationalIntentKind.SCHEDULE_TODAY


def test_consumption_excludes_purchases() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Produtos mais comprados no período"
    )
    assert kind == ProductionOperationalIntentKind.PURCHASES_RANKING


def test_infer_loss_type_refugo() -> None:
    loss_type = ChatProductionOperationalIntentService.infer_loss_type(
        "refugo de materia prima em marco"
    )
    assert loss_type == "refugo"
