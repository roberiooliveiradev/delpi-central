"""Regressão — SQL de eficiência canônico compartilhado (OEE + eficiência fabril)."""

from app.infrastructure.persistence.totvs.production_fabril.production_fabril_efficiency_sql import (
    FABRIL_EFICIENCIA_PERCENTUAL_SQL,
    FABRIL_META_POR_HORA_SQL,
    FABRIL_TEMPO_PREVISTO_SQL,
    fabril_recalculated_efficiency_status_expr,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_ef_items_sql import (
    EF_FABRIL_ITEMS_SELECT,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_sql import (
    OEE_FABRIL_APPOINTMENTS_SELECT,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_standard_time_sql import (
    build_fabril_standard_time_ranked_ctes,
)


def test_ef_and_oee_share_canonical_efficiency_expression() -> None:
    assert FABRIL_EFICIENCIA_PERCENTUAL_SQL in EF_FABRIL_ITEMS_SELECT
    assert FABRIL_EFICIENCIA_PERCENTUAL_SQL in OEE_FABRIL_APPOINTMENTS_SELECT
    assert FABRIL_TEMPO_PREVISTO_SQL in EF_FABRIL_ITEMS_SELECT
    assert "HY_TEMPAD" in FABRIL_META_POR_HORA_SQL


def test_oee_listing_status_uses_recalculated_pct() -> None:
    assert "EF.EFICIENCIA_PERCENTUAL" not in OEE_FABRIL_APPOINTMENTS_SELECT.split("AS oee_pct")[0]
    assert "valid" in fabril_recalculated_efficiency_status_expr()
    assert FABRIL_EFICIENCIA_PERCENTUAL_SQL in OEE_FABRIL_APPOINTMENTS_SELECT


def test_standard_time_ctes_are_set_based() -> None:
    cte, params = build_fabril_standard_time_ranked_ctes(branch="01")
    assert "SHY_RANKED" in cte
    assert "SG2_RANKED" in cte
    assert "SHY010" in cte
    assert "SG2010" in cte
    assert params == ("01", "01")
