from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.domain.services.kaizen.kaizen_savings_calculator import (
    amount_for_active_calendar_days,
)
from app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_repository import (
    PostgresKaizenRepository,
)


def _implanted_row(**overrides) -> dict:
    base = {
        "id": UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        "submodule_id": "sub",
        "branch_code": "01",
        "title": "Kaizen legado",
        "accountable": "Maria",
        "sector": "Producao",
        "investment": Decimal("100"),
        "savings_type": "tempo",
        "seconds_per_occurrence": Decimal("60"),
        "occurrences_per_day": Decimal("10"),
        "hourly_cost": Decimal("50"),
        "quantity_saved_per_day": None,
        "unit_material_cost": None,
        "fixed_daily_savings": None,
        "daily_savings": Decimal("8.33"),
        "annual_savings": Decimal("2107.49"),  # 8.33 × 253 dias úteis
        "realized_daily_savings": None,
        "realized_annual_savings": None,
        "status": "implantado",
        "date_committee_approved": None,
        "date_implemented": date(2026, 6, 15),
        "date_discontinued": None,
        "notes": None,
        "process_description": None,
        "problem_description": None,
        "improvement_description": None,
        "expected_result": None,
        "category": None,
        "current_revision_number": 1,
        "created_by_user_id": "u1",
        "updated_by_user_id": "u1",
        "created_at": date(2026, 6, 15),
        "updated_at": date(2026, 6, 15),
    }
    base.update(overrides)
    return base


def test_summary_counts_aprovado_in_quantity_not_savings() -> None:
    repo = PostgresKaizenRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        return_value=[
            _implanted_row(
                status="aprovado",
                date_committee_approved=date(2026, 7, 2),
                date_implemented=None,
                daily_savings=Decimal("50"),
                annual_savings=Decimal("18000"),
            )
        ]
    )

    result = repo.summary(
        branch_code="01",
        date_start="2026-07-01",
        date_end="2026-07-31",
    )

    assert result["period_implanted_count"] == 1
    assert result["aprovados"] == 1
    assert result["implantados"] == 0
    assert result["period_savings"] == 0.0
    assert result["period_hours_saved"] == 0.0
    assert result["active_count"] == 0
    assert result["implanted_by_month"] == [{"key": "2026-07", "value": 1}]


def test_summary_keeps_period_savings_and_active_when_no_new_implants_in_period() -> None:
    repo = PostgresKaizenRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(return_value=[_implanted_row()])

    result = repo.summary(
        branch_code="01",
        date_start="2026-07-01",
        date_end="2026-07-03",
    )

    assert result["total"] == 0
    assert result["period_implanted_count"] == 0
    assert result["period_savings"] > 0
    # 60s × 10 ocorr./dia = 0,1667 h/dia × dias úteis equivalentes (3 corridos)
    hours_day = (60.0 * 10.0) / 3600.0
    assert result["period_hours_saved"] == amount_for_active_calendar_days(hours_day, 3)
    assert result["active_hours_saved_per_day"] == pytest.approx(0.1667, rel=1e-2)
    assert result["active_count"] == 1
    assert result["active_annual_savings"] > 0
    assert result["realized_annual_savings"] == pytest.approx(2107.49, rel=1e-2)


