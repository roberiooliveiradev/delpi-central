"""Composition root — lançamento-notas-fiscais."""
from __future__ import annotations

from app.application.use_cases.lancamento_notas_fiscais.invoice_posting_use_cases import (
    AddInvoicePostingCommentUseCase,
    BlockInvoicePostingRequestUseCase,
    CancelInvoicePostingRequestUseCase,
    CreateInvoicePostingRequestUseCase,
    GetInvoicePostingRequestUseCase,
    ListInvoicePostingRequestsUseCase,
    PostManualInvoicePostingRequestUseCase,
    RefreshInvoicePostingReconciliationUseCase,
    ResumeInvoicePostingRequestUseCase,
    RunInvoicePostingReconciliationUseCase,
    SearchSuppliersUseCase,
    StartInvoicePostingRequestUseCase,
    UpdateInvoicePostingRequestUseCase,
)
from app.infrastructure.persistence.plugins.repositories.lancamento_notas_fiscais.postgres_invoice_posting_repository import (
    PostgresInvoicePostingRepository,
)
from app.infrastructure.persistence.totvs.invoice_posting_repositories.totvs_invoice_posting_sf1_repository import (
    TotvsInvoicePostingSf1Repository,
)
from app.infrastructure.persistence.totvs.supplier_repositories.totvs_supplier_repository import (
    TotvsSupplierRepository,
)


def build_invoice_posting_request_repository() -> PostgresInvoicePostingRepository:
    return PostgresInvoicePostingRepository()


def build_supplier_repository() -> TotvsSupplierRepository:
    return TotvsSupplierRepository()


def build_invoice_posting_sf1_repository() -> TotvsInvoicePostingSf1Repository:
    return TotvsInvoicePostingSf1Repository()


def build_search_suppliers_use_case() -> SearchSuppliersUseCase:
    return SearchSuppliersUseCase(build_supplier_repository())


def build_create_invoice_posting_request_use_case() -> CreateInvoicePostingRequestUseCase:
    return CreateInvoicePostingRequestUseCase(
        build_invoice_posting_request_repository(),
        build_supplier_repository(),
    )


def build_list_invoice_posting_requests_use_case() -> ListInvoicePostingRequestsUseCase:
    return ListInvoicePostingRequestsUseCase(build_invoice_posting_request_repository())


def build_get_invoice_posting_request_use_case() -> GetInvoicePostingRequestUseCase:
    return GetInvoicePostingRequestUseCase(build_invoice_posting_request_repository())


def build_update_invoice_posting_request_use_case() -> UpdateInvoicePostingRequestUseCase:
    repo = build_invoice_posting_request_repository()
    reconciler = RunInvoicePostingReconciliationUseCase(
        repo,
        build_invoice_posting_sf1_repository(),
    )
    return UpdateInvoicePostingRequestUseCase(
        repo,
        build_supplier_repository(),
        reconciler=reconciler,
    )


def build_start_invoice_posting_request_use_case() -> StartInvoicePostingRequestUseCase:
    return StartInvoicePostingRequestUseCase(build_invoice_posting_request_repository())


def build_block_invoice_posting_request_use_case() -> BlockInvoicePostingRequestUseCase:
    return BlockInvoicePostingRequestUseCase(build_invoice_posting_request_repository())


def build_resume_invoice_posting_request_use_case() -> ResumeInvoicePostingRequestUseCase:
    return ResumeInvoicePostingRequestUseCase(build_invoice_posting_request_repository())


def build_cancel_invoice_posting_request_use_case() -> CancelInvoicePostingRequestUseCase:
    return CancelInvoicePostingRequestUseCase(build_invoice_posting_request_repository())


def build_post_manual_invoice_posting_request_use_case() -> (
    PostManualInvoicePostingRequestUseCase
):
    return PostManualInvoicePostingRequestUseCase(
        build_invoice_posting_request_repository()
    )


def build_add_invoice_posting_comment_use_case() -> AddInvoicePostingCommentUseCase:
    return AddInvoicePostingCommentUseCase(build_invoice_posting_request_repository())


def build_run_invoice_posting_reconciliation_use_case() -> (
    RunInvoicePostingReconciliationUseCase
):
    return RunInvoicePostingReconciliationUseCase(
        build_invoice_posting_request_repository(),
        build_invoice_posting_sf1_repository(),
    )


def build_refresh_invoice_posting_reconciliation_use_case() -> (
    RefreshInvoicePostingReconciliationUseCase
):
    repo = build_invoice_posting_request_repository()
    run_uc = RunInvoicePostingReconciliationUseCase(
        repo,
        build_invoice_posting_sf1_repository(),
    )
    return RefreshInvoicePostingReconciliationUseCase(repo, run_uc)
