"""Erros de domínio — solicitação de emissão de NF."""

from __future__ import annotations


class InvoiceIssuanceError(Exception):
    status_code = 400
    code = "INVOICE_ISSUANCE_ERROR"

    def __init__(self, message: str, *, meta: dict | None = None) -> None:
        super().__init__(message)
        self.meta = meta or {}


class InvoiceIssuanceValidationError(InvoiceIssuanceError):
    status_code = 422
    code = "VALIDATION_ERROR"


class InvoiceIssuanceNotFoundError(InvoiceIssuanceError):
    status_code = 404
    code = "NOT_FOUND"


class InvoiceIssuanceForbiddenError(InvoiceIssuanceError):
    status_code = 403
    code = "FORBIDDEN"


class InvoiceIssuanceInvalidTransitionError(InvoiceIssuanceError):
    status_code = 409
    code = "INVALID_TRANSITION"


class PartyNotFoundError(InvoiceIssuanceValidationError):
    code = "PARTY_NOT_FOUND"


class PartyBlockedError(InvoiceIssuanceValidationError):
    code = "PARTY_BLOCKED"


class ProductNotFoundError(InvoiceIssuanceValidationError):
    code = "PRODUCT_NOT_FOUND"
