from pydantic import BaseModel, Field
from typing import List, Optional


# =========================================================
# SETTINGS GLOBAIS
# =========================================================

class ParameterItemSchema(BaseModel):
    key: str
    label: str
    value: str


class GovernanceItemSchema(BaseModel):
    key: str
    label: str
    value: str
    observation: str


class ParametersPayloadSchema(BaseModel):
    items: List[ParameterItemSchema] = Field(default_factory=list)


class GovernancePayloadSchema(BaseModel):
    items: List[GovernanceItemSchema] = Field(default_factory=list)


class UpdateStrategicIndicatorsSettingsBodySchema(BaseModel):
    parameters: ParametersPayloadSchema
    governance: GovernancePayloadSchema


# =========================================================
# CHANGE REQUESTS
# =========================================================

class CreateChangeRequestBody(BaseModel):
    title: str
    description: str
    target_block: str
    proposed_payload: dict


class AddCommentBody(BaseModel):
    comment_text: str


# =========================================================
# DEPARTAMENTOS ADMINISTRATIVOS
# =========================================================

class DepartmentAdminItemSchema(BaseModel):
    department_id: str
    department_name: str
    short_name: str
    strategic_summary: str = ""
    headline_goal: str = ""
    supporting_focus: str = ""
    weight_pct: float = 0
    aggregation_mode: str
    is_active: bool = True
    display_order: int = 0


class CreateDepartmentBodySchema(BaseModel):
    department_id: str
    department_name: str
    short_name: str
    strategic_summary: str = ""
    headline_goal: str = ""
    supporting_focus: str = ""
    weight_pct: float = 0
    aggregation_mode: str
    display_order: int = 0


class UpdateDepartmentBodySchema(BaseModel):
    department_name: str
    short_name: str
    strategic_summary: str = ""
    headline_goal: str = ""
    supporting_focus: str = ""
    weight_pct: float = 0
    aggregation_mode: str
    is_active: bool = True
    display_order: int = 0


# =========================================================
# INDICADORES ESTRUTURAIS
# =========================================================

class DepartmentIndicatorItemSchema(BaseModel):
    indicator_id: str
    indicator_name: str
    weight_pct: float
    scope_type: str
    strategic_description: str = ""
    source_key: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class CreateDepartmentIndicatorBodySchema(BaseModel):
    indicator_id: str
    indicator_name: str
    weight_pct: float
    scope_type: str
    strategic_description: str = ""
    source_key: Optional[str] = None
    display_order: int = 0


class UpdateDepartmentIndicatorBodySchema(BaseModel):
    indicator_name: str
    weight_pct: float
    scope_type: str
    strategic_description: str = ""
    source_key: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


# =========================================================
# METAS ANALÍTICAS UNITÁRIAS
# =========================================================

class CreateIndicatorGoalBodySchema(BaseModel):
    indicator_id: str
    goal_year: int
    goal_label: str
    goal_value: float
    goal_periodicity: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    notes: Optional[str] = None


class UpdateIndicatorGoalBodySchema(BaseModel):
    goal_label: str
    goal_value: float
    goal_periodicity: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    notes: Optional[str] = None


# =========================================================
# METAS ANALÍTICAS EM LOTE
# =========================================================

class BulkCreateIndicatorGoalItemSchema(BaseModel):
    indicator_id: str
    goal_label: str
    goal_value: float
    goal_periodicity: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    notes: Optional[str] = None


class BulkCreateIndicatorGoalsBodySchema(BaseModel):
    goal_year: int
    items: List[BulkCreateIndicatorGoalItemSchema] = Field(default_factory=list)


class DuplicateIndicatorGoalsYearBodySchema(BaseModel):
    source_year: int
    target_year: int
    department_ids: List[str] = Field(default_factory=list)
    overwrite_existing: bool = False


class FillMissingIndicatorGoalsBodySchema(BaseModel):
    goal_year: int
    department_ids: List[str] = Field(default_factory=list)
    copy_from_year: Optional[int] = None