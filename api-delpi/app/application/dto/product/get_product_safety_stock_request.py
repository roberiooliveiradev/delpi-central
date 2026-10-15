"""Request — consulta geral de estoque de segurança do produto (SBZ010)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_PRODUCT_TYPE_PATTERN = re.compile(r"^[A-Za-z0-9]{2}$")


@dataclass
class GetProductSafetyStockRequest:
    code: str
    branch: str | None = None
    product_type: str | None = None

    def __post_init__(self) -> None:
        self.code = str(self.code or "").strip()
        if not self.code:
            raise ValueError("product code é obrigatório.")

        if self.branch is not None:
            branch = str(self.branch).strip()
            self.branch = branch or None

        if self.product_type is not None:
            product_type = str(self.product_type).strip().upper()
            if not _PRODUCT_TYPE_PATTERN.fullmatch(product_type):
                raise ValueError(
                    "product_type inválido: use o código de 2 caracteres do tipo "
                    "Protheus (ex.: MP, PA, PI, MC, II)."
                )
            self.product_type = product_type
