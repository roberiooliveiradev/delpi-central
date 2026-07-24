"""Exceções de domínio — lançamento-notas-fiscais."""
from __future__ import annotations


class InvoicePostingError(Exception):
    code: str = "invoice_posting_request.error"
    status_code: int = 400

    def __init__(self, message: str, *, meta: dict | None = None) -> None:
        super().__init__(message)
        self.meta = meta or {}


class InvoicePostingNotFoundError(InvoicePostingError):
    code = "invoice_posting_request.not_found"
    status_code = 404


class InvoicePostingDuplicateError(InvoicePostingError):
    code = "invoice_posting_request.duplicate"
    status_code = 409


class InvoicePostingInvalidTransitionError(InvoicePostingError):
    code = "invoice_posting_request.invalid_transition"
    status_code = 409


class InvoicePostingForbiddenError(InvoicePostingError):
    code = "invoice_posting_request.not_owner"
    status_code = 403


class InvoicePostingConflictError(InvoicePostingError):
    code = "invoice_posting_request.already_assigned"
    status_code = 409


class InvoicePostingReconciliationBusyError(InvoicePostingError):
    code = "invoice_posting_reconciliation.busy"
    status_code = 409


class InvoicePostingErpQueryError(InvoicePostingError):
    code = "invoice_posting_reconciliation.erp_unavailable"
    status_code = 502


class InvoicePostingValidationError(InvoicePostingError):
    code = "invoice_posting_request.validation_error"
    status_code = 422


class SupplierNotFoundError(InvoicePostingError):
    code = "supplier.not_found"
    status_code = 404


class SupplierBlockedError(InvoicePostingError):
    code = "supplier.blocked"
    status_code = 422


class DuplicateFiscalKeyError(Exception):
    """Violação do índice único parcial de chave fiscal ativa."""
