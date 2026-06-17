from app.domain.services.chat_production_schedule_membership_presentation_service import (
    ChatProductionScheduleMembershipPresentationService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)


def test_schedule_membership_intent_resolves():
    message = "O produto 90260255 está na programação de hoje? Qual OP e quantidade?"

    assert (
        ChatProductionOperationalIntentService.resolve(message)
        == ProductionOperationalIntentKind.SCHEDULE_TODAY
    )


def test_membership_playbook_report_found():
    root = {
        "reference_date": "20260617",
        "query_context": {"product_code_prefix": "90260255"},
        "items": [
            {
                "product_code": "90260255",
                "production_order": "10448501001",
                "planned_qty": 1200,
                "unit": "UN",
                "branch": "01",
            }
        ],
    }

    report = ChatProductionScheduleMembershipPresentationService.try_build_playbook_report(
        root,
        entity="production_schedule_today",
    )

    assert report is not None
    assert "90260255" in report["titulo"]
    assert any("10448501001" in line for line in report["linhas"])
    assert any("Sim" in line for line in report["linhas"])


def test_membership_playbook_report_not_found():
    root = {
        "reference_date": "20260617",
        "query_context": {"product_code_prefix": "90260255"},
        "items": [],
    }

    report = ChatProductionScheduleMembershipPresentationService.try_build_playbook_report(
        root,
        entity="production_schedule_today",
    )

    assert report is not None
    assert any("Não" in line for line in report["linhas"])


def test_resolve_detail_filter_for_chicote_membership_question():
    message = "O chicote 90261486 está programado hoje?"

    detail_filter = ChatProductionScheduleMembershipPresentationService.resolve_detail_filter(
        message,
        path="/production/schedule/today",
    )

    assert detail_filter == {"product_code_prefix": "90261486"}


def test_membership_answer_from_message_without_query_context():
    root = {
        "reference_date": "2026-06-16",
        "items": [
            {
                "product_code": "90261486",
                "production_order": "2400012345",
                "planned_qty": 120,
                "unit": "PA",
            }
        ],
    }

    report = ChatProductionScheduleMembershipPresentationService.try_build_membership_answer(
        root,
        message="O chicote 90261486 está programado hoje?",
    )

    assert report is not None
    assert "90261486" in report["titulo"]
    assert any("2400012345" in line for line in report["linhas"])


def test_membership_answer_from_sql_rows():
    root = {
        "query_context": {"product_code_prefix": "90261486"},
        "items": [
            {
                "COD_PRODUTO": "90261486",
                "C2_OP": "10405001001",
                "QTD_PLANEJADA": 500,
                "UNIDADE": "UN",
                "FILIAL": "01",
            }
        ],
    }

    report = ChatProductionScheduleMembershipPresentationService.try_build_membership_answer(
        root
    )

    assert report is not None
    assert any("10405001001" in line for line in report["linhas"])
