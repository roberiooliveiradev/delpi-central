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
    invoice_type: str = ""
    participant_kind: str = ""
    participant_name: str = ""
    participant_tax_id: str = ""
    participant_state: str = ""


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
    pis_amount: float = 0.0
    cofins_amount: float = 0.0
    # Reforma tributária (FA-8): grupo IBSCBS do item.
    has_ibscbs: bool = False
    ibscbs_cst: str = ""
    ibscbs_class: str = ""
    reform_base: float = 0.0
    ibs_uf_rate: float = 0.0
    ibs_uf_amount: float = 0.0
    ibs_mun_rate: float = 0.0
    ibs_mun_amount: float = 0.0
    cbs_rate: float = 0.0
    cbs_amount: float = 0.0


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
    operation_nature: str = ""
    # Reforma tributária (FA-8): IBSCBS do CT-e (imposto) e IBSCBSTot da NF-e.
    has_ibscbs: bool = False
    ibscbs_cst: str = ""
    ibscbs_class: str = ""
    reform_base: float = 0.0
    ibs_uf_rate: float = 0.0
    ibs_uf_amount: float = 0.0
    ibs_mun_rate: float = 0.0
    ibs_mun_amount: float = 0.0
    cbs_rate: float = 0.0
    cbs_amount: float = 0.0


@dataclass(frozen=True)
class ReformTaxLine:
    """IBS/CBS calculado por item (SD1→F2D→F2B) — FA-8."""

    branch: str
    number: str
    series: str
    supplier_code: str
    supplier_store: str
    item: str
    tes: str
    tax_code: str
    rule_code: str
    base_amount: float
    tax_rate: float
    tax_amount: float


@dataclass(frozen=True)
class ReformBookLine:
    """IBS/CBS no livro digital (CD2) — FA-12."""

    branch: str
    number: str
    series: str
    supplier_code: str
    supplier_store: str
    item: str
    tax_code: str
    cst: str
    base_amount: float
    tax_rate: float
    tax_amount: float


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
    # FA-1/FA-2 (onda 1): com a flag, o participante vem de participant_* — SA1 nas notas tipo B/D.
    participant_by_type_enabled: bool = False
    # FA-3 (onda 1): TES de insumo fora de «Crédito de IPI em uso e consumo»; vazio = regra para todas.
    input_tes: str = ""
    # FA-4 (onda 2): uma ocorrência por causa — itens dentro dela, acompanhantes como followers.
    cause_grouping_enabled: bool = False
    # FA-8 (onda 3): IBS/CBS em todas as entradas, NF-e e CT-e.
    ibscbs_enabled: bool = False
    # FA-9: exceções «crt:X», «cfop:YYYY», «tes:ZZZ» separadas por vírgula; vazio = sem exceção.
    ibscbs_exceptions: str = ""
    # FA-12: regra do livro IBS/CBS só para documentos a partir desta data (ISO); vazio = desligada.
    ibscbs_book_from: str = ""


@dataclass(frozen=True)
class OccurrenceItem:
    """Um item (ou o cabeçalho) dentro da causa — FA-4."""

    item: str
    field: str
    protheus_value: str
    xml_value: str
    difference: str = ""


@dataclass(frozen=True)
class OccurrenceFollower:
    """Divergência acompanhante («Acompanha…») que virou detalhe da causa — FA-4."""

    rule_id: str
    title: str
    field: str
    protheus_value: str
    xml_value: str
    why: str = ""


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
    cause_id: str = ""
    items: tuple[OccurrenceItem, ...] = ()
    followers: tuple[OccurrenceFollower, ...] = ()


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
