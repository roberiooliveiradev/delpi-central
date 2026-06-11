class ProductionLossTypeFilterService:
    _LOSS_TYPES = {
        "refugo": ("R",),
        "scrap": ("S",),
        "both": ("R", "S"),
    }

    @classmethod
    def resolve_types(cls, loss_type: str | None) -> tuple[str, ...]:
        key = (loss_type or "both").strip().lower()
        return cls._LOSS_TYPES.get(key, cls._LOSS_TYPES["both"])

    @classmethod
    def sql_in_clause(cls, loss_type: str | None) -> tuple[str, list[str]]:
        types = cls.resolve_types(loss_type)
        placeholders = ", ".join("?" for _ in types)
        return f"BC.BC_TIPO IN ({placeholders})", list(types)
