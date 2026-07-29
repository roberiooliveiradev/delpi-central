"""Request canônico — quantidade produzida (H6_QTDPROD, inspeção final + OP mãe)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.production.production_appointments.production_appointments_scope import (
    DEFAULT_PRODUCED_PRODUCT_TYPES,
    VALID_BRANCHES,
)


@dataclass(frozen=True, slots=True)
class ProducedQuantityQueryRequest:
    date_start: str
    date_end: str
    branch: str | None = None
    products: tuple[str, ...] = ()
    product_types: tuple[str, ...] = ()
    require_products: bool = False

    @classmethod
    def create(
        cls,
        *,
        date_start: str | None,
        date_end: str | None,
        branch: str | None = None,
        products: list[str] | None = None,
        product_types: list[str] | None = None,
        require_products: bool = False,
        require_branch: bool = False,
    ) -> ProducedQuantityQueryRequest:
        if not (date_start and str(date_start).strip()):
            raise ValueError("date_start é obrigatório.")
        if not (date_end and str(date_end).strip()):
            raise ValueError("date_end é obrigatório.")

        normalized_branch = str(branch).strip() if branch else None
        if require_branch:
            if not normalized_branch or normalized_branch not in VALID_BRANCHES:
                raise ValueError('branch inválida. Use "01" (SC) ou "02" (ES).')
        elif normalized_branch and normalized_branch not in VALID_BRANCHES:
            raise ValueError('branch inválida. Use "01" (SC) ou "02" (ES).')

        normalized_products: list[str] = []
        seen: set[str] = set()
        for raw in products or []:
            for part in str(raw or "").split(","):
                code = part.strip()
                if not code or code in seen:
                    continue
                seen.add(code)
                normalized_products.append(code)

        if require_products and not normalized_products:
            raise ValueError("Informe ao menos um código de produto em product.")

        tipos_raw = product_types
        if tipos_raw is None:
            tipos = tuple(sorted(DEFAULT_PRODUCED_PRODUCT_TYPES))
        else:
            tipos = tuple(
                sorted(
                    {
                        str(tipo).strip().upper()
                        for tipo in tipos_raw
                        if str(tipo).strip()
                    }
                )
            )
            if not tipos:
                raise ValueError("product_types não pode ser vazio.")

        return cls(
            date_start=str(date_start).strip(),
            date_end=str(date_end).strip(),
            branch=normalized_branch,
            products=tuple(normalized_products),
            product_types=tipos,
            require_products=require_products,
        )
