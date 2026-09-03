from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerAssignmentBody(BaseModel):
    customer_code: str = Field(..., min_length=1)
    customer_store: str = Field(..., min_length=1)
    customer_name: str | None = None


class CreatePortfolioBody(BaseModel):
    """Name-first: `display_name` sozinho cria carteira órfã (V013 / ManageSellerPortfolio)."""

    user_id: str | None = Field(default=None, min_length=1)
    display_name: str = Field(..., min_length=1)
    customers: list[CustomerAssignmentBody] = Field(default_factory=list)
    user_ids: list[str] = Field(default_factory=list)
    owner_user_id: str | None = None


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
    nature: str | None = Field(
        default=None,
        pattern=r"^(gross|net)$",
        description="Natureza do faturamento: gross (NF) ou net (ROL). Default gross.",
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
    nature: str | None = Field(
        default=None,
        pattern=r"^(gross|net)$",
        description="Natureza do faturamento: gross (NF) ou net (ROL). Default gross.",
    )
    product_codes: list[str] | None = Field(
        default=None,
        description="Códigos de produto (D2_COD).",
    )
    product_groups: list[str] | None = Field(
        default=None,
        description="Famílias Protheus (B1_GRUPO).",
    )
    market: str | None = Field(
        default=None,
        pattern=r"^(domestic|export)$",
        description="Mercado: domestic (CFOP 5/6) ou export (CFOP 7).",
    )


class CustomerCoverageLookupBody(BaseModel):
    """Lookup batch de cobertura compartilhada (E6.4)."""

    customers: list[CustomerAssignmentBody] = Field(
        default_factory=list,
        max_length=200,
    )
    portfolio_ids: list[str] = Field(default_factory=list, max_length=200)
