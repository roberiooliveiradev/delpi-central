from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerAssignmentBody(BaseModel):
    customer_code: str = Field(..., min_length=1)
    customer_store: str = Field(..., min_length=1)
    customer_name: str | None = None


class CreatePortfolioBody(BaseModel):
    user_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    customers: list[CustomerAssignmentBody] = Field(default_factory=list)


class UpdatePortfolioBody(BaseModel):
    display_name: str | None = None
    active: bool | None = None


class ReplaceCustomersBody(BaseModel):
    customers: list[CustomerAssignmentBody] = Field(default_factory=list)


class AddCustomerBody(BaseModel):
    customer_code: str = Field(..., min_length=1)
    customer_store: str = Field(..., min_length=1)
    customer_name: str | None = None


class TransferCustomersBody(BaseModel):
    source_portfolio_id: str = Field(..., min_length=1)
    target_portfolio_id: str = Field(..., min_length=1)
    customers: list[CustomerAssignmentBody] = Field(default_factory=list)
    reason_note: str = Field(..., min_length=1)


class EnrichmentBody(BaseModel):
    customers: list[CustomerAssignmentBody] = Field(
        default_factory=list,
        max_length=200,
    )
