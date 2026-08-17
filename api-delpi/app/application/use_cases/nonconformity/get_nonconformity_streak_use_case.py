from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.domain.ports.nonconformity.nonconformity_query_repository_port import (
    NonconformityQueryRepositoryPort,
)
from app.domain.services.calendar_occurrence_streak_service import (
    compute_occurrence_streak,
)
from app.domain.services.quality.nonconformity_query_filter_service import (
    normalize_nonconformity_filter_type,
)
from app.domain.services.quality.ppm_product_scope import normalize_ppm_product_prefix
from app.domain.totvs.protheus_branches import is_all_branches, normalize_branch_scope


class GetNonconformityStreakUseCase:
    """Dias corridos sem NC TOTVS (QI2), no mesmo filtro de tipo do dashboard.

    O indicador fecha no **dia anterior** (não inclui NC com ``QI2_OCORRE`` = hoje).
    """

    def __init__(self, repository: NonconformityQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        filter_type: str = "customer",
        branch: str | None = None,
        product_prefix: str | None = None,
        as_of: date | None = None,
    ) -> dict[str, Any]:
        normalized_type = normalize_nonconformity_filter_type(filter_type)
        normalized_branch: str | None = None
        if branch and not is_all_branches(branch):
            normalized_branch = normalize_branch_scope(branch)
        normalized_prefix = normalize_ppm_product_prefix(product_prefix)

        # Até o dia anterior: NC de hoje não entra no streak (TV / KPI diário).
        as_of_date = (as_of or date.today()) - timedelta(days=1)
        occurrence_dates = self._repository.list_occurrence_dates(
            filter_type=normalized_type,
            branch=normalized_branch,
            product_prefix=normalized_prefix,
        )
        streak = compute_occurrence_streak(occurrence_dates, as_of=as_of_date)
        return {
            **streak,
            "value": streak["current_days_without_nc"],
            "type": normalized_type,
            "branch": normalized_branch or "all",
            "product_prefix": normalized_prefix,
        }
