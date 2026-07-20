import pytest

from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def test_department_kpi_rules_loaded_from_json() -> None:
    bundle = ChatAssistantContentService.load_bundle("department_kpi_rules")
    rules = bundle.get("rules")

    assert isinstance(rules, list)
    assert len(rules) >= 30


def test_resolve_ebitda_with_typo():
    match = ChatDepartmentKpiIntentService.resolve("qual o ebita do trimestre")

    assert match is not None
    assert "ebitda" in match.path_token
    assert match.domain_prefix == "/financial/"


def test_resolve_commercial_closing_rate():
    match = ChatDepartmentKpiIntentService.resolve("taxa de conversao de vendas")

    assert match is not None
    assert "closing-rate" in match.path_token


def test_resolve_financial_rol():
    match = ChatDepartmentKpiIntentService.resolve("qual o rol financeiro do mes")

    assert match is not None
    assert "rol" in match.path_token


def test_resolve_quality_kaizen_typo():
    match = ChatDepartmentKpiIntentService.resolve("resumo de kaisen")

    assert match is not None
    assert "kaizens" in match.path_token


def test_skips_when_product_code_present():
    match = ChatDepartmentKpiIntentService.resolve("ebitda do produto 10080047")

    assert match is None


def test_skips_supplies_cpv():
    match = ChatDepartmentKpiIntentService.resolve("qual o cpv da filial")

    assert match is None


def test_resolve_financial_rol_for_month_question():
    match = ChatDepartmentKpiIntentService.resolve("rol do mes de marco")

    assert match is not None
    assert match.path_token == "/financial/rol"
    assert match.domain_prefix == "/financial/"


def test_resolve_financial_rol_qual_foi_da_empresa():
    match = ChatDepartmentKpiIntentService.resolve(
        "Qual foi o ROL da empresa em março de 2026?"
    )

    assert match is not None
    assert match.path_token == "/financial/rol"


def test_resolve_rol_series_only_for_explicit_series():
    match = ChatDepartmentKpiIntentService.resolve("serie de rol no tempo")

    assert match is not None
    assert "rol/series" in match.path_token


def test_resolve_audit_5s_operational_nc():
    match = ChatDepartmentKpiIntentService.resolve("listar nc 5s operacional")

    assert match is not None
    assert match.domain_prefix == "/quality/audit-5s/"
    assert match.path_token == "nonconformities"


def test_resolve_audit_5s_operational_audits():
    match = ChatDepartmentKpiIntentService.resolve("listar auditorias 5s da filial")

    assert match is not None
    assert match.domain_prefix == "/quality/audit-5s/"
    assert match.path_token == "audits"


def test_resolve_eficiencia_fabril_dashboard():
    match = ChatDepartmentKpiIntentService.resolve(
        "dashboard eficiencia fabril com resultado mod"
    )

    assert match is not None
    assert match.path_token == "eficiencia-fabril"
    assert match.domain_prefix == "/production/"


def test_resolve_production_oee_apontamentos():
    match = ChatDepartmentKpiIntentService.resolve("listar apontamentos oee fora da faixa")

    assert match is not None
    assert match.path_token == "oee"
    assert match.domain_prefix == "/production/"


def test_resolve_commercial_branch_rol_target_meta_percentual_filial():
    match = ChatDepartmentKpiIntentService.resolve(
        "Qual é a meta percentual de ROL da filial?"
    )

    assert match is not None
    assert match.path_token == "branch_rol_target"
    assert match.domain_prefix == "/commercial/"


def test_resolve_commercial_head_office_meta_para_comercial_desse_mes():
    from app.domain.services.chat_department_kpi_intent_service import (
        invalidate_department_kpi_rules_cache,
    )

    invalidate_department_kpi_rules_cache()
    match = ChatDepartmentKpiIntentService.resolve(
        "qual a meta para comercial desse mês?"
    )

    assert match is not None
    assert match.path_token == "head_office_rol_target"
    assert match.domain_prefix == "/commercial/"


def test_resolve_commercial_branch_meta_comercial_da_filial():
    from app.domain.services.chat_department_kpi_intent_service import (
        invalidate_department_kpi_rules_cache,
    )

    invalidate_department_kpi_rules_cache()
    match = ChatDepartmentKpiIntentService.resolve(
        "qual a meta comercial da filial?"
    )

    assert match is not None
    assert match.path_token == "branch_rol_target"


def test_resolve_commercial_branch_meta_para_comercial_com_filial_02():
    from app.domain.services.chat_department_kpi_intent_service import (
        invalidate_department_kpi_rules_cache,
    )

    invalidate_department_kpi_rules_cache()
    match = ChatDepartmentKpiIntentService.resolve(
        "qual a meta para comercial desse mês filial 02?"
    )

    assert match is not None
    assert match.path_token == "branch_rol_target"
    assert match.domain_prefix == "/commercial/"


@pytest.mark.parametrize(
    "message,expected_token,expected_prefix",
    [
        ("qual a meta para financeiro desse mês?", "ebitda", "/financial/"),
        ("qual a meta para produção desse mês?", "oee", "/production/"),
        ("qual a meta para qualidade desse mês?", "ppm/internal", "/quality/"),
        ("qual a meta para rh desse mês?", "snapshot", "/hr/"),
        ("qual a meta custo fixo?", "fixed_cost", "/financial/"),
        ("qual a meta otd de produção?", "on_time_delivery", "/production/"),
        ("qual a meta ppm externo?", "ppm/external", "/quality/"),
        ("qual a meta pdi?", "active-pdi", "/hr/"),
    ],
)
def test_resolve_colloquial_meta_other_departments(
    message: str,
    expected_token: str,
    expected_prefix: str,
) -> None:
    from app.domain.services.chat_department_kpi_intent_service import (
        invalidate_department_kpi_rules_cache,
    )

    invalidate_department_kpi_rules_cache()
    match = ChatDepartmentKpiIntentService.resolve(message)

    assert match is not None
    assert match.path_token == expected_token
    assert match.domain_prefix == expected_prefix


def test_branch_rol_target_question_is_not_capability_inquiry():
    from app.application.services.chat_capabilities_service import ChatCapabilitiesService

    message = "Qual é a meta percentual de ROL da filial?"

    assert ChatDepartmentKpiIntentService.resolve(message) is not None
    assert ChatCapabilitiesService.is_capability_inquiry(message) is False
