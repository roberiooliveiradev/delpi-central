from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

VALID_BRANCHES = frozenset({"01", "02"})


@dataclass(frozen=True, slots=True)
class PeriodFilterRequest:
    start_date: str
    end_date: str
    branch: str | None = None

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
    ) -> PeriodFilterRequest:
        normalized_start = str(start_date or "").strip()
        normalized_end = str(end_date or "").strip()
        if not normalized_start or not normalized_end:
            raise ValueError("start_date e end_date são obrigatórios.")

        return cls(
            start_date=normalized_start,
            end_date=normalized_end,
            branch=cls._normalize_branch(branch),
        )

    @staticmethod
    def _normalize_branch(branch: str | None) -> str | None:
        if branch is None:
            return None

        normalized = str(branch).strip()
        if not normalized:
            return None

        if normalized not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        return normalized

    def resolve_protheus_period(self) -> tuple[str, str]:
        qb = QueryBuilder()
        start = qb.convert_date_to_protheus(self.start_date)
        end = qb.convert_date_to_protheus(self.end_date)

        if not start:
            raise ValueError(
                "start_date inválida. Use formatos como YYYYMMDD ou YYYY-MM-DD."
            )
        if not end:
            raise ValueError(
                "end_date inválida. Use formatos como YYYYMMDD ou YYYY-MM-DD."
            )
        if start > end:
            raise ValueError("start_date não pode ser maior que end_date.")

        return start, end
