"""Facts contract F-LMP-01..04 — unit, envelope, auth e paridade (doc 34).

SYNTHETIC_TEST_FIXTURE: todas as linhas/entidades são sintéticas; paridade é
verificada no nível do mapper/select compartilhado com o dashboard, não contra
dados reais de produção.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.use_cases.lmp.lmp_facts_use_cases import (
    FACTS_PAGE_SIZE_MAX,
    FACTS_PI_COUNT_BATCH_MAX,
    GetLmpFactUseCase,
    GetLmpFactsHistoryUseCase,
    GetLmpPiCountsUseCase,
    ListLmpFactsUseCase,
)
from app.domain.entities.lmp.lmp import LMP
from app.domain.entities.lmp.lmp_history_event import LMPHistoryEvent
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_repository import (
    LMPQueryRepository,
)
from app.interface.http.routes.engineering.lmp_facts_router import (
    LmpPiCountsBody,
    get_lmp_fact_route,
    get_lmp_facts_history_events_route,
    get_lmp_facts_history_flow_route,
    get_lmp_pi_counts_route,
    list_lmp_facts_route,
)
from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceScopeDeniedError,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

ROUTER_MODULE = "app.interface.http.routes.engineering.lmp_facts_router"

FORBIDDEN_FACT_KEYS = {
    "dashboard_status",
    "status",
    "nivel",
    "level",
    "sla_days",
    "data_limite",
    "lead_time",
    "percentual_no_prazo",
    "goal_value",
    "idd",
}


def _fact_row(**overrides) -> dict:
    """SYNTHETIC_TEST_FIXTURE — linha como projetada por _staged_facts_select."""
    base = {
        "branch": "01",
        "sale_number": "OV001",
        "sale_description": " Projeto Alpha ",
        "listing_kind_source": "LMP",
        "listing_kind": "LMP",
        "has_sample_anchor": 0,
        "has_lmp_finalized": 1,
        "sample_eng_minutes": 0,
        "residence_minutes": 120,
        "start_date": "20260501",
        "end_date": "20260510",
        "homolog_revision": "001",
        "measurement_revision": "002",
        "homolog_date": "20260501",
        "cycle_index": 1,
        "engineering_status": "FINALIZADA",
        "qtd_engineering_entries": 2,
        "qtd_engineering_closed": 2,
        "qtd_advanced_from_engineering": 1,
        "qtd_returned_from_engineering": 0,
        "qtd_pi": 5,
    }
    base.update(overrides)
    return base


def _lmp_entity(**overrides) -> LMP:
    base = {
        "branch": "01",
        "sale_number": "OV001",
        "sale_description": "Projeto Alpha",
        "listing_kind": "LMP",
        "start_date": "20260501",
        "end_date": "20260510",
        "engineering_status": "FINALIZADA",
        "engineering_total_minutes": 120,
        "qtd_pi": 5,
    }
    base.update(overrides)
    return LMP(**base)


def _history_event(**overrides) -> LMPHistoryEvent:
    base = {
        "revision": "001",
        "process_code": "000003",
        "stage_code": "000003",
        "stage_description": "Engenharia",
        "start_date": "20260501",
        "end_date": "20260502",
    }
    base.update(overrides)
    return LMPHistoryEvent(**base)


# ---------------------------------------------------------------------------
# F-LMP-01 — ListLmpFactsUseCase
# ---------------------------------------------------------------------------


def test_list_facts_paginates_and_exposes_policy_provenance() -> None:
    repository = MagicMock()
    repository.get_lmp_facts.return_value = [
        _fact_row(sale_number=f"OV{i:03d}") for i in range(3)
    ]

    result = ListLmpFactsUseCase(repository).execute(
        ListLMPRequest(date_start="20260501", date_end="20260531", page_size=2)
    )

    repository.get_lmp_facts.assert_called_once()
    assert result["total"] == 3
    assert result["page_size"] == 2
    assert result["total_pages"] == 2
    assert len(result["items"]) == 2
    assert result["provenance"]["source_system"] == "TOTVS"
    assert result["provenance"]["integration_owner"] == "api-delpi"
    assert result["policy"]["listing_type_filter_semantics"] == "effective"
    assert result["items"][0]["start_date"] == "2026-05-01"


def test_list_facts_caps_page_size() -> None:
    repository = MagicMock()
    repository.get_lmp_facts.return_value = []

    result = ListLmpFactsUseCase(repository).execute(
        ListLMPRequest(page_size=99999)
    )

    assert result["page_size"] == FACTS_PAGE_SIZE_MAX
    assert result["items"] == []
    assert result["total"] == 0


def test_fact_items_do_not_carry_business_rule_outputs() -> None:
    """LMP-G2-10: nenhum KPI/nível/status de dashboard nos facts."""
    repository = MagicMock()
    repository.get_lmp_facts.return_value = [_fact_row()]

    result = ListLmpFactsUseCase(repository).execute(ListLMPRequest())

    emitted_keys = set(result["items"][0].keys())
    assert emitted_keys.isdisjoint(FORBIDDEN_FACT_KEYS)


# ---------------------------------------------------------------------------
# F-LMP-02 — GetLmpFactUseCase
# ---------------------------------------------------------------------------


def test_get_fact_detail_strips_history_by_default() -> None:
    repository = MagicMock()
    repository.get_lmp.return_value = _lmp_entity(
        list_history=[_history_event()],
    )

    result = GetLmpFactUseCase(repository).execute(
        GetLMPRequest(sale_number="OV001")
    )

    repository.get_lmp_history_events.assert_not_called()
    assert result["list_history"] == []
    assert result["list_products"] == []
    assert result["provenance"]["integration_owner"] == "api-delpi"


def test_get_fact_detail_include_history_fetches_events() -> None:
    repository = MagicMock()
    repository.get_lmp.return_value = _lmp_entity()
    repository.get_lmp_history_events.return_value = [_history_event()]

    result = GetLmpFactUseCase(repository).execute(
        GetLMPRequest(sale_number="OV001"),
        include="history",
    )

    repository.get_lmp_history_events.assert_called_once()
    assert len(result["list_history"]) == 1
    assert result["list_history"][0]["stage_code"] == "000003"


# ---------------------------------------------------------------------------
# F-LMP-03 — GetLmpFactsHistoryUseCase
# ---------------------------------------------------------------------------


def test_facts_history_events_passthrough_raw_order() -> None:
    repository = MagicMock()
    repository.get_lmp_history_panel_context.return_value = {
        "branch": "01",
        "reference_revision": "002",
        "panel_start_date": "20260501",
    }
    repository.get_lmp_history_events.return_value = [
        _history_event(stage_code="000003"),
        _history_event(stage_code="000012"),
    ]

    result = GetLmpFactsHistoryUseCase(repository).execute(
        GetLmpHistoryRequest(sale_number="OV001"),
        view="events",
    )

    repository.get_lmp_history_flow.assert_not_called()
    assert result["view"] == "events"
    assert result["total"] == 2
    assert [i["stage_code"] for i in result["items"]] == ["000003", "000012"]
    assert result["reference_revision"] == "002"
    assert result["panel_start_date"] == "2026-05-01"


def test_facts_history_flow_view_uses_flow_repository() -> None:
    repository = MagicMock()
    repository.get_lmp_history_panel_context.return_value = {"branch": "01"}
    repository.get_lmp_history_flow.return_value = [_history_event()]

    result = GetLmpFactsHistoryUseCase(repository).execute(
        GetLmpHistoryRequest(sale_number="OV001"),
        view="flow",
    )

    repository.get_lmp_history_events.assert_not_called()
    repository.get_lmp_history_flow.assert_called_once()
    assert result["view"] == "flow"


# ---------------------------------------------------------------------------
# F-LMP-04 — GetLmpPiCountsUseCase
# ---------------------------------------------------------------------------


def test_pi_counts_maps_keys_unequivocally() -> None:
    repository = MagicMock()
    repository.get_lmp_pi_counts_by_ovs.return_value = {
        ("01", "OV002", "001"): 7,
        ("01", "OV001", "001"): 3,
    }

    result = GetLmpPiCountsUseCase(repository).execute(
        ov_keys=[
            {"branch": "01", "sale_number": "OV001", "revision": "001"},
            {"branch": "01", "sale_number": "OV002", "revision": "001"},
        ]
    )

    assert result["total"] == 2
    assert result["items"][0]["sale_number"] == "OV001"
    assert result["items"][0]["qtd_pi"] == 3
    assert result["items"][1]["qtd_pi"] == 7


def test_pi_counts_rejects_oversized_batch() -> None:
    repository = MagicMock()
    ov_keys = [
        {"branch": "01", "sale_number": f"OV{i}", "revision": "001"}
        for i in range(FACTS_PI_COUNT_BATCH_MAX + 1)
    ]

    with pytest.raises(ValueError, match="500"):
        GetLmpPiCountsUseCase(repository).execute(ov_keys=ov_keys)

    repository.get_lmp_pi_counts_by_ovs.assert_not_called()


def test_pi_counts_body_validation_rejects_empty_and_huge() -> None:
    with pytest.raises(Exception):
        LmpPiCountsBody(ovs=[])
    with pytest.raises(Exception):
        LmpPiCountsBody(
            ovs=[
                {"branch": "01", "sale_number": "OV", "revision": "1"}
            ]
            * (FACTS_PI_COUNT_BATCH_MAX + 1)
        )


# ---------------------------------------------------------------------------
# Paridade — mesmo dataset físico, campos compartilhados não divergem
# ---------------------------------------------------------------------------


def test_facts_mapper_parity_with_dashboard_summary_mapper() -> None:
    """Campos comuns facts x summary devem mapear identicamente o mesmo row."""
    staged_row = {
        "branch": "02",
        "sale_number": "OV777",
        "sale_description": "  Projeto Beta  ",
        "listing_kind": "AMOSTRA",
        "start_date": "20260601",
        "end_date": "20260615",
        "homolog_revision": "003",
        "measurement_revision": "002",
        "homolog_date": "20260601",
        "cycle_index": 2,
        "engineering_status": "EM_ANDAMENTO",
        "engineering_total_minutes": 240,
        "qtd_pi": 12,
    }

    summary = LMPQueryRepository._map_dashboard_summary_row(staged_row)
    fact = LMPQueryRepository._map_lmp_fact_row(
        {**staged_row, "residence_minutes": staged_row["engineering_total_minutes"]}
    )

    shared_keys = {
        "branch",
        "sale_number",
        "sale_description",
        "listing_kind",
        "start_date",
        "end_date",
        "homolog_revision",
        "measurement_revision",
        "homolog_date",
        "cycle_index",
        "engineering_status",
        "qtd_pi",
    }
    for key in shared_keys:
        assert fact[key] == summary[key], f"campo divergente: {key}"

    # Flags derivadas declaradas só existem no contrato facts.
    assert fact["has_lmp_finalized"] is False
    assert fact["residence_minutes"] == 240


def test_facts_select_uses_same_staged_tables_as_dashboard() -> None:
    """Garantia estrutural: facts reusa #Delpi_* — nada de query paralela."""
    repository = LMPQueryRepository()
    select = repository._staged_facts_select(include_qtd_pi=True, order_by=True)

    assert repository._TEMP_CANDIDATES in select
    assert repository._TEMP_ENG_RESUMO in select
    assert repository._TEMP_PI_COUNT in select
    assert "ORDER BY" in select


