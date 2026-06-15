from __future__ import annotations

from typing import Optional

from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import ListLMPRequest


def build_list_lmp_request(
    *,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    branch: Optional[str] = None,
    listing_type: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    include_qtd_pi: Optional[bool] = None,
) -> ListLMPRequest:
    return ListLMPRequest(
        date_start=date_start,
        date_end=date_end,
        branch=branch,
        listing_type=listing_type,
        page=page,
        page_size=page_size,
        include_qtd_pi=include_qtd_pi,
    )


def build_get_lmp_history_request(
    sale_number: str,
    *,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    branch: Optional[str] = None,
    revision: Optional[str] = None,
) -> GetLmpHistoryRequest:
    return GetLmpHistoryRequest(
        sale_number=sale_number,
        date_start=date_start,
        date_end=date_end,
        branch=branch,
        revision=revision,
    )


def build_get_lmp_request(
    sale_number: str,
    *,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    branch: Optional[str] = None,
) -> GetLMPRequest:
    return GetLMPRequest(
        sale_number=sale_number,
        date_start=date_start,
        date_end=date_end,
        branch=branch,
    )
