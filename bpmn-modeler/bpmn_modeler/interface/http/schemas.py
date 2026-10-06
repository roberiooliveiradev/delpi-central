from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from bpmn_modeler.application.policy import RecognitionState
from bpmn_modeler.application.use_cases import MutationOutcome
from bpmn_modeler.application.validation import (
    ValidationIssue,
    ValidationReport,
)
from bpmn_modeler.domain.entities.model import Model
from bpmn_modeler.domain.entities.revision import Revision


class ModelSummaryResponse(BaseModel):
    id: str
    display_name: str
    archived_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime
    latest_revision_number: int | None


class ModelDetailResponse(ModelSummaryResponse):
    created_by: str
    updated_by: str


class RevisionSummaryResponse(BaseModel):
    revision_number: int
    revision_id: str
    origin: Literal["explicit", "restore"]
    created_at: datetime
    created_by: str
    artifact_sha256: str
    name: str | None = None
    description: str | None = None
    created_by_name: str | None = None


class CreateRevisionRequest(BaseModel):
    """Metadados opcionais do checkpoint — imutáveis após a criação."""

    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ValidationIssueResponse(BaseModel):
    rule_id: str
    rule_source: str
    stage: str
    severity: str
    message: str
    element_id: str | None
    path: str | None


class ValidationReportResponse(BaseModel):
    evaluated_stages: list[str]
    not_evaluated_stages: list[str]
    issues: list[ValidationIssueResponse]


class ImportInspectionResponse(BaseModel):
    recognition_state: RecognitionState
    eligible_to_import: bool
    validation_report: ValidationReportResponse | None
    artifact_byte_length: int | None
    artifact_sha256: str | None


class MutationResultResponse(BaseModel):
    changed: bool
    model_id: str
    version: int
    artifact_sha256: str | None
    revision_number: int | None
    message: str


class PagedModelsResponse(BaseModel):
    items: list[ModelSummaryResponse]
    page: int
    page_size: int
    has_more: bool


class PagedRevisionsResponse(BaseModel):
    items: list[RevisionSummaryResponse]
    page: int
    page_size: int
    has_more: bool


class CreateModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=120)


class RenameModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=120)


class DuplicateModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=120)


# --------------------------------------------------------------------- #
# mappers                                                                #
# --------------------------------------------------------------------- #

def model_summary(model: Model) -> ModelSummaryResponse:
    latest = model.latest_revision
    return ModelSummaryResponse(
        id=model.id,
        display_name=model.display_name,
        archived_at=model.archived_at,
        version=model.version,
        created_at=model.created_at,
        updated_at=model.updated_at,
        latest_revision_number=latest.revision_number if latest else None,
    )


def model_detail(model: Model) -> ModelDetailResponse:
    return ModelDetailResponse(
        **model_summary(model).model_dump(),
        created_by=model.created_by,
        updated_by=model.updated_by,
    )


def summary_record_to_response(record) -> ModelSummaryResponse:
    return ModelSummaryResponse(
        id=record.id,
        display_name=record.display_name,
        archived_at=record.archived_at,
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
        latest_revision_number=record.latest_revision_number,
    )


def revision_summary(revision: Revision) -> RevisionSummaryResponse:
    return RevisionSummaryResponse(
        revision_number=revision.revision_number,
        revision_id=revision.revision_id,
        origin=revision.origin.value,
        created_at=revision.created_at,
        created_by=revision.created_by,
        artifact_sha256=revision.checksum,
        name=revision.name,
        description=revision.description,
        created_by_name=revision.created_by_name,
    )


def issue_response(issue: ValidationIssue) -> ValidationIssueResponse:
    element_id = None
    path = None
    if issue.reference:
        prefix, _, rest = issue.reference.partition(":")
        if prefix in ("element", "diagram", "extension"):
            element_id = rest or issue.reference
        elif prefix == "xml":
            path = issue.reference
        else:
            path = issue.reference
    return ValidationIssueResponse(
        rule_id=issue.rule_id,
        rule_source=issue.source.value,
        stage=issue.stage.value,
        severity=issue.severity.value,
        message=issue.message,
        element_id=element_id,
        path=path,
    )


def report_response(report: ValidationReport) -> ValidationReportResponse:
    return ValidationReportResponse(
        evaluated_stages=[s.value for s in report.evaluated_stages],
        not_evaluated_stages=[s.value for s in report.not_evaluated_stages],
        issues=[issue_response(i) for i in report.issues],
    )


def mutation_result(outcome: MutationOutcome) -> MutationResultResponse:
    return MutationResultResponse(
        changed=outcome.changed,
        model_id=outcome.model_id,
        version=outcome.version,
        artifact_sha256=outcome.artifact_sha256,
        revision_number=outcome.revision_number,
        message=outcome.message,
    )
