"""Entrada do motor. Os adapters traduzem Protheus e XML para estes objetos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class ProtheusHeader:
    branch: str
    number: str
    series: str
    supplier_code: str
    supplier_store: str
    supplier_name: str
    supplier_state: str
    supplier_tax_id: str
    species: str
    own_form: str
    access_key: str
    issue_date: date | None
    received_date: date | None
    freight_amount: float
    expense_amount: float
    icms_base: float
    icms_amount: float
    ipi_base: float
    ipi_amount: float
    goods_amount: float
    gross_amount: float
    discount_amount: float
    st_base: float
    st_amount: float
    insurance_amount: float


@dataclass(frozen=True)
class ProtheusItem:
    branch: str
    number: str
    series: str
    supplier_code: str
    supplier_store: str
    item: str
    product_code: str
    cfop: str
    tax_situation: str
    tes: str
    total_amount: float
    icms_base: float
    icms_rate: float
    icms_amount: float
    ipi_base: float
    ipi_rate: float
    ipi_amount: float
    st_amount: float


@dataclass(frozen=True)
class TesRecord:
    code: str
    description: str
    calculates_icms: str
    credits_icms: str
    icms_book: str
    calculates_ipi: str
    credits_ipi: str
    ipi_book: str
    consumption_material: str
    tes_type: str
    fiscal_code: str


@dataclass(frozen=True)
class XmlItem:
    number: int
    product_code: str
    description: str
    ncm: str
    cfop: str
    amount: float
    origin: str
    cst: str
    csosn: str
    icms_base: float
    icms_rate: float
    icms_amount: float
    ipi_amount: float
    ipi_base: float
    ipi_rate: float
    st_amount: float
    simple_credit: float = 0.0
    simple_rate: float = 0.0
    discount: float = 0.0
    other_amount: float = 0.0


@dataclass(frozen=True)
class XmlDocument:
    access_key: str
    model: str
    number: int
    series: str
    issued_at: datetime | None
    issuer_tax_id: str
    issuer_name: str
    issuer_state: str
    recipient_tax_id: str
    direction: str
    crt: str
    goods_amount: float
    freight_amount: float
    discount_amount: float
    other_amount: float
    icms_base: float
    icms_amount: float
    st_amount: float
    ipi_amount: float
    total_amount: float
    status_code: str
    cancelled: bool = False
    items: tuple[XmlItem, ...] = ()
    service_amount: float = 0.0
    cfop: str = ""
    origin_state: str = ""
    destination_state: str = ""
    taker_tax_id: str = ""
    icms_rate: float = 0.0
    cst: str = ""
    simples_national: bool = False
    substituted: bool = False
    linked_keys: tuple[str, ...] = ()
    taker_role: str = ""


@dataclass(frozen=True)
class AuditConfig:
    presumed_credit_tes: str = "004"
    freight_cfop_suffix: str = "352"
    tolerance: float = 0.05
    unmatched_grace_days: int = 3
    # D11 fica desligado no teste de paridade com a skill.
    improvements_enabled: bool = False
    # Com D11, «em trânsito» usa date_to da análise, não a maior emissão do download.
    period_end: date | None = None


@dataclass(frozen=True)
class Occurrence:
    rule_id: str
    title: str
    severity: str
    document_number: str
    item: str
    field: str
    protheus_value: str
    xml_value: str
    access_key: str
    why: str = ""
    action: str = ""


@dataclass(frozen=True)
class UnmatchedDocument:
    side: str
    document_number: str
    severity: str
    reason: str
    access_key: str
    species: str = ""
    series: str = ""
    party_name: str = ""
    party_tax_id: str = ""
    party_state: str = ""
    issue_date: str = ""
    amount: float | None = None
    icms_base: float | None = None
    icms_amount: float | None = None
    ipi_amount: float | None = None
    cfop: str = ""
    cst: str = ""
    nature: str = ""


@dataclass(frozen=True)
class FiscalBookLine:
    number: str
    series: str
    supplier_code: str
    supplier_store: str
    item: str
    icms_amount: float = 0.0
    other_icms: float = 0.0
    exempt_icms: float = 0.0
    ipi_amount: float = 0.0
    branch: str = ""
    movement: str = "E"
    cancelled: bool = False


@dataclass(frozen=True)
class ExcludedItem:
    kind: str
    document_number: str
    series: str
    supplier_code: str
    supplier_store: str
    item_count: int
    amount: float


@dataclass
class AuditResult:
    occurrences: list[Occurrence] = field(default_factory=list)
    unmatched: list[UnmatchedDocument] = field(default_factory=list)
    suppressed: dict[str, int] = field(default_factory=dict)
    not_reported: dict[str, int] = field(default_factory=dict)
    excluded: list[ExcludedItem] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def suppress(self, rule_id: str, label: str = "") -> None:
        self.suppressed[rule_id] = self.suppressed.get(rule_id, 0) + 1
        if label:
            self.not_reported[label] = self.not_reported.get(label, 0) + 1
