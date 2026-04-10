from pydantic import BaseModel, Field
from typing import List, Optional


class WeightItemSchema(BaseModel):
    department_id: str
    department_name: str
    weight_pct: int


class GoalItemSchema(BaseModel):
    department_id: str
    department_name: str
    headline_goal: str
    supporting_focus: str


class ParameterItemSchema(BaseModel):
    key: str
    label: str
    value: str


class GovernanceItemSchema(BaseModel):
    key: str
    label: str
    value: str
    observation: str


class WeightsPayloadSchema(BaseModel):
    items: List[WeightItemSchema] = Field(default_factory=list)


class GoalsPayloadSchema(BaseModel):
    items: List[GoalItemSchema] = Field(default_factory=list)


class ParametersPayloadSchema(BaseModel):
    items: List[ParameterItemSchema] = Field(default_factory=list)


class GovernancePayloadSchema(BaseModel):
    items: List[GovernanceItemSchema] = Field(default_factory=list)


class UpdateStrategicIndicatorsSettingsBodySchema(BaseModel):
    weights: WeightsPayloadSchema
    goals: GoalsPayloadSchema
    parameters: ParametersPayloadSchema
    governance: GovernancePayloadSchema


class CreateChangeRequestBody(BaseModel):
    title: str
    description: str
    target_block: str
    proposed_payload: dict


class AddCommentBody(BaseModel):
    comment_text: str


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