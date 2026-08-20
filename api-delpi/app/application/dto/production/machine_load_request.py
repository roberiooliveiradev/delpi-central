"""DTOs — carga máquina."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.domain.production.machine_load_scope import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT,
    DEFAULT_WINDOW_DAYS,
    MAX_PAGE_SIZE,
    MAX_WINDOW_DAYS,
    SORT_VALUES,
    VALID_MACHINE_LOAD_BRANCHES,
)
from app.domain.totvs.protheus_operation_appointments import (
    ACTIVE_APPOINTMENT_LOOKBACK_DAYS,
    APPOINTMENT_HISTORY_LOOKBACK_DAYS,
)


def _parse_iso_date(value: str | None) -> date | None:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _as_bool(value: bool | str | None) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "sim", "s"}:
        return True
    if text in {"0", "false", "no", "nao", "não", "n"}:
        return False
    raise ValueError(f"Valor booleano inválido: {value!r}")


def _protheus_date(value: date) -> str:
    return value.strftime("%Y%m%d")


@dataclass(frozen=True, slots=True)
class MachineLoadWindow:
    """Janela da carga máquina — programação (H8_DTINI) ou entrega efetiva do PA.

    Com ``delivery_start`` / ``delivery_end`` o recorte é a **entrega**: é como o
    PCP planeja (o que vence primeiro), e a janela de programação deixa de valer.
    O início pode ficar aberto, para não esconder OP atrasada.

    ``reference`` é o "hoje" do turno: dele saem as janelas de recência do
    apontamento (HZA), independentes do período escolhido pelo usuário.
    """

    scheduled_start: date
    scheduled_end: date
    branch: str | None
    reference: date
    delivery_start: date | None = None
    delivery_end: date | None = None

    @classmethod
    def resolve(
        cls,
        *,
        branch: str | None,
        scheduled_start: str | None = None,
        scheduled_end: str | None = None,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        today: date | None = None,
    ) -> MachineLoadWindow:
        normalized_branch = str(branch or "").strip() or None
        if (
            normalized_branch is not None
            and normalized_branch not in VALID_MACHINE_LOAD_BRANCHES
        ):
            raise ValueError('branch inválida. Use "01" ou "02".')

        parsed_start = _parse_iso_date(scheduled_start)
        parsed_end = _parse_iso_date(scheduled_end)
        if scheduled_start and parsed_start is None:
            raise ValueError("scheduled_start inválida. Use o formato YYYY-MM-DD.")
        if scheduled_end and parsed_end is None:
            raise ValueError("scheduled_end inválida. Use o formato YYYY-MM-DD.")

        reference = today or date.today()
        if parsed_start is None and parsed_end is None:
            start = reference
            end = reference + timedelta(days=DEFAULT_WINDOW_DAYS)
        elif parsed_start is None:
            end = parsed_end  # type: ignore[assignment]
            start = end - timedelta(days=DEFAULT_WINDOW_DAYS)
        elif parsed_end is None:
            start = parsed_start
            end = start + timedelta(days=DEFAULT_WINDOW_DAYS)
        else:
            start, end = parsed_start, parsed_end

        parsed_delivery_start = _parse_iso_date(delivery_start)
        parsed_delivery_end = _parse_iso_date(delivery_end)
        if delivery_start and parsed_delivery_start is None:
            raise ValueError("delivery_start inválida. Use o formato YYYY-MM-DD.")
        if delivery_end and parsed_delivery_end is None:
            raise ValueError("delivery_end inválida. Use o formato YYYY-MM-DD.")
        if (
            parsed_delivery_start is not None
            and parsed_delivery_end is not None
            and parsed_delivery_start > parsed_delivery_end
        ):
            raise ValueError("delivery_start não pode ser posterior a delivery_end.")

        if start > end:
            raise ValueError(
                "scheduled_start não pode ser posterior a scheduled_end."
            )
        if (end - start).days + 1 > MAX_WINDOW_DAYS:
            raise ValueError(f"Período máximo permitido: {MAX_WINDOW_DAYS} dias.")
        return cls(
            scheduled_start=start,
            scheduled_end=end,
            branch=normalized_branch,
            reference=reference,
            delivery_start=parsed_delivery_start,
            delivery_end=parsed_delivery_end,
        )

    @property
    def filters_by_delivery(self) -> bool:
        return self.delivery_start is not None or self.delivery_end is not None

    def filter_kwargs(self) -> dict[str, Any]:
        return {
            "scheduled_start": _protheus_date(self.scheduled_start),
            "scheduled_end": _protheus_date(self.scheduled_end),
            "delivery_start": (
                self.delivery_start.isoformat() if self.delivery_start else None
            ),
            "delivery_end": self.delivery_end.isoformat() if self.delivery_end else None,
            "branch": self.branch,
            "appointment_active_since": _protheus_date(
                self.reference - timedelta(days=ACTIVE_APPOINTMENT_LOOKBACK_DAYS)
            ),
            "appointment_history_since": _protheus_date(
                self.reference - timedelta(days=APPOINTMENT_HISTORY_LOOKBACK_DAYS)
            ),
        }

    def period_dict(self) -> dict[str, str | None]:
        return {
            "scheduled_start": self.scheduled_start.isoformat(),
            "scheduled_end": self.scheduled_end.isoformat(),
            "delivery_start": (
                self.delivery_start.isoformat() if self.delivery_start else None
            ),
            "delivery_end": self.delivery_end.isoformat() if self.delivery_end else None,
            "period_field": "delivery_date" if self.filters_by_delivery else "scheduled_date",
            "branch": self.branch,
        }


@dataclass(frozen=True, slots=True)
class MachineLoadFilterRequest:
    window: MachineLoadWindow
    work_center: str | None = None
    product_code: str | None = None
    production_order: str | None = None
    tool: str | None = None
    open_only: bool | None = True

    @classmethod
    def from_params(
        cls,
        *,
        window: MachineLoadWindow,
        work_center: str | None = None,
        product_code: str | None = None,
        production_order: str | None = None,
        tool: str | None = None,
        open_only: bool | str | None = None,
    ) -> MachineLoadFilterRequest:
        resolved_open = _as_bool(open_only)
        return cls(
            window=window,
            work_center=(str(work_center).strip() or None)
            if work_center is not None
            else None,
            product_code=(str(product_code).strip() or None)
            if product_code is not None
            else None,
            production_order=(str(production_order).strip() or None)
            if production_order is not None
            else None,
            tool=(str(tool).strip() or None) if tool is not None else None,
            open_only=True if resolved_open is None else resolved_open,
        )

    def filter_kwargs(self) -> dict[str, Any]:
        return {
            **self.window.filter_kwargs(),
            "work_center": self.work_center,
            "product_code": self.product_code,
            "production_order": self.production_order,
            "tool": self.tool,
            "open_only": self.open_only,
        }

    def filters_dict(self) -> dict[str, Any]:
        return {
            **self.window.period_dict(),
            "work_center": self.work_center,
            "product_code": self.product_code,
            "production_order": self.production_order,
            "tool": self.tool,
            "open_only": self.open_only,
        }


@dataclass(frozen=True, slots=True)
class MachineLoadOperationsRequest(MachineLoadFilterRequest):
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    sort: str = DEFAULT_SORT

    @classmethod
    def from_params(  # type: ignore[override]
        cls,
        *,
        window: MachineLoadWindow,
        work_center: str | None = None,
        product_code: str | None = None,
        production_order: str | None = None,
        tool: str | None = None,
        open_only: bool | str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort: str | None = None,
    ) -> MachineLoadOperationsRequest:
        base = MachineLoadFilterRequest.from_params(
            window=window,
            work_center=work_center,
            product_code=product_code,
            production_order=production_order,
            tool=tool,
            open_only=open_only,
        )
        resolved_sort = (sort or DEFAULT_SORT).strip()
        if resolved_sort not in SORT_VALUES:
            raise ValueError(f"sort inválido. Use um de: {', '.join(SORT_VALUES)}.")
        return cls(
            window=base.window,
            work_center=base.work_center,
            product_code=base.product_code,
            production_order=base.production_order,
            tool=base.tool,
            open_only=base.open_only,
            page=max(1, int(page or 1)),
            page_size=min(max(1, int(page_size or DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE),
            sort=resolved_sort,
        )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
