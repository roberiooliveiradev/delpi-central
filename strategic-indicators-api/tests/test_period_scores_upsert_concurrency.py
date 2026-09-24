from __future__ import annotations

from psycopg.errors import UniqueViolation

from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_period_scores_repository import (
    is_period_scores_unique_violation,
)


def test_is_period_scores_unique_violation_detects_psycopg_error() -> None:
    root = UniqueViolation(
        'duplicate key value violates unique constraint "uq_si_period_scores_scope_version"'
    )
    wrapped = PluginsRepositoryError(f"Falha ao executar comando: {root}")
    wrapped.__cause__ = root
    assert is_period_scores_unique_violation(wrapped) is True


def test_is_period_scores_unique_violation_detects_message_without_type() -> None:
    exc = PluginsRepositoryError(
        'Falha ao executar comando: duplicate key value violates unique constraint '
        '"uq_si_period_scores_scope_version"'
    )
    assert is_period_scores_unique_violation(exc) is True


def test_is_period_scores_unique_violation_negative_other_errors() -> None:
    assert is_period_scores_unique_violation(RuntimeError("timeout")) is False
    assert (
        is_period_scores_unique_violation(
            PluginsRepositoryError("Falha ao executar comando: connection reset")
        )
        is False
    )


def test_upsert_retries_on_unique_violation_then_succeeds() -> None:
    from unittest.mock import MagicMock, patch

    from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_period_scores_repository import (
        PostgresStrategicIndicatorsPeriodScoresRepository,
    )

    repo = PostgresStrategicIndicatorsPeriodScoresRepository()
    conflict = PluginsRepositoryError(
        'Falha ao executar comando: duplicate key value violates unique constraint '
        '"uq_si_period_scores_scope_version"'
    )
    conflict.__cause__ = UniqueViolation("uq_si_period_scores_scope_version")

    calls = {"n": 0}

    def _locked(**_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise conflict

    snapshot = MagicMock()
    snapshot.period.competence = "2026-09"
    snapshot.period.start_date = "01-09-2026"
    snapshot.period.end_date = "30-09-2026"

    with (
        patch.object(repo, "_upsert_period_snapshot_locked", side_effect=_locked),
        patch(
            "si_app.infrastructure.persistence.plugins.repositories.strategic_indicators."
            "postgres_period_scores_repository.serialize_period_snapshot",
            return_value={
                "igd": 1.0,
                "igd_exact": 1.0,
                "classification": "ok",
                "calculated_departments": [],
                "calculated_indicators": [],
                "measurement_errors": [],
            },
        ),
    ):
        repo.upsert_period_snapshot(
            snapshot=snapshot,
            scope_branch="01",
            scope_department_id="",
            is_clean=True,
        )

    assert calls["n"] == 2
