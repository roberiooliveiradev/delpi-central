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
AUDIT_5S_STATUS_VALUES = ("open", "in_progress", "closed", "cancelled")
AUDIT_5S_LIFECYCLE_STATUS_VALUES = (
    "draft",
    "evaluation_complete",
    "nc_in_progress",
    "closed",
    "closed_without_nc_treatment",
)
AUDIT_5S_NC_SORT_VALUES = (
    "due_date_asc",
    "due_date_desc",
    "created_desc",
    "priority_desc",
)
PRIORITY_VALUES = ("high", "medium", "low")
SCHEDULING_BRANCH_VALUES = ("ES", "SC")
SCHEDULING_SCOPE_VALUES = ("occurrence", "future", "all")
SCHEDULING_RESOURCE_TYPE_VALUES = (
    "meeting_room",
    "training_room",
    "company_car",
    "other",
)
SCHEDULING_RECURRENCE_VALUES = ("weekly", "monthly")
GRANULARITY_DAY_WEEK_MONTH_VALUES = ("day", "week", "month")
GRANULARITY_DAY_MONTH_AUTO_VALUES = ("day", "month", "auto")
INSPECTION_RESULT_VALUES = ("A", "R", "T")
KAIZEN_STATUS_VALUES = (
    "recebido",
    "aprovado",
    "implantado",
    "descontinuado",
    "cancelado",
)
KAIZEN_SAVINGS_TYPE_VALUES = (
    "tempo",
    "material",
    "financeiro",
    "qualitativo",
    "misto",
)
KAIZEN_ROLE_VALUES = ("responsavel", "participante", "apoio")
KAIZEN_EVIDENCE_STAGE_VALUES = ("antes", "depois", "geral")
PAC_EVIDENCE_SECTION_VALUES = (
    "general",
    "nc_description",
    "containment",
    "root_cause",
    "corrective",
    "effectiveness",
    "preventive",
    "documentation",
    "attachments",
)
PAC_EVIDENCE_TYPE_VALUES = (
    "email",
    "message",
    "spreadsheet",
    "pdf",
    "image",
    "manual_text",
    "system_reference",
    "other",
)
PAC_AREA_VALUES = ("comercial", "qualidade", "pcp", "engenharia", "outro")
REFUGOS_DIMENSION_VALUES = (
    "motivo",
    "materia_prima",
    "produto_acabado",
    "centro_trabalho",
    "colaborador",
)
RETRABALHO_ORDER_BY_RANKING_VALUES = ("horas", "custo")
RETRABALHO_ORDER_BY_DETALHES_VALUES = ("data", "horas", "custo")
PRODUCTION_APPOINTMENTS_GROUP_BY_VALUES = ("day", "day_work_center")
CONSUMPTION_TOP_ITEMS_GROUP_BY_VALUES = (
    "general",
    "branch",
    "product_group",
    "unit",
    "branch_summary",
)
SAFETY_STOCK_STATUS_VALUES = (
    "without_safety_stock",
    "below_safety_stock",
    "at_safety_stock",
    "above_safety_stock",
)
INADIMPLENCIA_STATUS_VALUES = ("all", "on_time", "late")
COMMERCIAL_PROPOSAL_STATUS_VALUES = ("won", "open")
COMMERCIAL_OTD_STATUS_VALUES = ("on_time", "late")
LMP_LISTING_TYPE_VALUES = ("Todos", "LMP", "Amostra", "Outro")
LMP_DASHBOARD_STATUS_VALUES = (
    "Todos",
    "Pontual",
    "Atrasado",
    "Andamento",
    "Retornada",
)
PRODUCT_EXCLUSIVITY_VIEW_VALUES = ("by_material", "by_finished_product")
PRODUCT_DETAIL_VIEW_VALUES = ("full", "summary")


