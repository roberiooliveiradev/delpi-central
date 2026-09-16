# app/application/dto/list_product_stock_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductStockRequest:
    """Product stock page request.

    ``branch`` may arrive as wire scope (``all`` | ``01`` | ``02``). The use case
    canonicalizes via ``optional_concrete_branch`` before cache/repository:
    omit/``all`` → consolidated (no ``B2_FILIAL`` predicate); ``01``/``02`` → filter.
    """

    code: str
    page: int
    page_size: int

    branch: Optional[str] = None
    location: Optional[str] = None