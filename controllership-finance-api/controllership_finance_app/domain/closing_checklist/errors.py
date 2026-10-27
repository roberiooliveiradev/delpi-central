"""Erros tipados do domínio Central de Fechamento.

Cada erro carrega `code` (contrato HTTP) e `status` — as rotas mapeiam
para o envelope `fail(message, status, {"error": {"code": ...}})`.
"""

from __future__ import annotations


class ChecklistDomainError(Exception):
    code = "domain_error"
    status = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TemplateNotFound(ChecklistDomainError):
    code = "template_not_found"
    status = 404


class VersionNotFound(ChecklistDomainError):
    code = "version_not_found"
    status = 404


class DraftAlreadyOpen(ChecklistDomainError):
    code = "draft_already_open"
    status = 409


class VersionNotDraft(ChecklistDomainError):
    code = "version_not_draft"
    status = 409


class VersionNotPublished(ChecklistDomainError):
    code = "version_not_published"
    status = 409


class StaleRevision(ChecklistDomainError):
    code = "stale_revision"
    status = 409


class DuplicateItemKey(ChecklistDomainError):
    code = "duplicate_item_key"
    status = 409


class NoPublishedTemplate(ChecklistDomainError):
    code = "no_published_template"
    status = 409


class CompetenceNotOpened(ChecklistDomainError):
    code = "competence_not_opened"
    status = 404


class ItemNotFound(ChecklistDomainError):
    code = "item_not_found"
    status = 404


class PersistenceUnavailable(ChecklistDomainError):
    code = "persistence_unavailable"
    status = 503


class DocumentNotFound(ChecklistDomainError):
    code = "document_not_found"
    status = 404


class FileTooLarge(ChecklistDomainError):
    code = "file_too_large"
    status = 422


class UnsupportedMediaType(ChecklistDomainError):
    code = "unsupported_media_type"
    status = 415


class InvalidFileContent(ChecklistDomainError):
    code = "invalid_file_content"
    status = 422


class EmptyFile(ChecklistDomainError):
    code = "empty_file"
    status = 422


class ContentTypeMismatch(ChecklistDomainError):
    code = "content_type_mismatch"
    status = 422


class IdempotencyConflict(ChecklistDomainError):
    code = "idempotency_conflict"
    status = 409


class FileMissing(ChecklistDomainError):
    code = "file_missing"
    status = 503


class InvalidUpload(ChecklistDomainError):
    code = "invalid_upload"
    status = 422


class Forbidden(ChecklistDomainError):
    code = "forbidden"
    status = 403


class DocumentCancelled(ChecklistDomainError):
    code = "document_cancelled"
    status = 409


class DocumentNotAttached(ChecklistDomainError):
    code = "document_not_attached"
    status = 409


class InvalidStateTransition(ChecklistDomainError):
    code = "invalid_state_transition"
    status = 409


class MissingJustification(ChecklistDomainError):
    code = "missing_justification"
    status = 422


class ValidationScopeMismatch(ChecklistDomainError):
    code = "validation_scope_mismatch"
    status = 409


class ItemLocked(ChecklistDomainError):
    code = "item_locked"
    status = 409


class NoEvidence(ChecklistDomainError):
    code = "no_evidence"
    status = 409


class DecisionNotFound(ChecklistDomainError):
    code = "decision_not_found"
    status = 404


class CorrectionNotFound(ChecklistDomainError):
    code = "correction_not_found"
    status = 404


class CorrectionNotPending(ChecklistDomainError):
    code = "correction_not_pending"
    status = 409


class ItemCancelled(ChecklistDomainError):
    code = "item_cancelled"
    status = 409


class InvalidRejectionReason(ChecklistDomainError):
    code = "invalid_rejection_reason"
    status = 422


class PendencyNotFound(ChecklistDomainError):
    code = "pendency_not_found"
    status = 404


class PendencyTerminal(ChecklistDomainError):
    code = "pendency_terminal"
    status = 409


class InvalidPendencyTransition(ChecklistDomainError):
    code = "invalid_pendency_transition"
    status = 409


class MissingDismissJustification(ChecklistDomainError):
    code = "missing_dismiss_justification"
    status = 422


class InvalidPendencyKind(ChecklistDomainError):
    code = "invalid_pendency_kind"
    status = 422


class InvalidPendencyState(ChecklistDomainError):
    code = "invalid_pendency_state"
    status = 422


class ClassificationAlreadyConfirmed(ChecklistDomainError):
    code = "classification_already_confirmed"
    status = 409


class CutoffAlreadyConfirmed(ChecklistDomainError):
    code = "cutoff_already_confirmed"
    status = 409


class CutoffNotConfirmed(ChecklistDomainError):
    code = "cutoff_not_confirmed"
    status = 409


class ReconciliationNotFound(ChecklistDomainError):
    code = "reconciliation_not_found"
    status = 404


class InvalidReconciliationDomain(ChecklistDomainError):
    code = "invalid_reconciliation_domain"
    status = 422


class InvalidSourceState(ChecklistDomainError):
    code = "invalid_source_state"
    status = 422


class RevalidationNotValid(ChecklistDomainError):
    code = "revalidation_not_valid"
    status = 409


class PendencyOwnershipRequired(ChecklistDomainError):
    code = "pendency_ownership_required"
    status = 403


class OfficialDocumentRequired(ChecklistDomainError):
    code = "official_document_required"
    status = 422


class PackageNotFound(ChecklistDomainError):
    code = "package_not_found"
    status = 404


class PackageVersionNotFound(ChecklistDomainError):
    code = "package_version_not_found"
    status = 404


class InvalidPackageTransition(ChecklistDomainError):
    code = "invalid_package_transition"
    status = 409


class MissingReason(ChecklistDomainError):
    code = "missing_reason"
    status = 422


class AssignmentNotFound(ChecklistDomainError):
    code = "assignment_not_found"
    status = 404


class ReviewerNotAssigned(ChecklistDomainError):
    code = "reviewer_not_assigned"
    status = 403


class AreaDecisionTerminal(ChecklistDomainError):
    code = "area_decision_terminal"
    status = 409


class ClarificationNotFound(ChecklistDomainError):
    code = "clarification_not_found"
    status = 404


class ClarificationResolved(ChecklistDomainError):
    code = "clarification_resolved"
    status = 409


class TerminalRejectionActive(ChecklistDomainError):
    code = "terminal_rejection_active"
    status = 409


class TerminalRejectionNotFound(ChecklistDomainError):
    code = "terminal_rejection_not_found"
    status = 404


class CoordinatorRequired(ChecklistDomainError):
    code = "coordinator_required"
    status = 403


class CatalogEntryNotFound(ChecklistDomainError):
    code = "catalog_entry_not_found"
    status = 404


class InvalidCatalogEntry(ChecklistDomainError):
    code = "invalid_catalog_entry"
    status = 400


class VersionNotInReview(ChecklistDomainError):
    code = "version_not_in_review"
    status = 409


class ReviewerNotEligible(ChecklistDomainError):
    code = "reviewer_not_eligible"
    status = 403


class ItemLockedBySubmittedPackage(ChecklistDomainError):
    code = "item_locked_by_submitted_package"
    status = 409


class InvalidMessage(ChecklistDomainError):
    """Corpo/chave de mensagem fora do contrato U9 (1–4000 chars úteis,
    idempotency_key 1–128)."""

    code = "invalid_message"
    status = 422
