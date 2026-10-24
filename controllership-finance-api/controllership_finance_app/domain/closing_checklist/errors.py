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