def test_facts_select_omits_pi_join_when_disabled() -> None:
    repository = LMPQueryRepository()
    select = repository._staged_facts_select(include_qtd_pi=False, order_by=False)

    assert repository._TEMP_PI_COUNT not in select
    assert "0 AS qtd_pi" in select


# ---------------------------------------------------------------------------
# Envelope/meta — handlers com autouse authenticated_superadmin
# ---------------------------------------------------------------------------


def test_route_list_facts_envelope_meta() -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [_fact_row()],
        "total": 1,
        "page": 1,
        "page_size": 50,
        "total_pages": 1,
        "provenance": {},
        "policy": {},
    }

    with patch(
        f"{ROUTER_MODULE}.build_engineering_list_lmp_facts_use_case",
        return_value=use_case,
    ):
        response = list_lmp_facts_route()

    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="list_lmp_facts",
        shape="paged_list",
        entity="lmp_fact",
    )


def test_route_fact_detail_envelope_meta() -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _lmp_entity().to_dict()

    with patch(
        f"{ROUTER_MODULE}.build_engineering_get_lmp_fact_use_case",
        return_value=use_case,
    ):
        response = get_lmp_fact_route("OV001")

    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="get_lmp_fact",
        shape="product_snapshot",
        entity="lmp_fact",
    )