PRODUCTION_OTD_STATUS_VALUES = ("on_time", "late")
PRODUCTION_OEE_STATUS_VALUES = ("valid", "outlier")
NONCONFORMITY_QI2_STATUS_VALUES = ("1", "2", "3", "4", "5")
GUIAS_PROCEDURE_STATUS_VALUES = ("draft", "published", "archived")
QUALITY_LABEL_RESULT_VALUES = ("approved", "rejected", "conditional")

PAC_PLAN_STATUS_VALUES = (
    "draft",
    "triage",
    "containment",
    "root_cause_analysis",
    "action_plan_defined",
    "in_progress",
    "waiting_validation",
    "completed",
    "cancelled",
)

def GRANULARITY_QUERY_REQUIRED():
    return Query(
    ...,
    description="Series bucket size.",
    enum=list(GRANULARITY_VALUES),
)
def GRANULARITY_QUERY_MONTH():
    return Query(
    "month",
    description="Series bucket size.",
    enum=list(GRANULARITY_VALUES),
)
def SORT_DIR_QUERY():
    return Query(
    "asc",
    description="Sort direction: asc or desc.",
    enum=list(SORT_DIR_VALUES),
)
def SORT_DIR_QUERY_DESC():
    return Query(
    "desc",
    description="Sort direction: asc or desc.",
    enum=list(SORT_DIR_VALUES),
)
def SORT_DIR_QUERY_OPTIONAL():
    return Query(
    None,
    description="Sort direction: asc or desc.",
    enum=list(SORT_DIR_VALUES),
)
def SORT_DIR_QUERY_ALIAS_SORT_DIRECTION():
    return Query(
    "asc",
    alias="sortDirection",
    description="Sort direction: asc or desc.",
    enum=list(SORT_DIR_VALUES),
)
def SORT_DIR_QUERY_ALIAS_ORDER_DIR():
    return Query(
    "asc",
    alias="orderDir",
    description="Sort direction: asc or desc.",
    enum=list(SORT_DIR_VALUES),
)
def SORT_DIR_QUERY_ALIAS_ORDER_DIR_DESC():
    return Query(
    "desc",
    alias="orderDir",
    description="Sort direction: asc or desc.",
    enum=list(SORT_DIR_VALUES),
)
def CUSTOMER_SEGMENT_QUERY():
    return Query(
    None,
    description="Customer segment: weg or new_business.",
    enum=list(CUSTOMER_SEGMENT_VALUES),
)
def PRODUCT_TYPE_QUERY():
    return Query(
    None,
    description="Product type: PA or PI.",
    enum=list(PRODUCT_TYPE_VALUES),
)
def LOSS_TYPE_QUERY():
    return Query(
    "both",
    description="Loss type filter.",
    enum=list(LOSS_TYPE_VALUES),
)
def STOCK_METHOD_QUERY():
    return Query(
    "auto",
    description="Historical stock method: auto, hybrid, estimated or official_closure.",
    enum=list(STOCK_METHOD_VALUES),
)
def NONCONFORMITY_TYPE_QUERY():
    return Query(
    "all",
    description="Nonconformity type filter.",
    enum=list(NONCONFORMITY_TYPE_VALUES),
)
def NONCONFORMITY_SCOPE_QUERY():
    return Query(
    None,
    description="Nonconformity scope: internal or external.",
    enum=list(NONCONFORMITY_SCOPE_VALUES),
)
def BRANCH_QUERY_REQUIRED():
    return Query(
    ...,
    description="Protheus branch code (01 or 02).",
    enum=list(BRANCH_CODE_VALUES),
)
def BRANCH_QUERY_OPTIONAL():
    return Query(
    None,
    description="Protheus branch code (01 or 02). Empty uses consolidated scope when allowed.",
    enum=list(BRANCH_CODE_VALUES),
)
def SEVERITY_QUERY():
    return Query(
    None,
    description="Severity: low, medium, high or critical.",
    enum=list(SEVERITY_VALUES),
)
def SHIFT_5S_QUERY():
    return Query(
    None,
    description="5S shift: TURNO_1, TURNO_2, TURNO_3 or ADMINISTRATIVO.",
    enum=list(SHIFT_5S_VALUES),
)
def AUDIT_5S_STATUS_QUERY():
    return Query(
    None,
    description="5S audit status: open, in_progress, closed or cancelled.",
    enum=list(AUDIT_5S_STATUS_VALUES),
)
def AUDIT_5S_LIFECYCLE_STATUS_QUERY():
    return Query(
    None,
    alias="audit_status",
    description="5S audit lifecycle status.",
    enum=list(AUDIT_5S_LIFECYCLE_STATUS_VALUES),
)
def AUDIT_5S_LIFECYCLE_STATUS_QUERY_PLAIN():
    return Query(
    None,
    description="5S audit lifecycle status.",
    enum=list(AUDIT_5S_LIFECYCLE_STATUS_VALUES),
)
def AUDIT_5S_NC_SORT_QUERY():
    return Query(
    "due_date_asc",
    description="NC board sort: due_date_asc, due_date_desc, created_desc or priority_desc.",
    enum=list(AUDIT_5S_NC_SORT_VALUES),
)
def PRIORITY_QUERY():
    return Query(
    None,
    description="Priority: high, medium or low.",
    enum=list(PRIORITY_VALUES),
)
def SCHEDULING_BRANCH_QUERY():
    return Query(
    ...,
    description="Scheduling branch: ES or SC.",
    enum=list(SCHEDULING_BRANCH_VALUES),
)
def SCHEDULING_SCOPE_QUERY():
    return Query(
    "occurrence",
    description="Scheduling scope: occurrence, future or all.",
    enum=list(SCHEDULING_SCOPE_VALUES),
)
def GRANULARITY_QUERY_MONTH_DWM():
    return Query(
    "month",
    description="Series bucket size: day, week or month.",
    enum=list(GRANULARITY_DAY_WEEK_MONTH_VALUES),
)
def GRANULARITY_QUERY_DAY_MONTH_AUTO():
    return Query(
    "auto",
    alias="granularity",
    description="Series bucket size: day, month or auto.",
    enum=list(GRANULARITY_DAY_MONTH_AUTO_VALUES),
)
def INSPECTION_RESULT_QUERY():
    return Query(
    None,
    description="Inspection result: A (approved), R (rejected) or T (pending).",
    enum=list(INSPECTION_RESULT_VALUES),
)
def KAIZEN_STATUS_QUERY():
    return Query(
    None,
    description="Kaizen status: recebido, aprovado, implantado, descontinuado or cancelado.",
    enum=list(KAIZEN_STATUS_VALUES),
)
def KAIZEN_SAVINGS_TYPE_QUERY():
    return Query(
    None,
    description="Kaizen savings type: tempo, material, financeiro, qualitativo or misto.",
    enum=list(KAIZEN_SAVINGS_TYPE_VALUES),
)
def PAC_EVIDENCE_SECTION_QUERY():
    return Query(
    None,
    description="PAC evidence section.",
    enum=list(PAC_EVIDENCE_SECTION_VALUES),
)
def PAC_EVIDENCE_TYPE_QUERY():
    return Query(
    None,
    description="PAC evidence type.",
    enum=list(PAC_EVIDENCE_TYPE_VALUES),
)
def REFUGOS_DIMENSION_QUERY():
    return Query(
    ...,
    description="Refugos ranking dimension.",
    enum=list(REFUGOS_DIMENSION_VALUES),
)
def RETRABALHO_ORDER_BY_RANKING_QUERY():
    return Query(
    "horas",
    alias="orderBy",
    description="Retrabalho ranking sort: horas or custo.",
    enum=list(RETRABALHO_ORDER_BY_RANKING_VALUES),
)
def RETRABALHO_ORDER_BY_DETALHES_QUERY():
    return Query(
    "data",
    alias="orderBy",
    description="Retrabalho details sort: data, horas or custo.",
    enum=list(RETRABALHO_ORDER_BY_DETALHES_VALUES),
)
def PRODUCTION_APPOINTMENTS_GROUP_BY_QUERY():
    return Query(
    "day",
    description="Group appointments by day or day_work_center.",
    enum=list(PRODUCTION_APPOINTMENTS_GROUP_BY_VALUES),
)
def CONSUMPTION_TOP_ITEMS_GROUP_BY_QUERY():
    return Query(
    "general",
    description="Consumption ranking group_by dimension.",
    enum=list(CONSUMPTION_TOP_ITEMS_GROUP_BY_VALUES),
)
def SAFETY_STOCK_STATUS_QUERY():
    return Query(
    None,
    description=(
        "Safety stock status: without_safety_stock, below_safety_stock, "
        "at_safety_stock or above_safety_stock."
    ),
    enum=list(SAFETY_STOCK_STATUS_VALUES),
)
def INADIMPLENCIA_STATUS_QUERY():
    return Query(
    "all",
    description="Delay status filter: all, on_time or late.",
    enum=list(INADIMPLENCIA_STATUS_VALUES),
)
def COMMERCIAL_PROPOSAL_STATUS_QUERY():
    return Query(
    None,
    description="Proposal status: won (won deals), open (others) or omit for all.",
    enum=list(COMMERCIAL_PROPOSAL_STATUS_VALUES),
)
def COMMERCIAL_OTD_STATUS_QUERY():
    return Query(
    None,
    description="OTD status filter: on_time or late.",
    enum=list(COMMERCIAL_OTD_STATUS_VALUES),
)
def LMP_LISTING_TYPE_QUERY():
    return Query(
    None,
    description="LMP listing type: Todos, LMP, Amostra or Outro.",
    enum=list(LMP_LISTING_TYPE_VALUES),
)
def LMP_DASHBOARD_STATUS_QUERY():
    return Query(
    "Todos",
    description="LMP dashboard status: Todos, Pontual, Atrasado, Andamento or Retornada.",
    enum=list(LMP_DASHBOARD_STATUS_VALUES),
)
def LMP_DASHBOARD_STATUS_QUERY_OPTIONAL():
    return Query(
    None,
    description="LMP dashboard status: Todos, Pontual, Atrasado, Andamento or Retornada.",
    enum=list(LMP_DASHBOARD_STATUS_VALUES),
)
def PRODUCT_EXCLUSIVITY_VIEW_QUERY():
    return Query(
    "by_material",
    description="by_material=exclusive MPs; by_finished_product=PAs with exclusive MP.",
    enum=list(PRODUCT_EXCLUSIVITY_VIEW_VALUES),
)
def PRODUCT_DETAIL_VIEW_QUERY():
    return Query(
    "full",
    description="full=complete payload; summary=lighter subset.",
    enum=list(PRODUCT_DETAIL_VIEW_VALUES),
)

def PRODUCTION_OTD_STATUS_QUERY():
    return Query(
    None,
    description="OTD status filter: on_time or late.",
    enum=list(PRODUCTION_OTD_STATUS_VALUES),
)
def PRODUCTION_OEE_STATUS_QUERY():
    return Query(
    None,
    description="OEE list status filter: valid or outlier.",
    enum=list(PRODUCTION_OEE_STATUS_VALUES),
)
def NONCONFORMITY_QI2_STATUS_QUERY():
    return Query(
    None,
    description="QI2 status code: 1=Registrada, 2=Em análise, 3=Procede, 4=Não procede, 5=Cancelada.",
    enum=list(NONCONFORMITY_QI2_STATUS_VALUES),
)
def GUIAS_PROCEDURE_STATUS_QUERY():
    return Query(
    None,
    description="Procedure status: draft, published or archived.",
    enum=list(GUIAS_PROCEDURE_STATUS_VALUES),
)
def PAC_PLAN_STATUS_QUERY():
    return Query(
    None,
    description="PAC plan status.",
    enum=list(PAC_PLAN_STATUS_VALUES),
)
