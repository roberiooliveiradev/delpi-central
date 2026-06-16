from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


IdentifierType = Literal["delpi_code", "customer_reference"]


@dataclass(frozen=True, slots=True)
class ResolvedProductIdentifier:
    identifier: str
    identifier_type: IdentifierType
    product_code: str
    customer_reference: str | None
    description: str | None
    product_type: str | None
    unit: str | None
    group_code: str | None


class ProductIdentifierResolutionService:
    DELPI_PA_PREFIX = "9026"

    @classmethod
    def looks_like_delpi_pa_code(cls, identifier: str) -> bool:
        cleaned = cls.normalize_identifier(identifier)
        return bool(re.fullmatch(rf"{cls.DELPI_PA_PREFIX}\d{{4,}}", cleaned))

    @classmethod
    def normalize_identifier(cls, identifier: str | None) -> str:
        return re.sub(r"\D", "", str(identifier or "").strip())

    @classmethod
    def resolve(
        cls,
        identifier: str | None,
        *,
        by_code: dict | None,
        by_customer_reference: dict | None,
    ) -> ResolvedProductIdentifier | None:
        cleaned = cls.normalize_identifier(identifier)

        if not cleaned:
            return None

        if cls.looks_like_delpi_pa_code(cleaned) and by_code:
            return cls._from_row(
                cleaned,
                by_code,
                identifier_type="delpi_code",
            )

        if by_customer_reference:
            return cls._from_row(
                cleaned,
                by_customer_reference,
                identifier_type="customer_reference",
            )

        if by_code:
            return cls._from_row(
                cleaned,
                by_code,
                identifier_type="delpi_code",
            )

        return None

    @classmethod
    def _from_row(
        cls,
        identifier: str,
        row: dict,
        *,
        identifier_type: IdentifierType,
    ) -> ResolvedProductIdentifier:
        customer_reference = cls._trim(row.get("customer_reference"))

        return ResolvedProductIdentifier(
            identifier=identifier,
            identifier_type=identifier_type,
            product_code=str(row.get("product_code") or row.get("code") or "").strip(),
            customer_reference=customer_reference or None,
            description=cls._trim(row.get("description")),
            product_type=cls._trim(row.get("product_type") or row.get("type")),
            unit=cls._trim(row.get("unit")),
            group_code=cls._trim(row.get("group_code")),
        )

    @staticmethod
    def _trim(value) -> str | None:
        if value in (None, ""):
            return None

        return str(value).strip() or None
