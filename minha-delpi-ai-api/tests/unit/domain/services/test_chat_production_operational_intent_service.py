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


def test_resolve_work_center_summary_before_consumption_by_ct() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Resumo de OPs por centro de trabalho hoje"
    )
    assert kind == ProductionOperationalIntentKind.WORK_CENTER_SUMMARY


def test_resolve_consumption_by_work_center_still_matches() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Itens com maior consumo por centro de trabalho mês passado top 10"
    )
    assert kind == ProductionOperationalIntentKind.CONSUMPTION_BY_WORK_CENTER


def test_resolve_consumption_validated_with_top_limit() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Consumo validado por apontamento no mês top 10"
    )
    assert kind == ProductionOperationalIntentKind.CONSUMPTION_VALIDATED


def test_resolve_allocation_gaps_intent() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Liste componentes sem empenho hoje filial 01"
    )
    assert kind == ProductionOperationalIntentKind.ALLOCATION_GAPS


def test_resolve_finished_without_consumption_intent() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Quais OPs finalizadas sem consumo hoje?"
    )
    assert kind == ProductionOperationalIntentKind.FINISHED_WITHOUT_CONSUMPTION


def test_resolve_average_planned_time_intent() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Tempo médio planejado por CT hoje"
    )
    assert kind == ProductionOperationalIntentKind.AVERAGE_PLANNED_TIME


def test_resolve_consumption_by_item_requires_code() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Consumo real do item 01010001"
    )
    assert kind == ProductionOperationalIntentKind.CONSUMPTION_BY_ITEM


def test_consumption_by_item_without_code_does_not_match_by_item() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Consumo real do item no mês"
    )
    assert kind != ProductionOperationalIntentKind.CONSUMPTION_BY_ITEM


def test_resolve_planned_vs_real_time_intent() -> None:
    kind = ChatProductionOperationalIntentService.resolve(
        "Compare tempo planejado e tempo real das OPs hoje filial 01"
    )
    assert kind == ProductionOperationalIntentKind.PLANNED_VS_REAL_TIME