def test_summary_period_savings_zero_for_future_competence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Filtro de competência futura não projeta ganhos ainda não realizados."""

    class _FixedDate(date):
        @classmethod
        def today(cls) -> date:  # type: ignore[override]
            return date(2026, 7, 8)

    monkeypatch.setattr(
        "app.domain.services.kaizen.kaizen_savings_validity.date",
        _FixedDate,
    )
    monkeypatch.setattr(
        "app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_repository.date",
        _FixedDate,
    )
    repo = PostgresKaizenRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        return_value=[_implanted_row(date_implemented=date(2026, 1, 10))]
    )

    result = repo.summary(
        branch_code="01",
        date_start="2026-08-01",
        date_end="2026-08-31",
    )

    assert result["period_implanted_count"] == 0
    assert result["period_savings"] == 0.0
    assert result["period_hours_saved"] == 0.0
    # Run-rate vigente continua refletindo kaizens ativos hoje.
    assert result["active_count"] == 1
    assert result["active_hours_saved_per_day"] == pytest.approx(0.1667, rel=1e-2)


def test_summary_counts_recebido_by_idea_received_anchor() -> None:
    """Caso original: recebido sem marcos entra nos totais do período pela
    data de recebimento da ideia, na unidade correta."""
    repo = PostgresKaizenRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        return_value=[
            _implanted_row(
                status="recebido",
                branch_code="02",
                date_committee_approved=None,
                date_implemented=None,
                date_idea_received=date(2026, 8, 12),
                created_at=date(2026, 8, 12),
                daily_savings=None,
                annual_savings=None,
                investment=Decimal("0"),
            )
        ]
    )

    result = repo.summary(
        branch_code="02",
        date_start="2026-01-01",
        date_end="2026-11-05",
    )

    assert result["total"] == 1
    assert result["recebidos"] == 1
    assert result["by_status"] == [{"key": "recebido", "value": 1}]
    assert result["by_branch"] == [{"key": "02", "value": 1}]
    # Não infla o indicador de quantidade (aprovados/implantados).
    assert result["period_implanted_count"] == 0
    assert result["aprovados"] == 0
    assert result["implantados"] == 0


def test_summary_counts_descontinuado_without_committee_by_idea_received() -> None:
    """Irmão: descontinuado sem data de comitê ancora no recebimento da ideia."""
    repo = PostgresKaizenRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        return_value=[
            _implanted_row(
                status="descontinuado",
                date_committee_approved=None,
                date_implemented=None,
                date_idea_received=date(2026, 3, 19),
                created_at=date(2026, 7, 2),
                daily_savings=None,
                annual_savings=None,
            )
        ]
    )

    result = repo.summary(
        branch_code="01",
        date_start="2026-01-01",
        date_end="2026-11-05",
    )

    assert result["total"] == 1
    assert result["descontinuados"] == 1


def test_summary_anchors_on_created_at_when_no_lifecycle_dates() -> None:
    """Fallback: cadastro legado sem nenhuma data de ciclo ancora na criação."""
    repo = PostgresKaizenRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        return_value=[
            _implanted_row(
                status="recebido",
                date_committee_approved=None,
                date_implemented=None,
                created_at=date(2026, 9, 10),
                daily_savings=None,
                annual_savings=None,
            )
        ]
    )

    result = repo.summary(
        branch_code="01",
        date_start="2026-09-01",
        date_end="2026-09-30",
    )

    assert result["total"] == 1
    assert result["recebidos"] == 1


def test_summary_excludes_record_anchored_outside_period() -> None:
    """Negativo: recebido anterior ao recorte continua fora dos totais."""
    repo = PostgresKaizenRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        return_value=[
            _implanted_row(
                status="recebido",
                date_committee_approved=None,
                date_implemented=None,
                date_idea_received=date(2025, 12, 15),
                created_at=date(2025, 12, 15),
                daily_savings=None,
                annual_savings=None,
            )
        ]
    )

    result = repo.summary(
        branch_code="01",
        date_start="2026-01-01",
        date_end="2026-11-05",
    )

    assert result["total"] == 0
    assert result["recebidos"] == 0
    assert result["by_status"] == []


def test_summary_recebidos_total_ignores_period() -> None:
    """O card de pendências conta recebidos do escopo mesmo fora do recorte
    de datas — um recebido antigo continua aguardando aprovação."""
    repo = PostgresKaizenRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        return_value=[
            _implanted_row(
                status="recebido",
                branch_code="02",
                date_committee_approved=None,
                date_implemented=None,
                date_idea_received=date(2025, 5, 10),
                created_at=date(2025, 5, 10),
                daily_savings=None,
                annual_savings=None,
            )
        ]
    )

    result = repo.summary(
        branch_code="02",
        date_start="2026-01-01",
        date_end="2026-11-05",
    )

    # Fora do período: não entra nos totais recortados…
    assert result["total"] == 0
    assert result["recebidos"] == 0
    # …mas continua pendente no escopo da unidade.
    assert result["recebidos_total"] == 1


def test_list_records_filters_multiple_statuses_and_savings_types() -> None:
    """Filtros multi-seleção da listagem: status e tipo de economia aceitam
    listas (repeated query param) e isolam com ANY."""
    repo = PostgresKaizenRepository(connection=MagicMock())
    captured: dict[str, object] = {}

    def _capture(query: str, params: object = None):
        captured["query"] = query
        captured["params"] = params
        return {"total": 0} if "COUNT" in query else []

    repo.fetch_one = MagicMock(side_effect=lambda q, p=None: {"total": 0})
    repo.fetch_all = MagicMock(side_effect=lambda q, p=None: captured.update(query=q, params=p) or [])

    repo.list_records(
        status=["recebido", "aprovado"],
        savings_type=["tempo", "material"],
        title="fita",
    )

    assert "k.status = ANY(%s)" in str(captured["query"])
    assert "k.savings_type = ANY(%s)" in str(captured["query"])
    assert ["recebido", "aprovado"] in captured["params"]
    assert ["tempo", "material"] in captured["params"]


def test_list_records_keeps_single_status_string_compatible() -> None:
    """Retrocompatibilidade: chamador com string única continua filtrando."""
    repo = PostgresKaizenRepository(connection=MagicMock())
    captured: dict[str, object] = {}

    repo.fetch_one = MagicMock(return_value={"total": 0})
    repo.fetch_all = MagicMock(side_effect=lambda q, p=None: captured.update(query=q, params=p) or [])

    repo.list_records(status="recebido")

    assert ["recebido"] in captured["params"]
