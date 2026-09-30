from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

from bpmn_modeler.domain.entities.model import MAX_DISPLAY_NAME_LENGTH, Model
from bpmn_modeler.domain.entities.revision import Revision, RevisionOrigin
from bpmn_modeler.domain.entities.working_copy import WorkingCopy
from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)

from .errors import (
    CONFLICT,
    INFRASTRUCTURE_FAILURE,
    INVALID_DISPLAY_NAME,
    MODEL_ARCHIVED,
    MODEL_NOT_FOUND,
    NO_CHANGES,
    OUTCOME_VERIFICATION_FAILED,
    REVISION_NOT_FOUND,
    UNAUTHORIZED_OPERATION,
    VALIDATION_BLOCKED,
    ApplicationError,
)
from .policy import (
    RecognitionState,
    artifact_checksum,
    editing_allowed,
    import_allowed,
    classify_recognition,
    save_allowed,
    sorted_issues,
)
from .ports import (
    AggregateNotFoundError,
    BlankArtifactFactoryPort,
    ClockPort,
    ConcurrencyConflictError,
    IdGeneratorPort,
    ModelRepositoryPort,
    ModelSummaryRecord,
    RepositoryError,
)
from .validation import (
    BpmnArtifactValidationPort,
    InputSafetyEvaluationPort,
    InputSafetyEvidence,
    ValidationReport,
)

PERMISSION_VIEW = "bpmn-modeler.view"
PERMISSION_EDIT = "bpmn-modeler.edit"
PERMISSION_MANAGE = "bpmn-modeler.manage"


@dataclass(frozen=True, slots=True)
class CallerIdentity:
    subject: str
    permissions: frozenset[str] = frozenset()

    def can(self, permission: str) -> bool:
        return permission in self.permissions


@dataclass(frozen=True, slots=True)
class ArtifactInput:
    """Intake boundary result: decoded artifact text + original-input evidence.

    `artifact` is None only when the input could not produce usable XML text
    (decode failure). Security-rejected inputs may carry an artifact; the
    recognition classifier decides the state from the evidence report.
    """

    artifact: CanonicalBpmnArtifact | None
    evidence: InputSafetyEvidence


@dataclass(frozen=True, slots=True)
class MutationOutcome:
    changed: bool
    model_id: str
    version: int
    artifact_sha256: str | None
    revision_number: int | None
    message: str


@dataclass(frozen=True, slots=True)
class InspectResult:
    recognition_state: RecognitionState
    eligible_to_import: bool
    validation_report: ValidationReport | None
    artifact_byte_length: int | None
    artifact_sha256: str | None
    editable: bool = False


@dataclass(frozen=True, slots=True)
class WorkingCopyRead:
    artifact: CanonicalBpmnArtifact
    version: int
    artifact_sha256: str


@dataclass(frozen=True, slots=True)
class ModelDetailRead:
    record: ModelSummaryRecord
    created_by: str
    updated_by: str


@dataclass(frozen=True, slots=True)
class PagedRecords:
    items: Sequence[Any]
    page: int
    page_size: int
    has_more: bool


MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25