def test_route_facts_history_events_envelope_meta() -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "total": 0}

    with patch(
        f"{ROUTER_MODULE}.build_engineering_get_lmp_facts_history_use_case",
        return_value=use_case,
    ):
        response = get_lmp_facts_history_events_route("OV001")

    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="get_lmp_facts_history_events",
        shape="list",
        entity="lmp_fact_history",
    )


def test_route_facts_history_flow_envelope_meta() -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "total": 0}

    with patch(
        f"{ROUTER_MODULE}.build_engineering_get_lmp_facts_history_use_case",
        return_value=use_case,
    ):
        response = get_lmp_facts_history_flow_route("OV001")

    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="get_lmp_facts_history_flow",
        shape="list",
        entity="lmp_fact_history_flow",
    )


def test_route_pi_counts_envelope_meta() -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "total": 0}

    with patch(
        f"{ROUTER_MODULE}.build_engineering_get_lmp_pi_counts_use_case",
        return_value=use_case,
    ):
        response = get_lmp_pi_counts_route(
            LmpPiCountsBody(
                ovs=[
                    {"branch": "01", "sale_number": "OV001", "revision": "001"}
                ]
            )
        )

    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="get_lmp_pi_counts",
        shape="list",
        entity="lmp_pi_count",
    )


def test_route_validation_error_returns_400_envelope() -> None:
    use_case = MagicMock()
    use_case.execute.side_effect = ValueError("OV não encontrada")

    with patch(
        f"{ROUTER_MODULE}.build_engineering_get_lmp_fact_use_case",
        return_value=use_case,
    ):
        response = get_lmp_fact_route("OV404")

    body = body_json(response)
    assert body["success"] is False


