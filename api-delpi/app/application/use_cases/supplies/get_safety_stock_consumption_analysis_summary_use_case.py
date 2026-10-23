from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockConsumptionAnalysisQueryRequest,
)
from app.application.services.supplies.safety_stock_consumption_analysis_query_service import (
    SafetyStockConsumptionAnalysisQueryService,
)
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.supplies.safety_stock_consumption_analysis_service import (
    ANALYSIS_CALENDAR_DAYS,
    CONSUMPTION_MOVEMENT_TYPE,
    CONSUMPTION_PROFILE_RAW_MATERIAL,
    CONSUMPTION_PROFILE_REPLACEMENT_PART,
    CONSUMPTION_WAREHOUSE,
    REPLACEMENT_PART_CONSUMPTION_MOVEMENT_TYPE,
    REPLACEMENT_PART_CONSUMPTION_WAREHOUSE,
    SafetyStockConsumptionAnalysisService,
)
from app.domain.totvs.protheus_product_types import SUPPLIES_OTD_PRODUCT_CODE_PREFIX


class GetSafetyStockConsumptionAnalysisSummaryUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._query_service = SafetyStockConsumptionAnalysisQueryService(repository)

    def execute(self, request: SafetyStockConsumptionAnalysisQueryRequest) -> dict:
        items, period_start, period_end, period_business_days = (
            self._query_service.load_enriched_items(request)
        )
        summary = SafetyStockConsumptionAnalysisService.build_summary(items)
        return {
            **summary,
            "branch": request.branch,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "period_calendar_days": ANALYSIS_CALENDAR_DAYS,
            "period_business_days": period_business_days,
            "consumption_warehouse": CONSUMPTION_WAREHOUSE,
            # Legado: TM da MP (produção). Peças 3019 usam o perfil replacement_part.
            "consumption_movement_type": CONSUMPTION_MOVEMENT_TYPE,
            "replacement_part_consumption_movement_type": (
                REPLACEMENT_PART_CONSUMPTION_MOVEMENT_TYPE
            ),
            "consumption_profiles": {
                CONSUMPTION_PROFILE_RAW_MATERIAL: {
                    "warehouse": CONSUMPTION_WAREHOUSE,
                    "movement_type": CONSUMPTION_MOVEMENT_TYPE,
                    "requires_production_order": True,
                },
                CONSUMPTION_PROFILE_REPLACEMENT_PART: {
                    "warehouse": REPLACEMENT_PART_CONSUMPTION_WAREHOUSE,
                    "movement_type": REPLACEMENT_PART_CONSUMPTION_MOVEMENT_TYPE,
                    "requires_production_order": False,
                    "code_prefix": SUPPLIES_OTD_PRODUCT_CODE_PREFIX,
                },
            },
            "status_distribution": [
                {"status": "below_suggested", "count": summary["below_suggested"]},
                {"status": "above_suggested", "count": summary["above_suggested"]},
                {"status": "adequate", "count": summary["adequate"]},
                {
                    "status": "inconsistent_data",
                    "count": summary["inconsistent_data"],
                },
            ],
        }
