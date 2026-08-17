from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.third_party_materials.constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    EXPORT_FORMAT_CSV,
    EXPORT_FORMAT_VALUES,
    MAX_PAGE_SIZE,
    VALID_SHIPMENT_STATUS,
    parse_ignored_products,
)
from app.config import settings
from app.domain.totvs.protheus_third_party_materials import API_TO_VIEW_SHIPMENT_STATUS
from app.infrastructure.persistence.totvs.pagination import paginate


@dataclass(frozen=True, slots=True)
class ThirdPartyMaterialsQueryRequest:
    branch: str
    product: str | None = None
    customer_reference: str | None = None
    partner_code: str | None = None
    partner_store: str | None = None
    receipt_number: str | None = None
    return_number: str | None = None
    issued_from: str | None = None
    issued_to: str | None = None
    status: str | None = None
    only_with_balance: bool = False
    include_test_products: bool = False
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    export_format: str = EXPORT_FORMAT_CSV

    @classmethod
    def from_query(
        cls,
        *,
        branch: str,
        product: str | None = None,
        customer_reference: str | None = None,
        partner_code: str | None = None,
        partner_store: str | None = None,
        receipt_number: str | None = None,
        return_number: str | None = None,
        issued_from: str | None = None,
        issued_to: str | None = None,
        status: str | None = None,
        only_with_balance: bool = False,
        include_test_products: bool = False,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        export_format: str = EXPORT_FORMAT_CSV,
    ) -> ThirdPartyMaterialsQueryRequest:
        normalized_branch = str(branch or "").strip()
        if not normalized_branch:
            raise ValueError("Filial é obrigatória.")

        normalized_status = str(status or "").strip().lower() or None
        if normalized_status and normalized_status not in VALID_SHIPMENT_STATUS:
            raise ValueError("Status inválido. Use completed, partial ou no_return.")

        normalized_format = str(export_format or EXPORT_FORMAT_CSV).strip().lower()
        if normalized_format not in EXPORT_FORMAT_VALUES:
            raise ValueError("Formato de exportação inválido. Use csv ou xlsx.")

        issued_from_iso = _optional_iso_date(issued_from, "issued_from")
        issued_to_iso = _optional_iso_date(issued_to, "issued_to")
        if issued_from_iso and issued_to_iso and issued_from_iso > issued_to_iso:
            raise ValueError("issued_from não pode ser posterior a issued_to.")

        paging = paginate(page, min(int(page_size or DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE))
        return cls(
            branch=normalized_branch,
            product=_optional_text(product),
            customer_reference=_optional_text(customer_reference),
            partner_code=_optional_text(partner_code),
            partner_store=_optional_text(partner_store),
            receipt_number=_optional_text(receipt_number),
            return_number=_optional_text(return_number),
            issued_from=issued_from_iso,
            issued_to=issued_to_iso,
            status=normalized_status,
            only_with_balance=bool(only_with_balance),
            include_test_products=bool(include_test_products),
            page=int(paging["page"]),
            page_size=int(paging["page_size"]),
            export_format=normalized_format,
        )

    def ignored_products(self) -> tuple[str, ...]:
        if self.include_test_products:
            return ()
        return parse_ignored_products(settings.THIRD_PARTY_MATERIALS_IGNORED_PRODUCTS)

    def view_status(self) -> str | None:
        if not self.status:
            return None
        return API_TO_VIEW_SHIPMENT_STATUS[self.status]

    def has_useful_filter(self) -> bool:
        return any(
            (
                self.product,
                self.customer_reference,
                self.partner_code,
                self.receipt_number,
                self.return_number,
                self.issued_from,
                self.issued_to,
                self.status,
                self.only_with_balance,
            )
        )


def _optional_text(value: str | None) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_iso_date(value: str | None, field_name: str) -> str | None:
    text = _optional_text(value)
    if not text:
        return None
    if len(text) == 8 and text.isdigit():
        text = f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    if len(text) < 10 or text[4] != "-" or text[7] != "-":
        raise ValueError(f"{field_name} deve estar em YYYY-MM-DD.")
    return text[:10]
