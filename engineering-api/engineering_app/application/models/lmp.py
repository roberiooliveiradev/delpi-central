"""Modelos da aplicação LMP — contratos facts (entrada) e funcionais (saída).

`LmpFact` espelha a projeção F-LMP-01 da api-delpi (doc 34 §3) — só
campos de origem + flags derivadas declaradas. `LmpDashboardItem` espelha
o shape do dashboard legado para paridade funcional.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from engineering_app.domain.lmp.dates import format_date_iso


@dataclass(frozen=True)
class LmpQuery:
    """Filtros funcionais validados na borda — datas ISO, branch, listing."""

    start_date: str | None = None
    end_date: str | None = None
    branch: str | None = None
    listing_type: str | None = None
    status_filter: str | None = None
    page: int = 1
    page_size: int = 50


@dataclass(frozen=True)
class LmpFact:
    """Linha de fato F-LMP-01 — sem campos calculados de negócio."""

    branch: str | None
    sale_number: str
    sale_description: str
    listing_kind_source: str | None
    listing_kind: str | None  # classe efetiva executada na fonte (referência)
    has_sample_anchor: bool
    has_lmp_finalized: bool
    sample_eng_minutes: int
    residence_minutes: int | None
    start_date: str | None
    end_date: str | None
    homolog_revision: str | None
    measurement_revision: str | None
    homolog_date: str | None
    cycle_index: int
    engineering_status: str | None
    qtd_engineering_entries: int
    qtd_engineering_closed: int
    qtd_advanced_from_engineering: int
    qtd_returned_from_engineering: int
    qtd_pi: int = 0

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LmpFact":
        if not isinstance(raw, dict) or not raw.get("sale_number"):
            raise ValueError("fact row sem sale_number")
        return cls(
            branch=raw.get("branch"),
            sale_number=str(raw["sale_number"]),
            sale_description=str(raw.get("sale_description") or ""),
            listing_kind_source=raw.get("listing_kind_source"),
            listing_kind=raw.get("listing_kind"),
            has_sample_anchor=bool(raw.get("has_sample_anchor")),
            has_lmp_finalized=bool(raw.get("has_lmp_finalized")),
            sample_eng_minutes=int(raw.get("sample_eng_minutes") or 0),
            residence_minutes=(
                int(raw["residence_minutes"])
                if raw.get("residence_minutes") is not None
                else None
            ),
            start_date=raw.get("start_date"),
            end_date=raw.get("end_date"),
            homolog_revision=raw.get("homolog_revision"),
            measurement_revision=raw.get("measurement_revision"),
            homolog_date=raw.get("homolog_date"),
            cycle_index=int(raw.get("cycle_index") or 1),
            engineering_status=raw.get("engineering_status"),
            qtd_engineering_entries=int(raw.get("qtd_engineering_entries") or 0),
            qtd_engineering_closed=int(raw.get("qtd_engineering_closed") or 0),
            qtd_advanced_from_engineering=int(
                raw.get("qtd_advanced_from_engineering") or 0
            ),
            qtd_returned_from_engineering=int(
                raw.get("qtd_returned_from_engineering") or 0
            ),
            qtd_pi=int(raw.get("qtd_pi") or 0),
        )


@dataclass
class LmpDashboardItem:
    """Item funcional do contrato E-LMP-01 — paridade com o legado."""

    branch: Optional[str]
    sale_number: str
    sale_description: str
    listing_kind: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    nivel: str
    dias_uteis_sla: int
    sla_minutos: int
    engineering_total_minutes: int
    data_limite: Optional[str]
    lead_time_util: Optional[int]
    status: str
    homolog_revision: Optional[str] = None
    measurement_revision: Optional[str] = None
    homolog_date: Optional[str] = None
    cycle_index: int = 1
    engineering_status: Optional[str] = None
    qtd_pi: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("start_date", "end_date", "data_limite", "homolog_date"):
            data[key] = format_date_iso(data.get(key))
        return data


@dataclass(frozen=True)
class LmpFactsResult:
    """Resposta normalizada do port facts — estado honesto de fonte."""

    status: str  # "available" | "empty" | "unavailable" | "forbidden"
    facts: tuple[LmpFact, ...] = ()
    total: int | None = None
    reason: str | None = None
    message: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LmpPiCountsResult:
    """Resposta normalizada do port F-LMP-04 — mapa chave→contagem."""

    status: str  # "available" | "empty" | "unavailable" | "forbidden"
    counts: tuple[tuple[tuple[str, str, str], int], ...] = ()
    reason: str | None = None
    message: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def get(self, key: tuple[str, str, str], default: int = 0) -> int:
        for candidate, value in self.counts:
            if candidate == key:
                return value
        return default
