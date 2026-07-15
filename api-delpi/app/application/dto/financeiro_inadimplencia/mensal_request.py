from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.application.dto.financeiro_inadimplencia.period_filter_request import (
    PeriodFilterRequest,
)
from app.application.dto.financeiro_inadimplencia.query_request import (
    InadimplenciaQueryRequest,
)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def parse_customer_pairs(customers: str | None) -> tuple[tuple[str, str], ...]:
    """Aceita `CODIGO/LOJA,CODIGO/LOJA` (também `::` como separador interno)."""
    if customers is None:
        return ()
    raw = str(customers).strip()
    if not raw:
        return ()

    pairs: list[tuple[str, str]] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        if "/" in token:
            code, store = token.split("/", 1)
        elif "::" in token:
            code, store = token.split("::", 1)
        else:
            raise ValueError(
                "Parâmetro customers inválido. Use CODIGO/LOJA separados por vírgula."
            )
        code_norm = code.strip()
        store_norm = store.strip()
        if not code_norm or not store_norm:
            raise ValueError(
                "Parâmetro customers inválido. Cada item precisa de código e loja."
            )
        pairs.append((code_norm, store_norm))
    return tuple(pairs)


@dataclass(frozen=True, slots=True)
class InadimplenciaMensalQueryRequest:
    start_date: str | None = None
    end_date: str | None = None
    customer_code: str | None = None
    store_code: str | None = None
    customer_pairs: tuple[tuple[str, str], ...] = ()
    novos_negocios: bool = False

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        customer_code: str | None = None,
        store_code: str | None = None,
        customers: str | None = None,
        novos_negocios: bool = False,
    ) -> InadimplenciaMensalQueryRequest:
        period = PeriodFilterRequest.from_query(
            start_date=start_date,
            end_date=end_date,
        )
        pairs = parse_customer_pairs(customers)
        single_code = _normalize_optional_text(customer_code)
        single_store = _normalize_optional_text(store_code)
        if pairs:
            single_code = None
            single_store = None
        return cls(
            start_date=period.start_date,
            end_date=period.end_date,
            customer_code=single_code,
            store_code=single_store,
            customer_pairs=pairs,
            novos_negocios=bool(novos_negocios),
        )

    def to_base_request(self) -> InadimplenciaQueryRequest:
        return InadimplenciaQueryRequest(
            start_date=self.start_date,
            end_date=self.end_date,
        )

    def resolve_period(
        self,
        *,
        today: date | None = None,
    ) -> tuple[date, date, str]:
        return self.to_base_request().resolve_period(today=today)

    def periodo_dict(self, *, today: date | None = None) -> dict[str, str]:
        return self.to_base_request().periodo_dict(today=today)
