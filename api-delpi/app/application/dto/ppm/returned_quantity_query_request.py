"""Request canônico — quantidade devolvida (QI2_QTDDEV, numerador PPM)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReturnedQuantityQueryRequest:
    type: str  # internal | external
    date_start: str
    date_end: str
    branch: str | None = None
    product_prefix: str | None = None

    @classmethod
    def create(
        cls,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
        branch: str | None = None,
        product_prefix: str | None = None,
    ) -> ReturnedQuantityQueryRequest:
        normalized_type = str(ppm_type or "").strip().lower()
        if normalized_type not in {"internal", "external"}:
            raise ValueError("type deve ser internal ou external")
        if not (date_start and str(date_start).strip()):
            raise ValueError("date_start é obrigatório.")
        if not (date_end and str(date_end).strip()):
            raise ValueError("date_end é obrigatório.")

        prefix = str(product_prefix).strip() if product_prefix else None
        return cls(
            type=normalized_type,
            date_start=str(date_start).strip(),
            date_end=str(date_end).strip(),
            branch=str(branch).strip() if branch else None,
            product_prefix=prefix or None,
        )
