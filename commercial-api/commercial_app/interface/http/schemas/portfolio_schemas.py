from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class CustomerAssignmentBody(BaseModel):
    customer_code: str = Field(..., min_length=1)
    customer_store: str = Field(..., min_length=1)
    customer_name: str | None = None


class CreatePortfolioBody(BaseModel):
    user_id: str | None = Field(default=None, min_length=1)
    display_name: str = Field(..., min_length=1)
    customers: list[CustomerAssignmentBody] = Field(default_factory=list)
    user_ids: list[str] = Field(default_factory=list)
    owner_user_id: str | None = None

    @model_validator(mode="after")
    def require_user_id_or_user_ids(self) -> CreatePortfolioBody:
        ids = [uid.strip() for uid in self.user_ids if uid and str(uid).strip()]
        if ids:
            return self
        if not (self.user_id and self.user_id.strip()):
            raise ValueError("Informe user_id ou user_ids.")
        return self


class UpdatePortfolioBody(BaseModel):
    display_name: str | None = None
    active: bool | None = None


class ReplaceCustomersBody(BaseModel):
    customers: list[CustomerAssignmentBody] = Field(default_factory=list)


class AddCustomerBody(BaseModel):
    customer_code: str = Field(..., min_length=1)
    customer_store: str = Field(..., min_length=1)
    customer_name: str | None = None


class MemberBody(BaseModel):
    user_id: str = Field(..., min_length=1)
    role: str = Field(default="member")


class ReplaceMembersBody(BaseModel):
    members: list[MemberBody] = Field(default_factory=list)


class AddMemberBody(BaseModel):
    user_id: str = Field(..., min_length=1)
    role: str = Field(default="member")


class SetOwnerBody(BaseModel):
    user_id: str = Field(..., min_length=1)


class TransferCustomersBody(BaseModel):
    source_portfolio_id: str = Field(..., min_length=1)
    target_portfolio_id: str = Field(..., min_length=1)
    customers: list[CustomerAssignmentBody] = Field(default_factory=list)
    reason_note: str = Field(..., min_length=1)


class TransferCustomersBulkBody(BaseModel):
    """Transferência em massa best-effort (E6.5) — resultado por cliente."""

    source_portfolio_id: str = Field(..., min_length=1)
    target_portfolio_id: str = Field(..., min_length=1)
    customers: list[CustomerAssignmentBody] = Field(default_factory=list, max_length=500)
    reason_note: str = Field(..., min_length=1)


class EnrichmentBody(BaseModel):
    customers: list[CustomerAssignmentBody] = Field(
        default_factory=list,
        max_length=200,
    )
    window_days: int | None = Field(
        default=None,
        ge=1,
        le=365,
        description="Janela da tendência (dias); presets 7/30/90; default 30 no TOTVS.",
    )


class BillingSeriesBody(BaseModel):
    """Série de faturamento — aceita 1 cliente (Conta) ou subset multi-select da carteira."""

    customers: list[CustomerAssignmentBody] = Field(
        default_factory=list,
        max_length=200,
    )
    months: int = Field(default=12, ge=1, le=24)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    granularity: str | None = Field(
        default=None,
        pattern=r"^(day|week|month|year)$",
    )


class CustomerCoverageLookupBody(BaseModel):
    """Lookup batch de cobertura compartilhada (E6.4)."""

    customers: list[CustomerAssignmentBody] = Field(
        default_factory=list,
        max_length=200,
    )
    portfolio_ids: list[str] = Field(default_factory=list, max_length=200)
