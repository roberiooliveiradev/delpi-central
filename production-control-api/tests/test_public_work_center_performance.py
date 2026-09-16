"""Desempenho do posto no cockpit público — recorte, degradação e privacidade."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import pytest

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_work_center_performance_cache import (
    clear_work_center_performance_cache,
)
from production_control_app.application.services.public_work_center_performance_service import (
    PublicWorkCenterPerformanceService,
    clamp_days,
)
from production_control_app.domain.errors import (
    DelpiGatewayError,
    InvalidBranch,
    PublicAccessDenied,
    SnapshotNotFound,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

TODAY = date(2026, 9, 14)

_OPERATIONS = [
    {
        "work_center": "CT-12",
        "resource": "MAQ-12A",
        "production_order": "24696001001",
        "operation_code": "06",
        "pa_product_code": "90264260",
    },
    {
        "work_center": "CT-12",
        "resource": "MAQ-12B",
        "production_order": "24696001002",
        "operation_code": "06",
        "pa_product_code": "90264261",
    },
    # Irmão: outro posto, com recurso próprio.
    {
        "work_center": "CT-70",
        "resource": "MAQ-70",
        "production_order": "24696002001",
        "operation_code": "02",
        "pa_product_code": "90264262",
    },
    # Sem recurso cadastrado — o fallback é o próprio código do CT.
    {
        "work_center": "CT-99",
        "resource": "",
        "production_order": "24696003001",
        "operation_code": "01",
        "pa_product_code": "90264263",
    },
]


class FakeSnapshotRepo:
    def __init__(self, branches: tuple[str, ...] = ("01", "02")) -> None:
        self.rows = {
            branch: {
                "id": f"snap-{branch}",
                "branch": branch,
                "start_date": date(2026, 9, 1),
                "end_date": date(2026, 9, 30),
                "payload_json": {
                    "work_centers": [
                        {"work_center": "CT-12"},
                        {"work_center": "CT-70"},
                        {"work_center": "CT-99"},
                    ],
                    "operations": _OPERATIONS,
                },
                "schema_version": 1,
                "refreshed_at": datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc),
                "refreshed_by": "pcp",
            }
            for branch in branches
        }

    def get(self, *, branch: str) -> dict[str, Any] | None:
        return self.rows.get(branch)


class FakeDelpiGateway:
    """Espelha o envelope da api-delpi: ora ``data`` lista, ora ``data.items``."""

    def __init__(self, *, fail_efficiency: bool = False, fail_downtime: bool = False) -> None:
        self.fail_efficiency = fail_efficiency
        self.fail_downtime = fail_downtime
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def fetch_factory_shifts(self) -> dict[str, Any]:
        self.calls.append(("factory_shifts", {}))
        return {
            "success": True,
            "data": {
                "current_shift_id": "2",
                "current_shift": {
                    "id": "2",
                    "label": "2º Turno",
                    "start_time": "14:18",
                    "end_time": "23:49",
                },
                "shifts": [],
            },
        }

    def fetch_efficiency_by_work_center(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("efficiency_by_work_center", kwargs))
        if self.fail_efficiency:
            raise DelpiGatewayError("api-delpi fora do ar.")
        pct = 92.5 if kwargs.get("shift") else 88.0
        count = 4 if kwargs.get("shift") else 9
        return {
            "success": True,
            "data": [
                {
                    "work_center": kwargs.get("work_center") or "CT-12",
                    "efficiency_pct": pct,
                    "appointment_count": count,
                }
            ],
        }

    def fetch_efficiency_series(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("efficiency_series", kwargs))
        if self.fail_efficiency:
            raise DelpiGatewayError("api-delpi fora do ar.")
        return {
            "success": True,
            "data": [
                {
                    "date": "2026-09-13",
                    "work_center": "CT-12",
                    "efficiency_pct": 80.0,
                    "appointment_count": 5,
                },
                {
                    "date": "2026-09-14",
                    "work_center": "CT-12",
                    "efficiency_pct": 90.0,
                    "appointment_count": 9,
                },
            ],
        }

    def fetch_eficiencia_fabril_appointments(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("appointments", kwargs))
        if self.fail_efficiency:
            raise DelpiGatewayError("api-delpi fora do ar.")
        shift_row = {
            "op": "24696001001",
            "operacao": "06",
            "descricao_operacao": "INSPECAO",
            "produto": "50320064",
            "produto_acabado": "90264260",
            "cod_operador": "000123",
            "login_operador": "jsilva",
            "nome_operador": "JOAO DA SILVA",
            "qtd_apontada": 120.0,
            "tempo_real_horas": 1.25,
            "tempo_previsto_horas": 1.0,
            "eficiencia_percentual": 80.0,
            "valor_mod_hora": 32.5,
            "resultado_mod": -8.12,
            "hora_inicio": "15:00",
            "hora_final": "16:15",
        }
        if kwargs.get("shift"):
            return {"success": True, "data": [shift_row]}
        # Dia inteiro: turno atual + apontamento de outro turno.
        other_shift_row = {
            **shift_row,
            "op": "24696001002",
            "qtd_apontada": 230.0,
            "hora_inicio": "08:00",
            "hora_final": "09:30",
        }
        return {"success": True, "data": [shift_row, other_shift_row]}

    def fetch_unproductive_hours_summary(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("downtime_summary", kwargs))
        if self.fail_downtime:
            raise DelpiGatewayError("api-delpi fora do ar.")
        # Sem turno: dia inteiro. Com turno: só a fatia do turno corrente.
        hours = 0.6 if kwargs.get("shift") else 1.75
        count = 1 if kwargs.get("shift") else 3
        return {
            "success": True,
            "data": {
                "summary": {
                    "total_appointments": count,
                    "total_hours": hours,
                    "total_cost": 140.0,
                }
            },
        }

    def fetch_unproductive_hours_ranking(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("downtime_ranking", kwargs))
        if self.fail_downtime:
            raise DelpiGatewayError("api-delpi fora do ar.")
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "rank": 1,
                        "motivo": "MT",
                        "motivoDescricao": "MANUTENCAO",
                        "totalHoras": 4.5,
                        "totalApontamentos": 2,
                        "totalCusto": 360.0,
                    }
                ]
            },
        }

    def fetch_unproductive_hours_series(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("downtime_series", kwargs))
        if self.fail_downtime:
            raise DelpiGatewayError("api-delpi fora do ar.")
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "date": "2026-09-13",
                        "total_hours": 2.0,
                        "total_appointments": 2,
                        "total_cost": 160.0,
                    },
                    {
                        "date": "2026-09-14",
                        "total_hours": 1.75,
                        "total_appointments": 3,
                        "total_cost": 140.0,
                    },
                ]
            },
        }


class EmptyDelpiGateway(FakeDelpiGateway):
    """Posto real, turno sem nenhum apontamento no TOTVS."""

    def fetch_efficiency_by_work_center(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("efficiency_by_work_center", kwargs))
        return {"success": True, "data": []}

    def fetch_efficiency_series(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("efficiency_series", kwargs))
        return {"success": True, "data": []}

    def fetch_eficiencia_fabril_appointments(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("appointments", kwargs))
        return {"success": True, "data": []}

    def fetch_unproductive_hours_summary(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("downtime_summary", kwargs))
        return {"success": True, "data": {"summary": {}}}

    def fetch_unproductive_hours_ranking(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("downtime_ranking", kwargs))
        return {"success": True, "data": {"items": []}}

    def fetch_unproductive_hours_series(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("downtime_series", kwargs))
        return {"success": True, "data": {"items": []}}


def _service(gateway: FakeDelpiGateway) -> PublicWorkCenterPerformanceService:
    branch_access = BranchAccessService()
    return PublicWorkCenterPerformanceService(
        gateway,
        access=PublicCockpitAccessService(),
        machine_load=MachineLoadService(
            gateway,
            snapshots=FakeSnapshotRepo(),
            branch_access=branch_access,
        ),
        branch_access=branch_access,
        clock=lambda: datetime(2026, 9, 14, 18, 0, tzinfo=timezone.utc),
    )


def _token() -> str:
    return PublicCockpitAccessService().token()


@pytest.fixture(autouse=True)
def _isolate_cache():
    clear_work_center_performance_cache()
    yield
    clear_work_center_performance_cache()


def test_clamp_days_keeps_the_totvs_window_bounded() -> None:
    assert clamp_days(None) == 14
    assert clamp_days("") == 14
    assert clamp_days("abc") == 14
    assert clamp_days(1) == 7
    assert clamp_days(365) == 30
    assert clamp_days(21) == 21


def test_positive_case_composes_shift_efficiency_and_downtime() -> None:
    gateway = FakeDelpiGateway()
    payload = _service(gateway).build(
        token=_token(), branch="01", work_center="CT-12", days=14
    )

    assert payload["branch"] == "01"
    assert payload["work_center"] == "CT-12"
    assert payload["days"] == 14
    assert payload["period"] == {"start_date": "2026-09-01", "end_date": "2026-09-14"}
    assert payload["shift"]["id"] == "2"

    efficiency = payload["efficiency"]
    assert efficiency["available"] is True
    assert efficiency["shift_pct"] == 92.5
    assert efficiency["shift_appointment_count"] == 4
    assert efficiency["shift_produced_qty"] == 120.0
    assert efficiency["day_pct"] == 88.0
    assert "day_produced_qty" not in efficiency
    assert efficiency["period_avg_pct"] == 85.0
    assert [point["date"] for point in efficiency["series"]] == [
        "2026-09-13",
        "2026-09-14",
    ]
    appointment_calls = [kwargs for name, kwargs in gateway.calls if name == "appointments"]
    assert appointment_calls
    assert all(call.get("shift") == "2" for call in appointment_calls)
    series_calls = [kwargs for name, kwargs in gateway.calls if name == "efficiency_series"]
    assert series_calls
    assert all(call.get("shift") == "2" for call in series_calls)

    downtime = payload["downtime"]
    assert downtime["available"] is True
    assert downtime["today_hours"] == 0.6
    assert downtime["today_appointment_count"] == 1
    assert downtime["period_hours"] == 3.75
    assert downtime["period_appointment_count"] == 5
    assert downtime["by_reason"][0]["stop_reason"] == "MT"
    assert downtime["by_reason"][0]["hours"] == 4.5
    summary_calls = [kwargs for name, kwargs in gateway.calls if name == "downtime_summary"]
    assert summary_calls
    assert all(call.get("shift") == "2" for call in summary_calls)


def test_downtime_is_filtered_by_the_work_center_resources_not_the_ct_code() -> None:
    """RECURSO do BI é ``H8_RECURSO``, não ``H8_CTRAB`` — o snapshot faz a ponte."""
    gateway = FakeDelpiGateway()
    payload = _service(gateway).build(token=_token(), branch="01", work_center="CT-12")

    assert payload["resources"] == ["MAQ-12A", "MAQ-12B"]
    downtime_calls = [
        kwargs for name, kwargs in gateway.calls if name.startswith("downtime_")
    ]
    assert downtime_calls
    for kwargs in downtime_calls:
        assert kwargs["resource"] == "MAQ-12A,MAQ-12B"


def test_work_center_without_resource_falls_back_to_its_own_code() -> None:
    gateway = FakeDelpiGateway()
    payload = _service(gateway).build(token=_token(), branch="01", work_center="CT-99")

    assert payload["resources"] == ["CT-99"]


def test_sibling_work_center_and_branch_are_scoped_independently() -> None:
    gateway = FakeDelpiGateway()
    payload = _service(gateway).build(token=_token(), branch="02", work_center="CT-70")

    assert payload["branch"] == "02"
    assert payload["resources"] == ["MAQ-70"]
    efficiency_calls = [
        kwargs for name, kwargs in gateway.calls if name == "efficiency_by_work_center"
    ]
    assert all(kwargs["branch"] == "02" for kwargs in efficiency_calls)
    assert all(kwargs["work_center"] == "CT-70" for kwargs in efficiency_calls)


def test_response_hides_operator_credentials_and_currency_values() -> None:
    payload = _service(FakeDelpiGateway()).build(
        token=_token(), branch="01", work_center="CT-12"
    )

    appointment = payload["efficiency"]["appointments"][0]
    assert appointment["production_order"] == "24696001001"
    assert appointment["efficiency_pct"] == 80.0
    assert appointment["pa_product_code"] == "90264260"
    assert appointment["operator_name"] == "JOAO DA SILVA"
    assert set(appointment) == {
        "production_order",
        "operation",
        "operation_description",
        "pa_product_code",
        "product_code",
        "operator_name",
        "quantity",
        "real_hours",
        "planned_hours",
        "efficiency_pct",
        "start_time",
        "end_time",
    }

    serialized = repr(payload)
    for leaked in ("jsilva", "000123", "valor_mod", "total_cost", "totalCusto"):
        assert leaked not in serialized
    assert "JOAO DA SILVA" in serialized


def test_downtime_failure_still_answers_efficiency() -> None:
    payload = _service(FakeDelpiGateway(fail_downtime=True)).build(
        token=_token(), branch="01", work_center="CT-12"
    )

    assert payload["efficiency"]["available"] is True
    assert payload["efficiency"]["shift_pct"] == 92.5
    assert payload["downtime"]["available"] is False
    assert payload["downtime"]["message"]


def test_efficiency_failure_still_answers_downtime() -> None:
    payload = _service(FakeDelpiGateway(fail_efficiency=True)).build(
        token=_token(), branch="01", work_center="CT-12"
    )

    assert payload["efficiency"]["available"] is False
    assert payload["downtime"]["available"] is True
    assert payload["downtime"]["today_hours"] == 0.6


def test_shift_without_appointments_reports_empty_not_a_false_zero() -> None:
    """Sem apontamento o posto não é 0% de eficiência — é ausência de medição."""
    payload = _service(EmptyDelpiGateway()).build(
        token=_token(), branch="01", work_center="CT-12"
    )

    efficiency = payload["efficiency"]
    assert efficiency["available"] is True
    assert efficiency["shift_pct"] is None
    assert efficiency["day_pct"] is None
    assert efficiency["period_avg_pct"] is None
    assert efficiency["series"] == []
    assert efficiency["appointments"] == []

    # Parada é contagem de horas: zero parada realmente vale 0 h.
    downtime = payload["downtime"]
    assert downtime["available"] is True
    assert downtime["today_hours"] == 0.0
    assert downtime["period_hours"] == 0.0
    assert downtime["by_reason"] == []


def test_invalid_token_is_denied() -> None:
    with pytest.raises(PublicAccessDenied):
        _service(FakeDelpiGateway()).build(
            token="nao-e-o-token", branch="01", work_center="CT-12"
        )


def test_invalid_branch_is_rejected() -> None:
    with pytest.raises(InvalidBranch):
        _service(FakeDelpiGateway()).build(
            token=_token(), branch="99", work_center="CT-12"
        )


def test_work_center_outside_the_published_queue_is_rejected() -> None:
    with pytest.raises(ValueError, match="CT-404"):
        _service(FakeDelpiGateway()).build(
            token=_token(), branch="01", work_center="CT-404"
        )


def test_empty_work_center_is_rejected() -> None:
    with pytest.raises(ValueError):
        _service(FakeDelpiGateway()).build(token=_token(), branch="01", work_center="  ")


def test_branch_without_published_queue_is_not_found() -> None:
    branch_access = BranchAccessService()
    gateway = FakeDelpiGateway()
    service = PublicWorkCenterPerformanceService(
        gateway,
        access=PublicCockpitAccessService(),
        machine_load=MachineLoadService(
            gateway,
            snapshots=FakeSnapshotRepo(branches=("02",)),
            branch_access=branch_access,
        ),
        branch_access=branch_access,
    )
    with pytest.raises(SnapshotNotFound):
        service.build(token=_token(), branch="01", work_center="CT-12")


def test_second_read_within_the_ttl_does_not_hit_the_api_delpi_again() -> None:
    gateway = FakeDelpiGateway()
    service = _service(gateway)

    first = service.build(token=_token(), branch="01", work_center="CT-12", days=14)
    calls_after_first = len(gateway.calls)
    second = service.build(token=_token(), branch="01", work_center="CT-12", days=14)

    assert second == first
    assert len(gateway.calls) == calls_after_first
