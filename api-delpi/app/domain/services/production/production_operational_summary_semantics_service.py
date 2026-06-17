"""Semântica de summary em rotas playbook — flags consumidas pelo chat (sem texto aqui)."""

from app.domain.services.production.production_consumption_top_items_group_by_service import (
    ProductionConsumptionTopItemsGroupByService,
)


class ProductionOperationalSummarySemanticsService:
    @classmethod
    def consolidated_for_ranking(
        cls,
        *,
        branch: str | None,
        group_by: str,
    ) -> bool | None:
        """Ranking TOP N: consolidado conforme perfil da dimensão de agrupamento."""
        if branch is not None:
            return False

        spec = ProductionConsumptionTopItemsGroupByService.resolve(group_by)

        return spec.consolidated_when_no_branch_filter

    @classmethod
    def consolidated_for_product_aggregation(cls, *, branch: str | None) -> bool:
        """Consumo/agregação por produto pai — soma todas as filiais quando branch omitida."""
        return branch is None
