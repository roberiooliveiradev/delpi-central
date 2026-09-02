"""Rateio proporcional do frete de compra — regra pura, sem I/O.

Um CT-e cobre uma ou mais NFs de compra. O valor bruto do CT-e é distribuído
entre essas NFs na proporção do valor de mercadoria de cada uma, e o percentual
de frete da NF é a soma do que lhe foi rateado dividida pela sua mercadoria.

Toda aritmética usa ``Decimal``: o percentual é comparado com o limite da filial
na fronteira exata (3,25%), onde o erro de ``float`` decidiria alerta indevido.

Inconsistência nunca é escondida nem convertida em zero. Vínculo sem NF, sem
CT-e ou sem base de rateio sai classificado com código e fica fora dos totais
válidos, para que o usuário veja o furo em vez de um percentual inventado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Mapping, Sequence

_CENTS = Decimal("0.01")
_ZERO = Decimal("0")

REASON_NF_NOT_FOUND = "nf_not_found"
REASON_CTE_NOT_FOUND = "cte_not_found"
REASON_NF_GOODS_VALUE_NOT_POSITIVE = "nf_goods_value_not_positive"
REASON_CTE_GROSS_VALUE_NOT_POSITIVE = "cte_gross_value_not_positive"
REASON_DUPLICATED_LINK = "duplicated_link"
REASON_CTE_WITHOUT_VALID_BASE = "cte_without_valid_base"
REASON_SPECIAL_OR_UNKNOWN_CTE = "special_or_unknown_cte"
REASON_BRANCH_WITHOUT_LIMIT = "branch_without_limit"

SITUATION_NORMAL = "normal"
SITUATION_ABOVE_LIMIT = "above_limit"
SITUATION_INCONSISTENT = "inconsistent"


@dataclass(frozen=True)
class FreightLink:
    """Um vínculo NF de compra x CT-e, já traduzido do contrato da api-delpi."""

    branch: str
    in_filter: bool
    invoice_found: bool
    invoice_document: str
    invoice_series: str
    supplier_code: str
    supplier_store: str
    supplier_name: str
    goods_value: Decimal | None
    invoice_issue_date: str
    invoice_entry_date: str
    freight_found: bool
    freight_document: str
    freight_series: str
    carrier_code: str
    carrier_store: str
    carrier_name: str
    freight_gross_value: Decimal | None
    freight_issue_date: str
    freight_document_type: str
    freight_document_kind: str

    @property
    def invoice_key(self) -> tuple[str, ...]:
        return (
            self.branch,
            self.invoice_document,
            self.invoice_series,
            self.supplier_code,
            self.supplier_store,
        )

    @property
    def freight_key(self) -> tuple[str, ...]:
        return (
            self.branch,
            self.freight_document,
            self.freight_series,
            self.carrier_code,
            self.carrier_store,
        )

    @property
    def link_key(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (self.invoice_key, self.freight_key)

    @property
    def has_usable_goods_value(self) -> bool:
        return self.invoice_found and (self.goods_value or _ZERO) > _ZERO


@dataclass(frozen=True)
class FreightAllocation:
    """Parcela de um CT-e atribuída a uma NF."""

    freight_document: str
    freight_series: str
    carrier_code: str
    carrier_store: str
    carrier_name: str
    freight_issue_date: str
    freight_gross_value: Decimal
    allocation_base: Decimal
    allocated_value: Decimal
    linked_invoice_count: int


@dataclass(frozen=True)
class FreightInvoice:
    branch: str
    invoice_document: str
    invoice_series: str
    supplier_code: str
    supplier_store: str
    supplier_name: str
    issue_date: str
    entry_date: str
    goods_value: Decimal
    freight_total: Decimal
    freight_percent: Decimal | None
    freight_limit: Decimal | None
    situation: str
    allocations: tuple[FreightAllocation, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class FreightInconsistency:
    reason_code: str
    branch: str
    invoice_document: str
    invoice_series: str
    supplier_code: str
    supplier_store: str
    supplier_name: str
    freight_document: str
    freight_series: str
    carrier_name: str
    goods_value: Decimal | None
    freight_gross_value: Decimal | None

    @property
    def invoice_key(self) -> tuple[str, ...]:
        return (
            self.branch,
            self.invoice_document,
            self.invoice_series,
            self.supplier_code,
            self.supplier_store,
        )


@dataclass
class FreightAllocationResult:
    invoices: list[FreightInvoice] = field(default_factory=list)
    inconsistencies: list[FreightInconsistency] = field(default_factory=list)


class FreightAllocationService:
    """Converte vínculos brutos em NFs com frete rateado e percentual."""

    def allocate(
        self,
        links: Iterable[FreightLink],
        *,
        branch_limits: Mapping[str, Decimal],
        special_freight_kinds: Sequence[str] = (),
        normal_freight_type: str = "N",
        normal_freight_kind: str = "CTE",
    ) -> FreightAllocationResult:
        result = FreightAllocationResult()
        unique_links = self._deduplicate(list(links), result)
        special = {str(kind).strip().upper() for kind in special_freight_kinds}

        allocations_by_invoice: dict[tuple[str, ...], list[FreightAllocation]] = {}
        for freight_links in self._group_by_freight(unique_links).values():
            self._allocate_freight_document(
                freight_links,
                special_freight_kinds=special,
                normal_freight_type=str(normal_freight_type).strip().upper(),
                normal_freight_kind=str(normal_freight_kind).strip().upper(),
                allocations_by_invoice=allocations_by_invoice,
                result=result,
            )

        self._build_invoices(
            unique_links,
            allocations_by_invoice=allocations_by_invoice,
            branch_limits=branch_limits,
            result=result,
        )
        return result

    # ------------------------------------------------------------- deduplicação

    def _deduplicate(
        self,
        links: list[FreightLink],
        result: FreightAllocationResult,
    ) -> list[FreightLink]:
        seen: set[tuple] = set()
        unique: list[FreightLink] = []
        for link in links:
            if link.link_key in seen:
                result.inconsistencies.append(
                    self._inconsistency(link, REASON_DUPLICATED_LINK)
                )
                continue
            seen.add(link.link_key)
            unique.append(link)
        return unique

    @staticmethod
    def _group_by_freight(
        links: Sequence[FreightLink],
    ) -> dict[tuple[str, ...], list[FreightLink]]:
        grouped: dict[tuple[str, ...], list[FreightLink]] = {}
        for link in links:
            grouped.setdefault(link.freight_key, []).append(link)
        return grouped

    # ------------------------------------------------------------------ rateio

    def _allocate_freight_document(
        self,
        links: list[FreightLink],
        *,
        special_freight_kinds: set[str],
        normal_freight_type: str,
        normal_freight_kind: str,
        allocations_by_invoice: dict[tuple[str, ...], list[FreightAllocation]],
        result: FreightAllocationResult,
    ) -> None:
        blocking = self._blocking_reason(
            links,
            special_freight_kinds=special_freight_kinds,
            normal_freight_type=normal_freight_type,
            normal_freight_kind=normal_freight_kind,
        )
        for link in links:
            if not link.invoice_found:
                result.inconsistencies.append(
                    self._inconsistency(link, REASON_NF_NOT_FOUND)
                )
            elif (link.goods_value or _ZERO) <= _ZERO:
                result.inconsistencies.append(
                    self._inconsistency(link, REASON_NF_GOODS_VALUE_NOT_POSITIVE)
                )

        if blocking is not None:
            for link in links:
                result.inconsistencies.append(self._inconsistency(link, blocking))
            return

        base = self._allocation_base(links)
        gross = links[0].freight_gross_value or _ZERO
        payable = [link for link in links if link.has_usable_goods_value]
        linked_invoice_count = len({link.invoice_key for link in payable})

        shares: dict[tuple[str, ...], Decimal] = {}
        for link in payable:
            share = ((gross * (link.goods_value or _ZERO)) / base).quantize(
                _CENTS, rounding=ROUND_HALF_UP
            )
            shares[link.invoice_key] = share

        self._apply_residual(shares, gross=gross, payable=payable)

        for link in payable:
            allocations_by_invoice.setdefault(link.invoice_key, []).append(
                FreightAllocation(
                    freight_document=link.freight_document,
                    freight_series=link.freight_series,
                    carrier_code=link.carrier_code,
                    carrier_store=link.carrier_store,
                    carrier_name=link.carrier_name,
                    freight_issue_date=link.freight_issue_date,
                    freight_gross_value=gross,
                    allocation_base=base,
                    allocated_value=shares[link.invoice_key],
                    linked_invoice_count=linked_invoice_count,
                )
            )

    def _blocking_reason(
        self,
        links: Sequence[FreightLink],
        *,
        special_freight_kinds: set[str],
        normal_freight_type: str,
        normal_freight_kind: str,
    ) -> str | None:
        """Motivo que impede ratear o CT-e inteiro, na ordem em que importa."""
        sample = links[0]
        if not sample.freight_found:
            return REASON_CTE_NOT_FOUND
        if (sample.freight_gross_value or _ZERO) <= _ZERO:
            return REASON_CTE_GROSS_VALUE_NOT_POSITIVE

        kind = sample.freight_document_kind.strip().upper()
        document_type = sample.freight_document_type.strip().upper()
        if kind in special_freight_kinds or kind != normal_freight_kind:
            return REASON_SPECIAL_OR_UNKNOWN_CTE
        if document_type != normal_freight_type:
            return REASON_SPECIAL_OR_UNKNOWN_CTE

        if self._allocation_base(links) <= _ZERO:
            return REASON_CTE_WITHOUT_VALID_BASE
        return None

    @staticmethod
    def _allocation_base(links: Sequence[FreightLink]) -> Decimal:
        """Soma a mercadoria das NFs distintas do CT-e — o fecho da base.

        Inclui NFs fora do filtro do usuário: ignorá-las inflaria o rateio das
        NFs visíveis e o percentual de frete apareceria maior do que é.
        """
        by_invoice: dict[tuple[str, ...], Decimal] = {}
        for link in links:
            if link.has_usable_goods_value:
                by_invoice[link.invoice_key] = link.goods_value or _ZERO
        return sum(by_invoice.values(), _ZERO)

    @staticmethod
    def _apply_residual(
        shares: dict[tuple[str, ...], Decimal],
        *,
        gross: Decimal,
        payable: Sequence[FreightLink],
    ) -> None:
        """Fecha a soma dos rateios no valor bruto do CT-e.

        O arredondamento de cada parcela deixa centavos sobrando ou faltando; o
        resto vai para a NF de maior mercadoria, onde tem menor peso relativo.
        """
        if not shares:
            return
        residual = gross - sum(shares.values(), _ZERO)
        if residual == _ZERO:
            return

        anchor = max(
            payable,
            key=lambda link: ((link.goods_value or _ZERO), link.invoice_key),
        )
        shares[anchor.invoice_key] += residual

    # ------------------------------------------------------------ consolidação

    def _build_invoices(
        self,
        links: Sequence[FreightLink],
        *,
        allocations_by_invoice: dict[tuple[str, ...], list[FreightAllocation]],
        branch_limits: Mapping[str, Decimal],
        result: FreightAllocationResult,
    ) -> None:
        grouped: dict[tuple[str, ...], list[FreightLink]] = {}
        for link in links:
            if link.invoice_found:
                grouped.setdefault(link.invoice_key, []).append(link)

        reasons_by_invoice = self._reasons_by_invoice(result)

        for invoice_key, invoice_links in grouped.items():
            if not any(link.in_filter for link in invoice_links):
                continue

            sample = invoice_links[0]
            goods_value = sample.goods_value or _ZERO
            allocations = tuple(allocations_by_invoice.get(invoice_key, ()))
            freight_total = sum(
                (item.allocated_value for item in allocations), _ZERO
            )
            limit = branch_limits.get(sample.branch)
            reasons = set(reasons_by_invoice.get(invoice_key, ()))

            if limit is None:
                reasons.add(REASON_BRANCH_WITHOUT_LIMIT)
                result.inconsistencies.append(
                    self._inconsistency(sample, REASON_BRANCH_WITHOUT_LIMIT)
                )

            percent = self._percent(freight_total, goods_value)
            result.invoices.append(
                FreightInvoice(
                    branch=sample.branch,
                    invoice_document=sample.invoice_document,
                    invoice_series=sample.invoice_series,
                    supplier_code=sample.supplier_code,
                    supplier_store=sample.supplier_store,
                    supplier_name=sample.supplier_name,
                    issue_date=sample.invoice_issue_date,
                    entry_date=sample.invoice_entry_date,
                    goods_value=goods_value,
                    freight_total=freight_total,
                    freight_percent=percent,
                    freight_limit=limit,
                    situation=self._situation(percent, limit, reasons),
                    allocations=allocations,
                    reason_codes=tuple(sorted(reasons)),
                )
            )

    @staticmethod
    def _reasons_by_invoice(
        result: FreightAllocationResult,
    ) -> dict[tuple[str, ...], set[str]]:
        reasons: dict[tuple[str, ...], set[str]] = {}
        for item in result.inconsistencies:
            reasons.setdefault(item.invoice_key, set()).add(item.reason_code)
        return reasons

    @staticmethod
    def _percent(freight_total: Decimal, goods_value: Decimal) -> Decimal | None:
        """``None`` quando não há mercadoria — percentual sobre zero não existe."""
        if goods_value <= _ZERO:
            return None
        return ((freight_total / goods_value) * Decimal("100")).quantize(
            _CENTS, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def _situation(
        percent: Decimal | None,
        limit: Decimal | None,
        reasons: set[str],
    ) -> str:
        """Compara o percentual já arredondado, o mesmo que a tela exibe.

        Uma NF de 3,251% mostra 3,25% e fica como normal: destacar um número
        igual ao limite na tela seria lido como erro pelo usuário.
        """
        if reasons:
            return SITUATION_INCONSISTENT
        if percent is None or limit is None:
            return SITUATION_INCONSISTENT
        return SITUATION_ABOVE_LIMIT if percent > limit else SITUATION_NORMAL

    @staticmethod
    def _inconsistency(link: FreightLink, reason_code: str) -> FreightInconsistency:
        return FreightInconsistency(
            reason_code=reason_code,
            branch=link.branch,
            invoice_document=link.invoice_document,
            invoice_series=link.invoice_series,
            supplier_code=link.supplier_code,
            supplier_store=link.supplier_store,
            supplier_name=link.supplier_name,
            freight_document=link.freight_document,
            freight_series=link.freight_series,
            carrier_name=link.carrier_name,
            goods_value=link.goods_value,
            freight_gross_value=link.freight_gross_value,
        )