class BpmnModelerService:
    """Application service implementing all 17 frozen use cases."""

    def __init__(
        self,
        *,
        repository: ModelRepositoryPort,
        validator: BpmnArtifactValidationPort,
        input_safety: InputSafetyEvaluationPort,
        blank_artifacts: BlankArtifactFactoryPort,
        clock: ClockPort,
        ids: IdGeneratorPort,
    ) -> None:
        self._repo = repository
        self._validator = validator
        self._input_safety = input_safety
        self._blanks = blank_artifacts
        self._clock = clock
        self._ids = ids

    # ------------------------------------------------------------------ #
    # helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _require(caller: CallerIdentity, permission: str) -> None:
        if not caller.can(permission):
            raise ApplicationError(
                UNAUTHORIZED_OPERATION,
                "Permissão insuficiente para esta operação.",
                {"required_permission": permission},
            )

    @staticmethod
    def _validated_name(display_name: str) -> str:
        normalized = display_name.strip()
        if not normalized or len(normalized) > MAX_DISPLAY_NAME_LENGTH:
            raise ApplicationError(
                INVALID_DISPLAY_NAME,
                "Nome de modelo inválido.",
                {"constraint": "non-empty, max 120 characters"},
            )
        return normalized

    def _get_or_404(self, model_id: str) -> Model:
        try:
            model = self._repo.get_aggregate(model_id)
        except RepositoryError as exc:
            raise ApplicationError(
                INFRASTRUCTURE_FAILURE, "Falha de infraestrutura."
            ) from exc
        if model is None:
            raise ApplicationError(MODEL_NOT_FOUND, "Modelo não encontrado.")
        return model

    def _mutate(self, model_id: str, expected_version: int, fn):
        try:
            return self._repo.mutate(model_id, expected_version, fn)
        except AggregateNotFoundError as exc:
            raise ApplicationError(MODEL_NOT_FOUND, "Modelo não encontrado.") from exc
        except ConcurrencyConflictError as exc:
            raise ApplicationError(
                CONFLICT,
                "O modelo foi alterado por outra operação.",
                {"current_version": exc.current_version},
            ) from exc
        except RepositoryError as exc:
            raise ApplicationError(
                INFRASTRUCTURE_FAILURE, "Falha de infraestrutura."
            ) from exc

    def _touch(self, model: Model, caller: CallerIdentity) -> None:
        now = self._clock.now()
        model.version += 1
        model.updated_at = now
        model.updated_by = caller.subject

    def _to_record(self, model: Model) -> ModelSummaryRecord:
        return ModelSummaryRecord(
            id=model.id,
            display_name=model.display_name,
            archived_at=model.archived_at,
            version=model.version,
            created_at=model.created_at or self._clock.now(),
            updated_at=model.updated_at or self._clock.now(),
            latest_revision_number=(
                model.latest_revision.revision_number if model.latest_revision else None
            ),
        )

    def _readback_verify(self, model_id: str, predicate) -> Model:
        model = self._get_or_404(model_id)
        if not predicate(model):
            raise ApplicationError(
                OUTCOME_VERIFICATION_FAILED,
                "O resultado não pôde ser verificado; releia o estado do modelo.",
                {"hint": "read_authoritative_first"},
            )
        return model

    def _inspect(self, raw: ArtifactInput) -> InspectResult:
        safety_report = self._sorted(self._input_safety.evaluate(raw.evidence))
        security_failed = raw.artifact is None or any(
            issue.rule_id.startswith("SEC-") for issue in safety_report.issues
        )
        if security_failed:
            state = classify_recognition(
                safety_report, decode_succeeded=raw.evidence.decode_succeeded
            )
            return InspectResult(
                recognition_state=state,
                eligible_to_import=False,
                validation_report=safety_report,
                artifact_byte_length=None,
                artifact_sha256=None,
            )
        report = self._sorted(self._validator.validate(raw.artifact, raw.evidence))
        state = classify_recognition(report)
        return InspectResult(
            recognition_state=state,
            eligible_to_import=import_allowed(state),
            validation_report=report,
            artifact_byte_length=len(raw.artifact.content.encode("utf-8")),
            artifact_sha256=artifact_checksum(raw.artifact),
            editable=editing_allowed(report),
        )

    @staticmethod
    def _sorted(report: ValidationReport) -> ValidationReport:
        return ValidationReport(
            evaluated_stages=report.evaluated_stages,
            not_evaluated_stages=report.not_evaluated_stages,
            issues=sorted_issues(report),
        )

    # ------------------------------------------------------------------ #
    # UC-MODEL-001 CreateModel                                            #
    # ------------------------------------------------------------------ #

    def create_model(
        self, display_name: str, caller: CallerIdentity
    ) -> MutationOutcome:
        self._require(caller, PERMISSION_EDIT)
        name = self._validated_name(display_name)
        now = self._clock.now()
        model = Model(
            id=self._ids.new_model_id(),
            working_copy=WorkingCopy(self._blanks.new_blank_artifact()),
            display_name=name,
            version=1,
            created_at=now,
            updated_at=now,
            created_by=caller.subject,
            updated_by=caller.subject,
        )
        try:
            self._repo.create_aggregate(model)
        except RepositoryError as exc:
            raise ApplicationError(
                INFRASTRUCTURE_FAILURE, "Falha de infraestrutura."
            ) from exc
        expected_sha = artifact_checksum(model.working_copy.artifact)
        self._readback_verify(
            model.id,
            lambda m: m.version == 1
            and artifact_checksum(m.working_copy.artifact) == expected_sha,
        )
        return MutationOutcome(
            changed=True,
            model_id=model.id,
            version=1,
            artifact_sha256=expected_sha,
            revision_number=None,
            message="Modelo criado.",
        )

    # ------------------------------------------------------------------ #
    # UC-MODEL-002 ImportModel + inspect support op                        #
    # ------------------------------------------------------------------ #

    def inspect_import(self, raw: ArtifactInput) -> InspectResult:
        return self._inspect(raw)

    def import_model(
        self, raw: ArtifactInput, display_name: str, caller: CallerIdentity
    ) -> MutationOutcome:
        self._require(caller, PERMISSION_EDIT)
        name = self._validated_name(display_name)
        inspection = self._inspect(raw)
        if not inspection.eligible_to_import or raw.artifact is None:
            raise ApplicationError(
                VALIDATION_BLOCKED,
                "O arquivo não é um BPMN 2.0 aceitável para importação.",
                {
                    "recognition_state": inspection.recognition_state.value,
                    "validation_report": inspection.validation_report,
                },
            )
        now = self._clock.now()
        model = Model(
            id=self._ids.new_model_id(),
            working_copy=WorkingCopy(raw.artifact),
            display_name=name,
            version=1,
            created_at=now,
            updated_at=now,
            created_by=caller.subject,
            updated_by=caller.subject,
        )
        try:
            self._repo.create_aggregate(model)
        except RepositoryError as exc:
            raise ApplicationError(
                INFRASTRUCTURE_FAILURE, "Falha de infraestrutura."
            ) from exc
        expected_sha = artifact_checksum(raw.artifact)
        self._readback_verify(
            model.id,
            lambda m: m.version == 1
            and artifact_checksum(m.working_copy.artifact) == expected_sha,
        )
        return MutationOutcome(
            changed=True,
            model_id=model.id,
            version=1,
            artifact_sha256=expected_sha,
            revision_number=None,
            message="Modelo importado.",
        )

    # ------------------------------------------------------------------ #
    # reads                                                                #
    # ------------------------------------------------------------------ #

    def get_model(self, model_id: str, caller: CallerIdentity) -> Model:
        self._require(caller, PERMISSION_VIEW)
        return self._get_or_404(model_id)

    def list_models(
        self,
        *,
        query: str | None,
        archived: Literal["active", "archived", "all"],
        sort: Literal["updated_at", "created_at", "display_name"],
        direction: Literal["asc", "desc"],
        page: int,
        page_size: int,
        caller: CallerIdentity,
    ) -> PagedRecords:
        self._require(caller, PERMISSION_VIEW)
        if page < 1 or not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ApplicationError(
                INVALID_DISPLAY_NAME,  # replaced by transport INVALID_REQUEST upstream
                "Parâmetros de paginação inválidos.",
            )
        try:
            rows = self._repo.list_summaries(
                query=query,
                archived=archived,
                sort=sort,
                direction=direction,
                offset=(page - 1) * page_size,
                limit=page_size + 1,
            )
        except RepositoryError as exc:
            raise ApplicationError(
                INFRASTRUCTURE_FAILURE, "Falha de infraestrutura."
            ) from exc
        return PagedRecords(
            items=list(rows[:page_size]),
            page=page,
            page_size=page_size,
            has_more=len(rows) > page_size,
        )

    def get_working_copy(
        self, model_id: str, caller: CallerIdentity
    ) -> WorkingCopyRead:
        self._require(caller, PERMISSION_VIEW)
        model = self._get_or_404(model_id)
        artifact = model.working_copy.artifact
        return WorkingCopyRead(
            artifact=artifact,
            version=model.version,
            artifact_sha256=artifact_checksum(artifact),
        )

    def list_revisions(
        self, model_id: str, page: int, page_size: int, caller: CallerIdentity
    ) -> PagedRecords:
        self._require(caller, PERMISSION_VIEW)
        model = self._get_or_404(model_id)
        ordered = sorted(model.revisions, key=lambda r: r.revision_number, reverse=True)
        start = (page - 1) * page_size
        window = ordered[start : start + page_size + 1]
        return PagedRecords(
            items=window[:page_size],
            page=page,
            page_size=page_size,
            has_more=len(window) > page_size,
        )

    def get_revision(
        self, model_id: str, revision_number: int, caller: CallerIdentity
    ) -> Revision:
        self._require(caller, PERMISSION_VIEW)
        model = self._get_or_404(model_id)
        revision = self._find_revision(model, revision_number)
        return revision

    def export_working_copy(
        self, model_id: str, caller: CallerIdentity
    ) -> WorkingCopyRead:
        return self.get_working_copy(model_id, caller)

    def export_revision(
        self, model_id: str, revision_number: int, caller: CallerIdentity
    ) -> tuple[Revision, str]:
        revision = self.get_revision(model_id, revision_number, caller)
        return revision, revision.checksum

    @staticmethod
    def _find_revision(model: Model, revision_number: int) -> Revision:
        for revision in model.revisions:
            if revision.revision_number == revision_number:
                return revision
        raise ApplicationError(REVISION_NOT_FOUND, "Revisão não encontrada.")

    # ------------------------------------------------------------------ #
    # UC-MODEL-005/006/007/008                                            #
    # ------------------------------------------------------------------ #

    def rename_model(
        self,
        model_id: str,
        display_name: str,
        expected_version: int,
        caller: CallerIdentity,
    ) -> MutationOutcome:
        self._require(caller, PERMISSION_MANAGE)
        name = self._validated_name(display_name)
        model = self._get_or_404(model_id)
        if model.archived:
            raise ApplicationError(
                MODEL_ARCHIVED,
                "Modelo arquivado; desarquive para alterar.",
                {"archived_at": model.archived_at.isoformat()},
            )
        if model.version != expected_version:
            raise ApplicationError(
                CONFLICT,
                "O modelo foi alterado por outra operação.",
                {"current_version": model.version},
            )
        if model.display_name == name:
            return MutationOutcome(
                changed=False,
                model_id=model_id,
                version=model.version,
                artifact_sha256=artifact_checksum(model.working_copy.artifact),
                revision_number=None,
                message="Nenhuma alteração aplicada.",
            )

        def _apply(aggregate: Model) -> None:
            aggregate.rename(name)
            self._touch(aggregate, caller)

        self._mutate(model_id, expected_version, _apply)
        self._readback_verify(
            model_id,
            lambda m: m.version == expected_version + 1 and m.display_name == name,
        )
        return MutationOutcome(
            changed=True,
            model_id=model_id,
            version=expected_version + 1,
            artifact_sha256=artifact_checksum(model.working_copy.artifact),
            revision_number=None,
            message="Modelo renomeado.",
        )

    def duplicate_model(
        self, source_id: str, display_name: str, caller: CallerIdentity
    ) -> MutationOutcome:
        self._require(caller, PERMISSION_MANAGE)
        self._require(caller, PERMISSION_VIEW)
        name = self._validated_name(display_name)
        source = self._get_or_404(source_id)
        now = self._clock.now()
        artifact = CanonicalBpmnArtifact(source.working_copy.artifact.content)
        model = Model(
            id=self._ids.new_model_id(),
            working_copy=WorkingCopy(artifact),
            display_name=name,
            version=1,
            created_at=now,
            updated_at=now,
            created_by=caller.subject,
            updated_by=caller.subject,
        )
        try:
            self._repo.create_aggregate(model)
        except RepositoryError as exc:
            raise ApplicationError(
                INFRASTRUCTURE_FAILURE, "Falha de infraestrutura."
            ) from exc
        expected_sha = artifact_checksum(artifact)
        self._readback_verify(
            model.id,
            lambda m: m.version == 1
            and artifact_checksum(m.working_copy.artifact) == expected_sha,
        )
        return MutationOutcome(
            changed=True,
            model_id=model.id,
            version=1,
            artifact_sha256=expected_sha,
            revision_number=None,
            message="Modelo duplicado.",
        )

    def archive_model(
        self, model_id: str, expected_version: int, caller: CallerIdentity
    ) -> MutationOutcome:
        return self._set_archived(model_id, expected_version, caller, archive=True)

    def unarchive_model(
        self, model_id: str, expected_version: int, caller: CallerIdentity
    ) -> MutationOutcome:
        return self._set_archived(model_id, expected_version, caller, archive=False)

    def _set_archived(
        self,
        model_id: str,
        expected_version: int,
        caller: CallerIdentity,
        *,
        archive: bool,
    ) -> MutationOutcome:
        self._require(caller, PERMISSION_MANAGE)
        model = self._get_or_404(model_id)
        if model.version != expected_version:
            raise ApplicationError(
                CONFLICT,
                "O modelo foi alterado por outra operação.",
                {"current_version": model.version},
            )
        if model.archived == archive:
            return MutationOutcome(
                changed=False,
                model_id=model_id,
                version=model.version,
                artifact_sha256=artifact_checksum(model.working_copy.artifact),
                revision_number=None,
                message="Nenhuma alteração aplicada.",
            )

        def _apply(aggregate: Model) -> None:
            if archive:
                aggregate.archive(self._clock.now())
            else:
                aggregate.unarchive()
            self._touch(aggregate, caller)

        self._mutate(model_id, expected_version, _apply)
        self._readback_verify(
            model_id,
            lambda m: m.version == expected_version + 1 and m.archived == archive,
        )
        return MutationOutcome(
            changed=True,
            model_id=model_id,
            version=expected_version + 1,
            artifact_sha256=artifact_checksum(model.working_copy.artifact),
            revision_number=None,
            message="Modelo arquivado." if archive else "Modelo desarquivado.",
        )

    # ------------------------------------------------------------------ #
    # UC-WC-002 / UC-WC-004                                               #
    # ------------------------------------------------------------------ #

    def save_working_copy(
        self,
        model_id: str,
        raw: ArtifactInput,
        expected_version: int,
        caller: CallerIdentity,
    ) -> MutationOutcome:
        self._require(caller, PERMISSION_EDIT)
        model = self._get_or_404(model_id)
        if model.archived:
            raise ApplicationError(
                MODEL_ARCHIVED,
                "Modelo arquivado; desarquive para editar.",
                {"archived_at": model.archived_at.isoformat()},
            )
        if model.version != expected_version:
            raise ApplicationError(
                CONFLICT,
                "O modelo foi alterado por outra operação.",
                {"current_version": model.version},
            )
        if raw.artifact is None:
            report = self._input_safety.evaluate(raw.evidence)
            raise ApplicationError(
                VALIDATION_BLOCKED,
                "O conteúdo não é XML utilizável.",
                {
                    "recognition_state": RecognitionState.NON_XML.value,
                    "validation_report": report,
                },
            )
        if raw.artifact.content == model.working_copy.artifact.content:
            return MutationOutcome(
                changed=False,
                model_id=model_id,
                version=model.version,
                artifact_sha256=artifact_checksum(model.working_copy.artifact),
                revision_number=None,
                message="Nenhuma alteração aplicada.",
            )
        report = self._validator.validate(raw.artifact, raw.evidence)
        state = classify_recognition(
            report, decode_succeeded=raw.evidence.decode_succeeded
        )
        if not save_allowed(state, report):
            raise ApplicationError(
                VALIDATION_BLOCKED,
                "O conteúdo enviado não pode ser salvo.",
                {
                    "recognition_state": state.value,
                    "validation_report": ValidationReport(
                        evaluated_stages=report.evaluated_stages,
                        not_evaluated_stages=report.not_evaluated_stages,
                        issues=sorted_issues(report),
                    ),
                },
            )
        content = raw.artifact.content
        expected_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

        def _apply(aggregate: Model) -> None:
            aggregate.working_copy.replace_artifact(CanonicalBpmnArtifact(content))
            self._touch(aggregate, caller)

        self._mutate(model_id, expected_version, _apply)
        self._readback_verify(
            model_id,
            lambda m: m.version == expected_version + 1
            and artifact_checksum(m.working_copy.artifact) == expected_sha,
        )
        return MutationOutcome(
            changed=True,
            model_id=model_id,
            version=expected_version + 1,
            artifact_sha256=expected_sha,
            revision_number=None,
            message="Modelo salvo.",
        )

    def validate_working_copy(
        self, model_id: str, raw: ArtifactInput, caller: CallerIdentity
    ) -> ValidationReport:
        self._require(caller, PERMISSION_VIEW)
        self._get_or_404(model_id)
        safety_report = self._sorted(self._input_safety.evaluate(raw.evidence))
        if raw.artifact is None or any(
            issue.rule_id.startswith("SEC-") for issue in safety_report.issues
        ):
            raise ApplicationError(
                "INPUT_REJECTED_SECURITY",
                "O conteúdo enviado foi rejeitado pela verificação de segurança.",
                {"validation_report": safety_report},
            )
        return self._sorted(self._validator.validate(raw.artifact, raw.evidence))

    # ------------------------------------------------------------------ #
    # UC-REV-003 / UC-REV-004                                             #
    # ------------------------------------------------------------------ #

    def create_revision(
        self, model_id: str, expected_version: int, caller: CallerIdentity
    ) -> MutationOutcome:
        self._require(caller, PERMISSION_MANAGE)
        model = self._get_or_404(model_id)
        if model.archived:
            raise ApplicationError(
                MODEL_ARCHIVED,
                "Modelo arquivado; desarquive para alterar.",
                {"archived_at": model.archived_at.isoformat()},
            )
        if model.version != expected_version:
            raise ApplicationError(
                CONFLICT,
                "O modelo foi alterado por outra operação.",
                {"current_version": model.version},
            )
        wc_sha = artifact_checksum(model.working_copy.artifact)
        latest = model.latest_revision
        if latest is not None and latest.checksum == wc_sha:
            raise ApplicationError(
                NO_CHANGES,
                "Nenhuma alteração desde a última revisão.",
            )
        next_number = (latest.revision_number + 1) if latest else 1
        revision_id = self._ids.new_revision_id()
        now = self._clock.now()

        def _apply(aggregate: Model) -> str:
            aggregate.append_revision(
                Revision(
                    revision_id=revision_id,
                    revision_number=next_number,
                    artifact=CanonicalBpmnArtifact(
                        aggregate.working_copy.artifact.content
                    ),
                    checksum=wc_sha,
                    created_at=now,
                    created_by=caller.subject,
                    origin=RevisionOrigin.EXPLICIT,
                )
            )
            self._touch(aggregate, caller)
            return revision_id

        _, created_id = self._mutate(model_id, expected_version, _apply)
        self._readback_verify(
            model_id,
            lambda m: m.version == expected_version + 1
            and any(
                r.revision_id == created_id
                and r.revision_number == next_number
                and r.checksum == wc_sha
                for r in m.revisions
            ),
        )
        return MutationOutcome(
            changed=True,
            model_id=model_id,
            version=expected_version + 1,
            artifact_sha256=wc_sha,
            revision_number=next_number,
            message="Revisão criada.",
        )

    def restore_revision(
        self,
        model_id: str,
        revision_number: int,
        expected_version: int,
        caller: CallerIdentity,
    ) -> MutationOutcome:
        self._require(caller, PERMISSION_MANAGE)
        model = self._get_or_404(model_id)
        if model.archived:
            raise ApplicationError(
                MODEL_ARCHIVED,
                "Modelo arquivado; desarquive para alterar.",
                {"archived_at": model.archived_at.isoformat()},
            )
        target = self._find_revision(model, revision_number)
        if model.version != expected_version:
            raise ApplicationError(
                CONFLICT,
                "O modelo foi alterado por outra operação.",
                {"current_version": model.version},
            )
        if artifact_checksum(target.artifact) == artifact_checksum(
            model.working_copy.artifact
        ):
            return MutationOutcome(
                changed=False,
                model_id=model_id,
                version=model.version,
                artifact_sha256=artifact_checksum(model.working_copy.artifact),
                revision_number=None,
                message="Nenhuma alteração aplicada.",
            )
        next_number = (
            model.latest_revision.revision_number + 1 if model.latest_revision else 1
        )
        revision_id = self._ids.new_revision_id()
        restored_id = target.revision_id
        now = self._clock.now()

        def _apply(aggregate: Model) -> str:
            aggregate.working_copy.replace_artifact(
                CanonicalBpmnArtifact(target.artifact.content)
            )
            aggregate.append_revision(
                Revision(
                    revision_id=revision_id,
                    revision_number=next_number,
                    artifact=CanonicalBpmnArtifact(target.artifact.content),
                    checksum=artifact_checksum(target.artifact),
                    created_at=now,
                    created_by=caller.subject,
                    origin=RevisionOrigin.RESTORE,
                    restored_from_revision_id=restored_id,
                )
            )
            self._touch(aggregate, caller)
            return revision_id

        _, created_id = self._mutate(model_id, expected_version, _apply)
        target_sha = artifact_checksum(target.artifact)
        self._readback_verify(
            model_id,
            lambda m: m.version == expected_version + 1
            and artifact_checksum(m.working_copy.artifact) == target_sha
            and any(
                r.revision_id == created_id and r.revision_number == next_number
                for r in m.revisions
            ),
        )
        return MutationOutcome(
            changed=True,
            model_id=model_id,
            version=expected_version + 1,
            artifact_sha256=target_sha,
            revision_number=next_number,
            message="Revisão restaurada.",
        )
