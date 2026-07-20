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
NONCONFORMITY_SCOPE_VALUES = ("internal", "external")
BRANCH_CODE_VALUES = ("01", "02")
SEVERITY_VALUES = ("low", "medium", "high", "critical")
SHIFT_5S_VALUES = ("TURNO_1", "TURNO_2", "TURNO_3", "ADMINISTRATIVO")
ACTIVE_BOOL_VALUES = ("true", "false")
YES_NO_VALUES = ("sim", "nao")

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
NONCONFORMITY_SCOPE_QUERY = Query(
    None,
    description="Nonconformity scope: internal or external.",
    enum=list(NONCONFORMITY_SCOPE_VALUES),
)
BRANCH_QUERY_REQUIRED = Query(
    ...,
    description="Protheus branch code (01 or 02).",
    enum=list(BRANCH_CODE_VALUES),
)
BRANCH_QUERY_OPTIONAL = Query(
    None,
    description="Protheus branch code (01 or 02). Empty uses consolidated scope when allowed.",
    enum=list(BRANCH_CODE_VALUES),
)
SEVERITY_QUERY = Query(
    None,
    description="Severity: low, medium, high or critical.",
    enum=list(SEVERITY_VALUES),
)
SHIFT_5S_QUERY = Query(
    None,
    description="5S shift: TURNO_1, TURNO_2, TURNO_3 or ADMINISTRATIVO.",
    enum=list(SHIFT_5S_VALUES),
)
AUDIT_5S_STATUS_VALUES = ("open", "in_progress", "closed", "cancelled")
PRIORITY_VALUES = ("high", "medium", "low")
SCHEDULING_BRANCH_VALUES = ("ES", "SC")
SCHEDULING_SCOPE_VALUES = ("occurrence", "future", "all")
GRANULARITY_DAY_WEEK_MONTH_VALUES = ("day", "week", "month")
INSPECTION_RESULT_VALUES = ("A", "R", "T")

AUDIT_5S_STATUS_QUERY = Query(
    None,
    description="5S audit status: open, in_progress, closed or cancelled.",
    enum=list(AUDIT_5S_STATUS_VALUES),
)
PRIORITY_QUERY = Query(
    None,
    description="Priority: high, medium or low.",
    enum=list(PRIORITY_VALUES),
)
SCHEDULING_BRANCH_QUERY = Query(
    ...,
    description="Scheduling branch: ES or SC.",
    enum=list(SCHEDULING_BRANCH_VALUES),
)
SCHEDULING_SCOPE_QUERY = Query(
    "occurrence",
    description="Scheduling scope: occurrence, future or all.",
    enum=list(SCHEDULING_SCOPE_VALUES),
)
GRANULARITY_QUERY_MONTH_DWM = Query(
    "month",
    description="Series bucket size: day, week or month.",
    enum=list(GRANULARITY_DAY_WEEK_MONTH_VALUES),
)
INSPECTION_RESULT_QUERY = Query(
    None,
    description="Inspection result: A (approved), R (rejected) or T (pending).",
    enum=list(INSPECTION_RESULT_VALUES),
)