def test_route_source_failure_returns_500_envelope() -> None:
    use_case = MagicMock()
    use_case.execute.side_effect = RuntimeError("TOTVS indisponível")

    with patch(
        f"{ROUTER_MODULE}.build_engineering_list_lmp_facts_use_case",
        return_value=use_case,
    ):
        response = list_lmp_facts_route()

    body = body_json(response)
    assert body["success"] is False


# ---------------------------------------------------------------------------
# AuthN/AuthZ negativos — fail closed em todos os caminhos
# ---------------------------------------------------------------------------


def test_facts_denied_when_unauthenticated() -> None:
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=None,
    ):
        with pytest.raises(Exception, match="Unauthorized"):
            list_lmp_facts_route()


def test_facts_denied_for_user_without_permission() -> None:
    user = MagicMock(is_superadmin=False, rbac_unavailable=False)

    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ), patch(
        "delpi_auth.authorization.has_any_permission",
        return_value=False,
    ):
        with pytest.raises(Exception, match="Forbidden"):
            get_lmp_fact_route("OV001")


def test_facts_denied_for_legacy_service_principal() -> None:
    """X-Delpi-Service-Token compartilhado nunca autoriza facts."""
    user = MagicMock(principal_type="service", is_superadmin=False)

    with patch(
        "app.interface.http.s2s_service_access.resolve_user_context",
        return_value=user,
    ):
        with pytest.raises(HTTPException) as excinfo:
            get_lmp_facts_history_events_route("OV001")

    assert excinfo.value.status_code == 403


def test_facts_s2s_fails_closed_when_not_provisioned() -> None:
    """S2S não provisionado -> 503, nunca fallback para o caminho humano."""
    request = MagicMock()
    request.headers = {"x-delpi-service-authorization": "Bearer tok"}

    with patch(
        "app.interface.http.s2s_service_access.get_request",
        return_value=request,
    ), patch(
        "app.interface.http.s2s_service_access.extract_service_authorization",
        return_value="tok",
    ), patch(
        "app.interface.http.s2s_service_access.ServiceTokenValidator.from_env",
        side_effect=ServiceAuthConfigError(),
    ):
        with pytest.raises(HTTPException) as excinfo:
            list_lmp_facts_route()

    assert excinfo.value.status_code == 503


def test_facts_s2s_denied_on_missing_scope() -> None:
    request = MagicMock()
    request.headers = {"x-delpi-service-authorization": "Bearer tok"}
    validator = MagicMock()
    validator.validate.side_effect = ServiceScopeDeniedError()

    with patch(
        "app.interface.http.s2s_service_access.get_request",
        return_value=request,
    ), patch(
        "app.interface.http.s2s_service_access.extract_service_authorization",
        return_value="tok",
    ), patch(
        "app.interface.http.s2s_service_access.ServiceTokenValidator.from_env",
        return_value=validator,
    ):
        with pytest.raises(HTTPException) as excinfo:
            get_lmp_pi_counts_route(
                LmpPiCountsBody(
                    ovs=[
                        {"branch": "01", "sale_number": "OV1", "revision": "1"}
                    ]
                )
            )

    assert excinfo.value.status_code == 403


