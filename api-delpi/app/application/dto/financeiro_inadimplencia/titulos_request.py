from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.application.dto.financeiro_inadimplencia.constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_DIR,
    DEFAULT_TITULOS_SORT_BY,
    MAX_PAGE_SIZE,
    VALID_FAIXA_ATRASO_CODES,
    VALID_SORT_DIR,
    VALID_TITULO_STATUS,
    VALID_TITULOS_SORT_BY,
)
from app.application.dto.financeiro_inadimplencia.query_request import (
    InadimplenciaQueryRequest,
)


@dataclass(frozen=True, slots=True)
class InadimplenciaTitulosRequest:
    start_date: str | None = None
    end_date: str | None = None
    customer_code: str | None = None
    store_code: str | None = None
    status: str = "all"
    delay_range: str | None = None
    q: str | None = None
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    sort_by: str = DEFAULT_TITULOS_SORT_BY
    sort_dir: str = DEFAULT_SORT_DIR

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        customer_code: str | None = None,
        store_code: str | None = None,
        status: str = "all",
        delay_range: str | None = None,
        q: str | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort_by: str = DEFAULT_TITULOS_SORT_BY,
        sort_dir: str = DEFAULT_SORT_DIR,
    ) -> InadimplenciaTitulosRequest:
        base = InadimplenciaQueryRequest.from_query(
            start_date=start_date,
            end_date=end_date,
        )
        normalized_status = str(status or "all").strip().lower() or "all"
        if normalized_status not in VALID_TITULO_STATUS:
            raise ValueError(
                "status inválido. Use all, on_time ou late."
            )

        normalized_delay_range = _normalize_optional_text(delay_range)
        if (
            normalized_delay_range is not None
            and normalized_delay_range not in VALID_FAIXA_ATRASO_CODES
        ):
            raise ValueError(
                "delay_range inválido. Use um dos códigos oficiais de FAIXA_ATRASO."
            )

        normalized_sort_by = (
            str(sort_by or DEFAULT_TITULOS_SORT_BY).strip()
            or DEFAULT_TITULOS_SORT_BY
        )
        normalized_sort_dir = (
            str(sort_dir or DEFAULT_SORT_DIR).strip().lower() or DEFAULT_SORT_DIR
        )

        if normalized_sort_by not in VALID_TITULOS_SORT_BY:
            raise ValueError(
                "sort_by inválido. Use um dos campos permitidos: "
                + ", ".join(sorted(VALID_TITULOS_SORT_BY))
                + "."
            )
        if normalized_sort_dir not in VALID_SORT_DIR:
            raise ValueError("sort_dir inválido. Use asc ou desc.")

        return cls(
            start_date=base.start_date,
            end_date=base.end_date,
            customer_code=_normalize_optional_text(customer_code),
            store_code=_normalize_optional_text(store_code),
            status=normalized_status,
            delay_range=normalized_delay_range,
            q=_normalize_optional_text(q),
            page=page,
            page_size=page_size,
            sort_by=normalized_sort_by,
            sort_dir=normalized_sort_dir,
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
