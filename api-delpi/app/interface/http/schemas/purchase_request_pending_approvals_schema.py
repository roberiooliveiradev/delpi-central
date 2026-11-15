"""Additive internal polling contract; recipient identity is always a Protheus ID."""

from pydantic import BaseModel


class PendingApprover(BaseModel):
    code: str | None
    name: str | None
    protheus_user_id: str | None
    level: str | None


class PendingProduct(BaseModel):
    code: str
    description: str | None


class PendingRequest(BaseModel):
    branch: str
    request_number: str
    requester_protheus_user_id: str | None
    requester_name: str | None
    request_issue_date: str | None
    pending_approvers: list[PendingApprover]
    products: list[PendingProduct]


class PendingApprovalCursor(BaseModel):
    after_branch: str
    after_request_number: str


class PendingApprovalPage(BaseModel):
    items: list[PendingRequest]
    limit: int
    next_cursor: PendingApprovalCursor | None


class PendingApprovalResponse(BaseModel):
    success: bool
    message: str
    data: PendingApprovalPage
    error: dict | None = None
    meta: dict
