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
