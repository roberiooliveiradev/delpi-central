import re
from dataclasses import dataclass
from datetime import date

from app.domain.totvs.protheus_branches import normalize_branch_code
from app.infrastructure.persistence.totvs.production_repositories.consumption_audit_sql import (
    SEARCH_DATE_TYPES,
    SEARCH_SORT_DIRECTIONS,
    SEARCH_SORT_FIELDS,
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_STATUS_RE = re.compile(r"^[0-9A-Z ]$")
_OP_FRAGMENT_RE = re.compile(r"^[0-9A-Z]{1,11}$")


def _clean(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _date_or_none(value: object, name: str) -> str | None:
    text = _clean(value, 10)
    if not text:
        return None
    if not _DATE_RE.match(text):
        raise ValueError(f"{name} inválida: formato esperado AAAA-MM-DD.")
    try:
        date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"{name} inválida: data inexistente.")
    return text


@dataclass(frozen=True)
class SearchConsumptionAuditOrdersRequest:
    """Filtros da listagem paginada de OPs da Auditoria de Consumo (GLPI #1353).

    ``date_type`` decide qual data real filtra ``period_start``/``period_end``:
    ``emission`` (C2_EMISSAO), ``finished`` (C2_DATRF) ou ``appointment``
    (SH6.H6_DTAPONT via EXISTS) — semânticas distintas, nunca confundidas.
    """

    branch: str
    search: str | None = None
    product: str | None = None
    date_type: str = "emission"
    period_start: str | None = None
    period_end: str | None = None
    status: str | None = None
    work_center: str | None = None
    operation: str | None = None
    page: int = 1
    page_size: int = 25
    sort_by: str | None = None
    sort_direction: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", normalize_branch_code(self.branch))

        if self.date_type not in SEARCH_DATE_TYPES:
            raise ValueError(
                f"date_type inválido: {self.date_type!r} — use "
                f"{'|'.join(SEARCH_DATE_TYPES)}."
            )

        search = _clean(self.search, 40).upper() or None
        if search and not _OP_FRAGMENT_RE.match(search):
            raise ValueError(
                "search inválido: até 11 posições alfanuméricas "
                "(fragmento da chave C2_OP/C2_NUM)."
            )
        object.__setattr__(self, "search", search)

        object.__setattr__(self, "product", _clean(self.product, 60) or None)
        object.__setattr__(
            self, "period_start", _date_or_none(self.period_start, "period_start")
        )
        object.__setattr__(
            self, "period_end", _date_or_none(self.period_end, "period_end")
        )
        if (
            self.period_start
            and self.period_end
            and self.period_start > self.period_end
        ):
            raise ValueError("period_start não pode ser maior que period_end.")

        status = _clean(self.status, 1).upper() or None
        if status and not _STATUS_RE.match(status):
            raise ValueError("status inválido: 1 caractere alfanumérico.")
        object.__setattr__(self, "status", status)

        object.__setattr__(
            self, "work_center", _clean(self.work_center, 20).upper() or None
        )
        object.__setattr__(
            self, "operation", _clean(self.operation, 4).upper() or None
        )

        page = int(self.page) if self.page is not None else 1
        page_size = int(self.page_size) if self.page_size is not None else 25
        if page < 1:
            raise ValueError("page deve ser >= 1.")
        if not (1 <= page_size <= 50):
            raise ValueError("page_size deve estar entre 1 e 50.")
        object.__setattr__(self, "page", page)
        object.__setattr__(self, "page_size", page_size)

        sort_by = _clean(self.sort_by, 30).lower() or None
        sort_direction = _clean(self.sort_direction, 4).lower() or None
        if sort_by and sort_by not in SEARCH_SORT_FIELDS:
            raise ValueError(
                f"sort_by inválido: {sort_by!r} — use "
                f"{'|'.join(SEARCH_SORT_FIELDS)}."
            )
        if sort_direction and not sort_by:
            raise ValueError("sort_direction exige sort_by.")
        if sort_direction and sort_direction not in SEARCH_SORT_DIRECTIONS:
            raise ValueError(
                f"sort_direction inválido: {sort_direction!r} — use "
                f"{'|'.join(SEARCH_SORT_DIRECTIONS)}."
            )
        object.__setattr__(self, "sort_by", sort_by)
        object.__setattr__(
            self,
            "sort_direction",
            sort_direction or ("asc" if sort_by else None),
        )
