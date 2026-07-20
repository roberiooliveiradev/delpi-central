"""Enums e Query canônicos para OpenAPI — fonte única (não inventar no gerador TV)."""

from __future__ import annotations

from fastapi import Query

GRANULARITY_VALUES = ("day", "week", "month", "year")
SORT_DIR_VALUES = ("asc", "desc")
CUSTOMER_SEGMENT_VALUES = ("weg", "new_business")
PRODUCT_TYPE_VALUES = ("PA", "PI")
LOSS_TYPE_VALUES = ("refugo", "scrap", "both")
STOCK_METHOD_VALUES = ("auto", "hybrid", "estimated", "official_closure")
NONCONFORMITY_TYPE_VALUES = ("internal", "external", "all")

GRANULARITY_QUERY_REQUIRED = Query(
    ...,
    description="Series bucket size.",
    enum=list(GRANULARITY_VALUES),
)
GRANULARITY_QUERY_MONTH = Query(
    "month",
    description="Series bucket size.",
    enum=list(GRANULARITY_VALUES),
)
SORT_DIR_QUERY = Query(
    "asc",
    description="Sort direction: asc or desc.",
    enum=list(SORT_DIR_VALUES),
)
SORT_DIR_QUERY_DESC = Query(
    "desc",
    description="Sort direction: asc or desc.",
    enum=list(SORT_DIR_VALUES),
)
CUSTOMER_SEGMENT_QUERY = Query(
    None,
    description="Customer segment: weg or new_business.",
    enum=list(CUSTOMER_SEGMENT_VALUES),
)
PRODUCT_TYPE_QUERY = Query(
    None,
    description="Product type: PA or PI.",
    enum=list(PRODUCT_TYPE_VALUES),
)
LOSS_TYPE_QUERY = Query(
    "both",
    description="Loss type filter.",
    enum=list(LOSS_TYPE_VALUES),
)
STOCK_METHOD_QUERY = Query(
    "auto",
    description="Historical stock method: auto, hybrid, estimated or official_closure.",
    enum=list(STOCK_METHOD_VALUES),
)
NONCONFORMITY_TYPE_QUERY = Query(
    "all",
    description="Nonconformity type filter.",
    enum=list(NONCONFORMITY_TYPE_VALUES),
)
