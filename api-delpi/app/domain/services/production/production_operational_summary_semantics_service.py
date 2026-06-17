"""Semântica de summary em rotas playbook — flags consumidas pelo chat (sem texto aqui)."""


class ProductionOperationalSummarySemanticsService:
    @classmethod
    def consolidated_for_ranking(
        cls,
        *,
        branch: str | None,
        group_by: str,
    ) -> bool | None:
        """Ranking TOP N: consolidado só quando agrega por item (group_by=general) sem filial."""
        if branch is not None:
            return False

        if group_by == "general":
            return True

        return False

    @classmethod
    def consolidated_for_product_aggregation(cls, *, branch: str | None) -> bool:
        """Consumo/agregação por produto pai — soma todas as filiais quando branch omitida."""
        return branch is None
