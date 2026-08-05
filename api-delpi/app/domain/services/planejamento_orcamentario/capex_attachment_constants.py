"""Constantes de anexos CAPEX (Fase 2B.3)."""

from __future__ import annotations

ENTITY_TYPE_CAPEX_ATTACHMENT = "capex_investment_attachment"

ATTACHMENT_TYPE_QUOTATION = "quotation"
ATTACHMENT_TYPE_COMMERCIAL_PROPOSAL = "commercial_proposal"
ATTACHMENT_TYPE_TECHNICAL_SPECIFICATION = "technical_specification"
ATTACHMENT_TYPE_IMAGE = "image"
ATTACHMENT_TYPE_JUSTIFICATION = "justification"
ATTACHMENT_TYPE_OTHER = "other"

ALLOWED_ATTACHMENT_TYPES = frozenset(
    {
        ATTACHMENT_TYPE_QUOTATION,
        ATTACHMENT_TYPE_COMMERCIAL_PROPOSAL,
        ATTACHMENT_TYPE_TECHNICAL_SPECIFICATION,
        ATTACHMENT_TYPE_IMAGE,
        ATTACHMENT_TYPE_JUSTIFICATION,
        ATTACHMENT_TYPE_OTHER,
    }
)

AUDIT_ACTION_UPLOADED = "attachment.uploaded"
AUDIT_ACTION_ARCHIVED = "attachment.archived"
AUDIT_ACTION_DOWNLOADED = "attachment.downloaded"
AUDIT_ACTION_ACCESS_DENIED = "attachment.access_denied"
AUDIT_ACTION_UPLOAD_REJECTED = "attachment.upload_rejected"
