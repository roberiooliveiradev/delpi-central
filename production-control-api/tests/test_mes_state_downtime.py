"""Fundação MES — domínio puro + integração Postgres quando disponível.

Os testes de integração só rodam com ``PC_TEST_MES_DB=1`` e PLUGINS_DB_*
apontando para um banco de teste descartável; sem isso são pulados.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.domain.errors import InvalidMesEvent
from production_control_app.domain.services.mes_operational_state import (
    DOWNTIME_CONFIRMER_TYPES,
    DOWNTIME_SOURCES,
    STATE_EVENT_SOURCES,
    WorkCenterOperationalState,
    normalize_reason_code,
    normalize_state,
    validate_downtime_event,
    validate_state_event,
    validate_source,
    validate_time_range,
)

UTC = timezone.utc


def _aware(minutes: int = 0) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)


class TestOperationalStates:
    def test_all_states_normalize(self):
        assert [s.value for s in WorkCenterOperationalState] == [
            "idle",
            "setup",
            "producing",
            "stopped",
            "planned_stop",
        ]

    def test_normalize_accepts_case_and_padding(self):
        assert normalize_state("  PRODUCING ") is WorkCenterOperationalState.PRODUCING
        assert normalize_state("planned_stop") is WorkCenterOperationalState.PLANNED_STOP

    def test_invalid_state_rejected(self):
        with pytest.raises(InvalidMesEvent):
            normalize_state("flying")
        with pytest.raises(InvalidMesEvent):
            normalize_state("")


class TestSources:
    def test_known_sources(self):
        assert "operator_pause" in DOWNTIME_SOURCES
        assert "automatic_detection" in DOWNTIME_SOURCES
        assert "operator" in STATE_EVENT_SOURCES
        assert "recovery" in STATE_EVENT_SOURCES
        assert "operator" in DOWNTIME_CONFIRMER_TYPES

    def test_unknown_source_rejected(self):
        with pytest.raises(InvalidMesEvent):
            validate_source("mqtt", STATE_EVENT_SOURCES, field="source")


class TestTimeRange:
    def test_open_event_valid(self):
        validate_time_range(_aware(), None)

    def test_closed_event_valid(self):
        validate_time_range(_aware(), _aware(5))

    def test_ended_before_started_rejected(self):
        with pytest.raises(InvalidMesEvent):
            validate_time_range(_aware(), _aware(-5))

    def test_naive_timestamps_rejected(self):
        with pytest.raises(InvalidMesEvent):
            validate_time_range(datetime.now(), None)


class TestStateEventValidation:
    def test_valid_event(self):
        validate_state_event(
            {
                "state": "producing",
                "source": "operator",
                "started_at": _aware(),
                "ended_at": None,
            }
        )

    def test_telemetry_does_not_define_operational_state(self):
        """Device offline não transforma estado: o campo é ignorado pelo domínio."""
        validate_state_event(
            {
                "state": "producing",
                "source": "system",
                "started_at": _aware(),
                "device_online": False,
                "device_status": "offline",
            }
        )

    def test_invalid_state_rejected(self):
        with pytest.raises(InvalidMesEvent):
            validate_state_event(
                {
                    "state": "broken",
                    "source": "system",
                    "started_at": _aware(),
                }
            )


class TestDowntimeValidation:
    def test_open_downtime_without_reason_is_valid(self):
        """Pause antes da classificação: parada aberta sem motivo é legítima."""
        validate_downtime_event(
            {
                "source": "operator_pause",
                "started_at": _aware(),
                "ended_at": None,
                "reason_code": None,
                "confirmed": False,
                "confirmed_at": None,
            }
        )

    def test_confirmed_requires_reason(self):
        with pytest.raises(InvalidMesEvent):
            validate_downtime_event(
                {
                    "source": "operator_pause",
                    "started_at": _aware(),
                    "reason_code": None,
                    "confirmed": True,
                    "confirmed_at": _aware(),
                }
            )

    def test_confirmed_requires_confirmed_at(self):
        with pytest.raises(InvalidMesEvent):
            validate_downtime_event(
                {
                    "source": "operator_pause",
                    "started_at": _aware(),
                    "reason_code": "raw_material",
                    "confirmed": True,
                    "confirmed_at": None,
                }
            )

    def test_unconfirmed_with_confirmed_at_rejected(self):
        with pytest.raises(InvalidMesEvent):
            validate_downtime_event(
                {
                    "source": "system",
                    "started_at": _aware(),
                    "reason_code": None,
                    "confirmed": False,
                    "confirmed_at": _aware(),
                }
            )


class TestReasonCode:
    def test_normalizes_case_and_padding(self):
        assert normalize_reason_code("  RAW_MATERIAL ") == "raw_material"

    def test_empty_rejected(self):
        with pytest.raises(InvalidMesEvent):
            normalize_reason_code("")


# ---------------------------------------------------------------------------
# Integração Postgres (banco descartável): PC_TEST_MES_DB=1 + PLUGINS_DB_*
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestMesRepositoriesPostgres:
    @pytest.fixture()
    def repos(self):
        from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
            PostgresDowntimeEventRepository,
            PostgresDowntimeReasonRepository,
            PostgresWorkCenterStateRepository,
        )

        return (
            PostgresWorkCenterStateRepository(),
            PostgresDowntimeEventRepository(),
            PostgresDowntimeReasonRepository(),
        )

    @pytest.fixture()
    def clean_ct(self):
        """Fecha qualquer evento aberto do CT de teste antes e depois."""
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        wc = "ZZ-TEST-MES"

        def _clean() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {PC_SCHEMA_NAME}.work_center_state_events "
                        "SET ended_at = NOW() "
                        "WHERE work_center = %s AND ended_at IS NULL",
                        (wc,),
                    )
                    cur.execute(
                        f"UPDATE {PC_SCHEMA_NAME}.downtime_events "
                        "SET ended_at = NOW() "
                        "WHERE work_center = %s AND ended_at IS NULL",
                        (wc,),
                    )
                conn.commit()

        _clean()
        yield wc
        _clean()

    def test_open_state_then_second_open_conflicts(self, repos, clean_ct):
        from production_control_app.domain.errors import MesStateConflict

        states, _, _ = repos
        opened = states.open_event(
            branch="01", work_center=clean_ct, state="idle", source="system"
        )
        assert opened["state"] == "idle"
        assert states.get_open(branch="01", work_center=clean_ct)["id"] == opened["id"]
        with pytest.raises(MesStateConflict):
            states.open_event(
                branch="01", work_center=clean_ct, state="producing", source="system"
            )

    def test_other_work_center_can_hold_own_open_state(self, repos, clean_ct):
        states, _, _ = repos
        states.open_event(
            branch="01", work_center=clean_ct, state="idle", source="system"
        )
        other = states.open_event(
            branch="02", work_center=clean_ct, state="producing", source="operator"
        )
        assert other["state"] == "producing"
        states.close_open(branch="02", work_center=clean_ct)

    def test_close_then_reopen(self, repos, clean_ct):
        states, _, _ = repos
        states.open_event(
            branch="01", work_center=clean_ct, state="idle", source="system"
        )
        closed = states.close_open(branch="01", work_center=clean_ct)
        assert closed["ended_at"] is not None
        reopened = states.open_event(
            branch="01", work_center=clean_ct, state="producing", source="operator"
        )
        assert reopened["ended_at"] is None
        timeline = states.list_for_work_center(branch="01", work_center=clean_ct)
        assert len(timeline) >= 2
        assert timeline[0]["id"] == reopened["id"]

    def test_downtime_open_classify_close(self, repos, clean_ct):
        downtimes = repos[1]
        opened = downtimes.create(
            branch="01", work_center=clean_ct, source="operator_pause"
        )
        assert opened["reason_code"] is None
        assert opened["confirmed"] is False

        classified = downtimes.classify(
            opened["id"],
            reason_code="raw_material",
            planned=None,
            counts_as_availability_loss=None,
            confirmed_by_type="operator",
            confirmed_by_ref="OP-1234",
        )
        assert classified["reason_code"] == "raw_material"
        assert classified["confirmed"] is True
        assert classified["confirmed_at"] is not None

        closed = downtimes.close_open(branch="01", work_center=clean_ct)
        assert closed["ended_at"] is not None

    def test_second_open_downtime_conflicts(self, repos, clean_ct):
        from production_control_app.domain.errors import DowntimeConflict

        downtimes = repos[1]
        downtimes.create(
            branch="01", work_center=clean_ct, source="operator_pause"
        )
        with pytest.raises(DowntimeConflict):
            downtimes.create(
                branch="01", work_center=clean_ct, source="system"
            )

    def test_classify_unknown_reason_rejected(self, repos, clean_ct):
        downtimes = repos[1]
        opened = downtimes.create(
            branch="01", work_center=clean_ct, source="operator_pause"
        )
        with pytest.raises(InvalidMesEvent):
            downtimes.classify(
                opened["id"],
                reason_code="motivo_inexistente",
                planned=None,
                counts_as_availability_loss=None,
            )

    def test_catalog_seed_and_soft_deactivation(self, repos, clean_ct):
        reasons = repos[2]
        active = reasons.list_active()
        codes = {row["code"] for row in active}
        assert "raw_material" in codes
        assert "other" in codes

        other = reasons.get("other")
        assert other["requires_note"] is True
        # Classificação OEE ainda não governada: defaults permanecem NULL.
        assert reasons.get("raw_material")["default_planned"] is None

        downtimes = repos[1]
        opened = downtimes.create(
            branch="01", work_center=clean_ct, source="system"
        )
        downtimes.classify(
            opened["id"],
            reason_code="raw_material",
            planned=None,
            counts_as_availability_loss=None,
        )
        deactivated = reasons.set_active("raw_material", active=False)
        assert deactivated["active"] is False
        assert "raw_material" not in {r["code"] for r in reasons.list_active()}
        # Histórico continua apontando para o código — FK preservada.
        assert downtimes.get(opened["id"])["reason_code"] == "raw_material"
        reasons.set_active("raw_material", active=True)
