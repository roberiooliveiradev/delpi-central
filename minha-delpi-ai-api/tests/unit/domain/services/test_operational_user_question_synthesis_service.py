from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_user_question_synthesis_service import (
    ChatOperationalUserQuestionSynthesisService,
)
from app.domain.services.chat_production_schedule_membership_presentation_service import (
    ChatProductionScheduleMembershipPresentationService,
)

configure_domain_infrastructure_ports()


def test_synthesis_schedule_membership_yes():
    data = {
        "reference_date": "20260617",
        "query_context": {"product_code_prefix": "90261486"},
        "items": [
            {
                "product_code": "90261486",
                "production_order": "2400012345",
                "planned_qty": 120,
                "unit": "UN",
            }
        ],
    }

    result = ChatOperationalUserQuestionSynthesisService.try_synthesize(
        "O chicote 90261486 está programado hoje?",
        data,
        entity="production_schedule_today",
    )

    assert result is not None
    assert result["intent"] == "schedule_membership"
    assert "Sim" in result["summary"]
    assert "90261486" in result["summary"]


def test_synthesis_structure_exclusivity_no():
    data = {
        "product": {"product_code": "90261805", "description": "CHICOTE"},
        "summary": {
            "total_components": 3,
            "total_intermediates": 1,
            "total_raw_materials": 2,
            "total_exclusive_raw_materials": 0,
        },
        "items": [],
    }

    result = ChatOperationalUserQuestionSynthesisService.try_synthesize(
        "Tem MP exclusiva na estrutura do 90261805?",
        data,
        profile_key="structure_exclusivity",
        entity="product_structure_exclusivity",
    )

    assert result is not None
    assert "Não" in result["summary"]
    assert "90261805" in result["summary"]


def test_synthesis_structure_exclusivity_yes_names_mp():
    data = {
        "product": {"product_code": "90269002", "description": "PRODUTO FICTICIO FABRIL"},
        "summary": {
            "total_components": 2,
            "total_intermediates": 1,
            "total_raw_materials": 1,
            "total_exclusive_raw_materials": 1,
        },
        "items": [
            {
                "level": 2,
                "component_type": "MP",
                "product_code": "10019001",
                "description": "MATERIA PRIMA FICTICIA",
                "exclusive_raw_material": "SIM",
            }
        ],
    }

    result = ChatOperationalUserQuestionSynthesisService.try_synthesize(
        "Quais MPs compõem a estrutura do 90269002? Tem MP exclusiva?",
        data,
        profile_key="structure_exclusivity",
        entity="product_structure_exclusivity",
    )

    assert result is not None
    assert "10019001" in result["summary"]
    assert "MATERIA PRIMA FICTICIA" in result["summary"]
    assert "Sim" in result["summary"]


def test_synthesis_production_status_situacao():
    data = {
        "product": {"product_code": "90260255"},
        "reference_date": "20260617",
        "summary": {
            "total_pa_orders": 1,
            "total_pi_orders": 0,
            "pa_production_started": "SIM",
            "pi_production_started": "NAO",
            "total_pa_reported_quantity": 0,
            "total_pi_reported_quantity": 0,
        },
        "items": [],
    }

    result = ChatOperationalUserQuestionSynthesisService.try_synthesize(
        "Situação produtiva do 90260255 na data de hoje.",
        data,
        profile_key="production_status",
    )

    assert result is not None
    assert "90260255" in result["summary"]
    assert "Sim" in result["summary"] or "SIM" in result["summary"]


def test_synthesis_production_open_op_not_started():
    data = {
        "reference_date": "20260617",
        "summary": {"total_pa_orders": 1},
        "items": [
            {
                "level": 0,
                "product_type": "PA",
                "product_code": "90260255",
                "production_order": "10448501001",
                "production_started": "NAO",
                "reported_quantity": 0,
            }
        ],
    }

    result = ChatOperationalUserQuestionSynthesisService.try_synthesize(
        "O 90260255 tem OP aberta hoje?",
        data,
        profile_key="production_status",
    )

    assert result is not None
    assert "10448501001" in result["summary"]


def test_membership_service_aligns_with_synthesis():
    root = {
        "reference_date": "20260617",
        "items": [
            {
                "product_code": "90261486",
                "production_order": "2400012345",
                "planned_qty": 120,
                "unit": "UN",
            }
        ],
    }

    report = ChatProductionScheduleMembershipPresentationService.try_build_membership_answer(
        root,
        message="O chicote 90261486 está programado hoje?",
    )
    synthesis = ChatOperationalUserQuestionSynthesisService.try_synthesize(
        "O chicote 90261486 está programado hoje?",
        root,
        entity="production_schedule_today",
    )

    assert report is not None
    assert synthesis is not None
    assert report["linhas"][0] in synthesis["summary"] or synthesis["summary"] in report["linhas"][0]
