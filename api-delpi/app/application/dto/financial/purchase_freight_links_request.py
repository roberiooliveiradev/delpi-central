from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PurchaseFreightLinksRequest:
    """Filtros de leitura dos vínculos NF de compra x CT-e.

    As datas são sempre da NF de compra (emissão e digitação são independentes).
    """

    branch: Optional[str] = None
    issue_start: Optional[str] = None
    issue_end: Optional[str] = None
    entry_start: Optional[str] = None
    entry_end: Optional[str] = None
    supplier: Optional[str] = None
    invoice_document: Optional[str] = None
    freight_document: Optional[str] = None
