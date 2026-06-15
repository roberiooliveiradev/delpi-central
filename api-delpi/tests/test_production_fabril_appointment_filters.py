from datetime import date

from app.domain.production.production_fabril_appointment_scope import (
    EXCLUDED_WORK_CENTERS,
    STATUS_REGISTRO_OK,
)
from app.infrastructure.persistence.totvs.eficiencia_fabril.eficiencia_fabril_query_settings import (
    EficienciaFabrilQuerySettings,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_appointment_filters import (
    build_fabril_view_filters,
)


def test_build_fabril_view_filters_requires_ok_and_excludes_work_centers() -> None:
    where, params = build_fabril_view_filters(
        date_start=date(2026, 5, 1),
        date_end=date(2026, 5, 31),
        branch="01",
        status_ok_only=True,
    )

    assert "DATA_PRODUCAO" in where
    assert "FILIAL = ?" in where
    assert f"STATUS_REGISTRO = ?" in where
    assert STATUS_REGISTRO_OK in params
    for excluded in EXCLUDED_WORK_CENTERS:
        assert excluded in params


def test_build_fabril_view_filters_caps_efficiency_for_kpi() -> None:
    settings = EficienciaFabrilQuerySettings()
    where, params = build_fabril_view_filters(
        date_start="2026-05-01",
        date_end="2026-05-31",
        status_ok_only=True,
        efficiency_cap_pct=settings.max_efficiency_indicator_pct,
        column_prefix="EF",
    )

    assert "EF.EFICIENCIA_PERCENTUAL" in where
    assert settings.max_efficiency_indicator_pct in params


def test_ef_fabril_items_sql_includes_appointment_id_and_sh6010_apply() -> None:
    from app.infrastructure.persistence.totvs.production_fabril.production_fabril_ef_items_sql import (
        EF_FABRIL_ITEMS_FROM,
        EF_FABRIL_ITEMS_SELECT,
    )
    from app.infrastructure.persistence.totvs.production_fabril.production_fabril_sh6010_apply import (
        FABRIL_SH6010_OUTER_APPLY,
    )

    assert "appointment_id" in EF_FABRIL_ITEMS_SELECT
    assert "EF.FILIAL" in EF_FABRIL_ITEMS_SELECT
    assert "B1_UM" in EF_FABRIL_ITEMS_SELECT
    assert FABRIL_SH6010_OUTER_APPLY.strip() in EF_FABRIL_ITEMS_FROM