# ---------------------------------------------------------------------------
# G4.A.R1 — boundary corrigido: api-delpi NÃO conhece permissões
# funcionais `engineering.*`; facts humano = conjunto legado; facts via
# engineering-api = credencial S2S individual (negações abaixo).
# ---------------------------------------------------------------------------


def test_facts_human_engineering_access_alone_denied() -> None:
    """G4.A.R1 — `engineering.access` NÃO autoriza o contrato facts.

    Boundary: a Engineering API aplica `engineering.access` via Core; a
    api-delpi valida apenas a credencial técnica do consumidor (S2S) ou a
    permissão LMP legada de consumidores diretos preservados.
    """
    user = MagicMock(
        principal_type="user",
        is_superadmin=False,
        permissions=["engineering.access"],
        rbac_unavailable=False,
    )

    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with pytest.raises(Exception, match="Forbidden"):
            list_lmp_facts_route()


def test_facts_human_engineering_manage_only_denied() -> None:
    """G4.A.R1 — `engineering.manage` também não autoriza o contrato facts."""
    user = MagicMock(
        principal_type="user",
        is_superadmin=False,
        permissions=["engineering.manage"],
        rbac_unavailable=False,
    )

    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with pytest.raises(Exception, match="Forbidden"):
            list_lmp_facts_route()


def test_facts_s2s_denied_wrong_client() -> None:
    from delpi_auth.service_errors import ServiceClientDeniedError

    request = MagicMock()
    request.headers = {"x-delpi-service-authorization": "Bearer tok"}
    validator = MagicMock()
    validator.validate.side_effect = ServiceClientDeniedError()

    with patch(
        "app.interface.http.s2s_service_access.get_request",
        return_value=request,
    ), patch(
        "app.interface.http.s2s_service_access.extract_service_authorization",
        return_value="tok",
    ), patch(
        "app.interface.http.s2s_service_access.ServiceTokenValidator.from_env",
        return_value=validator,
    ):
        with pytest.raises(HTTPException) as excinfo:
            list_lmp_facts_route()

    assert excinfo.value.status_code == 403
    assert getattr(excinfo.value, "error_code", None) == "S2S_CLIENT_DENIED"


def test_facts_s2s_denied_invalid_token_or_audience() -> None:
    """Token inválido/audience incorreta → 401 com code estável."""
    from delpi_auth.service_errors import ServiceTokenInvalidError

    request = MagicMock()
    request.headers = {"x-delpi-service-authorization": "Bearer bad"}
    validator = MagicMock()
    validator.validate.side_effect = ServiceTokenInvalidError()

    with patch(
        "app.interface.http.s2s_service_access.get_request",
        return_value=request,
    ), patch(
        "app.interface.http.s2s_service_access.extract_service_authorization",
        return_value="bad",
    ), patch(
        "app.interface.http.s2s_service_access.ServiceTokenValidator.from_env",
        return_value=validator,
    ):
        with pytest.raises(HTTPException) as excinfo:
            list_lmp_facts_route()

    assert excinfo.value.status_code == 401
    assert getattr(excinfo.value, "error_code", None) == "S2S_TOKEN_INVALID"


def test_facts_s2s_validator_unavailable() -> None:
    """JWKS/Keycloak indisponível → 503 fail-closed."""
    from delpi_auth.service_errors import ServiceValidatorUnavailableError

    request = MagicMock()
    request.headers = {"x-delpi-service-authorization": "Bearer tok"}
    validator = MagicMock()
    validator.validate.side_effect = ServiceValidatorUnavailableError()

    with patch(
        "app.interface.http.s2s_service_access.get_request",
        return_value=request,
    ), patch(
        "app.interface.http.s2s_service_access.extract_service_authorization",
        return_value="tok",
    ), patch(
        "app.interface.http.s2s_service_access.ServiceTokenValidator.from_env",
        return_value=validator,
    ):
        with pytest.raises(HTTPException) as excinfo:
            list_lmp_facts_route()

    assert excinfo.value.status_code == 503


def test_facts_access_constant_has_no_engineering_functional_perms() -> None:
    """Guarda de boundary: a allowlist humana facts não contém `engineering.*`."""
    import app.application.security.api_delpi_permissions as perms

    legacy = perms.ENGINEERING_LMP_ACCESS
    assert not any(
        str(code).startswith("engineering.") for code in legacy
    ), "permissões funcionais engineering.* não pertencem à api-delpi"
