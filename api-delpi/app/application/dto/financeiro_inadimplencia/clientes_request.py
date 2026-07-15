from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.application.dto.financeiro_inadimplencia.constantes import (
    DEFAULT_CLIENTES_SORT_BY,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_DIR,
    MAX_PAGE_SIZE,
    VALID_CLIENTES_SORT_BY,
    VALID_SORT_DIR,
)
from app.application.dto.financeiro_inadimplencia.query_request import (
    InadimplenciaQueryRequest,
)


@dataclass(frozen=True, slots=True)
class InadimplenciaClientesRequest:
    start_date: str | None = None
    end_date: str | None = None
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    sort_by: str = DEFAULT_CLIENTES_SORT_BY
    sort_dir: str = DEFAULT_SORT_DIR
    q: str | None = None
    only_with_delays: bool = True

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort_by: str = DEFAULT_CLIENTES_SORT_BY,
        sort_dir: str = DEFAULT_SORT_DIR,
        q: str | None = None,
        only_with_delays: bool = True,
    ) -> InadimplenciaClientesRequest:
        base = InadimplenciaQueryRequest.from_query(
            start_date=start_date,
            end_date=end_date,
        )
        normalized_sort_by = (
            str(sort_by or DEFAULT_CLIENTES_SORT_BY).strip()
            or DEFAULT_CLIENTES_SORT_BY
        )
        normalized_sort_dir = (
            str(sort_dir or DEFAULT_SORT_DIR).strip().lower() or DEFAULT_SORT_DIR
        )

        if normalized_sort_by not in VALID_CLIENTES_SORT_BY:
            raise ValueError(
                "sort_by inválido. Use um dos campos permitidos: "
                + ", ".join(sorted(VALID_CLIENTES_SORT_BY))
                + "."
            )
        if normalized_sort_dir not in VALID_SORT_DIR:
            raise ValueError("sort_dir inválido. Use asc ou desc.")

        return cls(
            start_date=base.start_date,
            end_date=base.end_date,
            page=page,
            page_size=page_size,
            sort_by=normalized_sort_by,
            sort_dir=normalized_sort_dir,
            q=_normalize_optional_text(q),
            only_with_delays=bool(only_with_delays),
        )

    def resolve_period(
        self,
        *,
        today: date | None = None,
    ) -> tuple[date, date, str]:
        return InadimplenciaQueryRequest(
            start_date=self.start_date,
            end_date=self.end_date,
        ).resolve_period(today=today)

    def periodo_dict(self, *, today: date | None = None) -> dict[str, str]:
        return InadimplenciaQueryRequest(
            start_date=self.start_date,
            end_date=self.end_date,
        ).periodo_dict(today=today)

    def resolve_page(self) -> int:
        return max(int(self.page), 1)

    def resolve_page_size(self) -> int:
        return min(max(int(self.page_size), 1), MAX_PAGE_SIZE)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
