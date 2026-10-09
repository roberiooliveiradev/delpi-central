"""Use cases for the Transformômetro-owned native BPMN document (G7).

Ownership: the artifact lives in transformometro.processo_bpmn_documents +
processo_bpmn_revisions — scoped to the processo, never to the creator.

XOR (ADR-006): a processo has either a native document OR an external
reference (processo_bpmn_references, G5) — never both. Writes fail closed
with 409 DUAL_MODE_FORBIDDEN.

Concurrency: optimistic `version` — every write requires `expected_version`
(If-Match "v<n>"); stale → 409 VERSION_CONFLICT.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any
from uuid import UUID

from tm_app.application.security.authorization_policy import (
    TransformometroAuthorizationPolicy,
)
from tm_app.domain.entities.process_bpmn_document import (
    ProcessBpmnDocument,
    ProcessBpmnRevision,
)
from tm_app.domain.ports.process_bpmn_document_repository_port import (
    ProcessBpmnDocumentRepositoryPort,
)
from tm_app.domain.ports.process_bpmn_reference_repository_port import (
    ProcessBpmnReferenceRepositoryPort,
)

from bpmn_validation import (
    LxmlBpmnValidator,
    TemplateBlankArtifactFactory,
    ValidationReport,
    intake_bytes,
)

MAX_XML_BYTES = 10_485_760


class DualModeConflict(RuntimeError):
    """XOR violation — o processo já está no outro modo BPMN."""

    status_code = 409


class VersionConflict(RuntimeError):
    """If-Match stale — optimistic concurrency."""

    status_code = 409


class UnsafeArtifact(ValueError):
    """INPUT_SAFETY violation — falha fechada na fronteira."""


class _UuidBpmnIds:
    def new_bpmn_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _normalize_uuid(value: str, label: str) -> str:
    raw = str(value or "").strip()
    try:
        return str(UUID(raw))
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f"{label} inválido.") from None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _issue_dict(issue: Any) -> dict[str, Any]:
    """Mesmo shape do ValidationIssueResponse do Modeler (parity contract)."""
    element_id = None
    path = None
    if issue.reference:
        prefix, _, rest = issue.reference.partition(":")
        if prefix in ("element", "diagram", "extension"):
            element_id = rest or issue.reference
        else:
            path = issue.reference
    return {
        "rule_id": issue.rule_id,
        "rule_source": issue.source.value,
        "stage": issue.stage.value,
        "severity": issue.severity.value,
        "message": issue.message,
        "element_id": element_id,
        "path": path,
    }


def _report_dict(report: ValidationReport) -> dict[str, Any]:
    return {
        "evaluated_stages": sorted(s.value for s in report.evaluated_stages),
        "not_evaluated_stages": sorted(
            s.value for s in report.not_evaluated_stages
        ),
        "issues": [_issue_dict(i) for i in report.issues],
    }


class ProcessBpmnDocumentUseCases:
    def __init__(
        self,
        docs: ProcessBpmnDocumentRepositoryPort,
        refs: ProcessBpmnReferenceRepositoryPort | None = None,
        validator: LxmlBpmnValidator | None = None,
        policy: TransformometroAuthorizationPolicy | None = None,
    ) -> None:
        self._docs = docs
        self._refs = refs
        self._validator = validator or LxmlBpmnValidator()
        self._blank_factory = TemplateBlankArtifactFactory(_UuidBpmnIds())
        self._policy = policy or TransformometroAuthorizationPolicy()

    # -- helpers -----------------------------------------------------------

    def _require_processo(self, processo_id: str) -> str:
        pid = _normalize_uuid(processo_id, "processo_id")
        if not self._docs.process_exists(pid):
            raise LookupError("Processo não encontrado.")
        return pid

    def _require_doc(self, processo_id: str) -> ProcessBpmnDocument:
        doc = self._docs.get_active(processo_id)
        if doc is None:
            raise LookupError("O processo não possui documento BPMN nativo.")
        return doc

    def _assert_native_allowed(self, processo_id: str) -> None:
        """XOR: criação nativa é proibida com referência externa ativa."""
        if self._refs is not None and self._refs.get_active(processo_id) is not None:
            raise DualModeConflict(
                "O processo já referencia um modelo BPMN externo; "
                "desvincule-o antes de criar o documento nativo."
            )

    def _validate_or_raise(self, xml: str) -> ValidationReport:
        evidence_and_artifact = intake_bytes(xml.encode("utf-8"))
        artifact = evidence_and_artifact.artifact
        if artifact is None:
            raise UnsafeArtifact("O artefato BPMN enviado não é XML utilizável.")
        report = self._validator.validate(
            artifact, evidence=evidence_and_artifact.evidence
        )
        for issue in report.issues:
            if issue.severity.value == "ERROR" and issue.stage.value == "input_safety":
                raise UnsafeArtifact(
                    f"Artefato rejeitado na fronteira segura: {issue.message}"
                )
        return report

    # -- reads -------------------------------------------------------------

    def get_document(self, user: Any, processo_id: str) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._docs.get_active(pid)
        if doc is None:
            raise LookupError("O processo não possui documento BPMN nativo.")
        return {"document": doc.to_dict(), "version": doc.version}

    def get_working_copy(self, user: Any, processo_id: str) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._require_doc(pid)
        return {
            "xml": doc.working_copy_xml,
            "version": doc.version,
            "sha256": doc.working_copy_sha256,
        }

    def list_revisions(self, user: Any, processo_id: str) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._require_doc(pid)
        items = [r.to_dict() for r in self._docs.list_revisions(doc.id)]
        return {"items": items, "document": doc.to_dict()}

    def get_revision(
        self, user: Any, processo_id: str, revision_number: int
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._require_doc(pid)
        rev = self._docs.get_revision(doc.id, int(revision_number))
        if rev is None:
            raise LookupError("Revisão BPMN não encontrada.")
        return {"revision": rev.to_dict()}

    def export_revision_xml(
        self, user: Any, processo_id: str, revision_number: int
    ) -> ProcessBpmnRevision:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._require_doc(pid)
        rev = self._docs.get_revision(doc.id, int(revision_number), with_artifact=True)
        if rev is None or rev.artifact_xml is None:
            raise LookupError("Revisão BPMN não encontrada.")
        return rev

    def export_working_copy(self, user: Any, processo_id: str) -> ProcessBpmnDocument:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        return self._require_doc(pid)

    def validate_working_copy(
        self, user: Any, processo_id: str, candidate_xml: str | None
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._require_doc(pid)
        xml = candidate_xml if candidate_xml is not None else doc.working_copy_xml
        try:
            report = self._validate_or_raise(xml)
        except UnsafeArtifact as exc:
            return {"document": doc.to_dict(), "report": {"fatal": str(exc)}}
        return {"document": doc.to_dict(), "report": _report_dict(report)}

    # -- writes ------------------------------------------------------------

    def create_document(
        self, user: Any, processo_id: str, xml: str | None
    ) -> ProcessBpmnDocument:
        """Cria o documento nativo (blank ou import). XOR enforcement:
        falha 409 se houver referência externa ativa no processo."""
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        if self._docs.has_active(pid):
            raise DualModeConflict("O processo já possui documento BPMN nativo.")
        self._assert_native_allowed(pid)

        if xml is None:
            artifact = self._blank_factory.new_blank_artifact()
            xml = artifact.content
        else:
            self._validate_or_raise(xml)

        if len(xml.encode("utf-8")) > MAX_XML_BYTES:
            raise UnsafeArtifact("Artefato BPMN excede o limite de tamanho.")
        return self._docs.create(
            processo_id=pid,
            working_copy_xml=xml,
            working_copy_sha256=_sha256(xml),
            actor_user_id=str(getattr(user, "id", "") or getattr(user, "sub", "")),
        )

    def save_working_copy(
        self,
        user: Any,
        processo_id: str,
        *,
        xml: str,
        expected_version: int,
    ) -> ProcessBpmnDocument:
        """Autosave governado: valida fronteira → write otimista → read-back
        autoritativo (mesma semântica SaveMachine do editor compartilhado)."""
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._require_doc(pid)
        self._validate_or_raise(xml)
        if len(xml.encode("utf-8")) > MAX_XML_BYTES:
            raise UnsafeArtifact("Artefato BPMN excede o limite de tamanho.")
        updated = self._docs.update_working_copy(
            document_id=doc.id,
            working_copy_xml=xml,
            working_copy_sha256=_sha256(xml),
            expected_version=expected_version,
            actor_user_id=str(getattr(user, "id", "") or getattr(user, "sub", "")),
        )
        if updated is None:
            raise VersionConflict(
                "O documento foi alterado por outra sessão; recarregue antes de salvar."
            )
        return updated

    def delete_document(self, user: Any, processo_id: str) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        removed = self._docs.soft_delete(
            processo_id=pid,
            actor_user_id=str(getattr(user, "id", "") or getattr(user, "sub", "")),
        )
        if removed is None:
            raise LookupError("O processo não possui documento BPMN nativo.")
        return {"deleted": True, "document_id": removed.id}

    def create_revision(
        self,
        user: Any,
        processo_id: str,
        *,
        expected_version: int,
        name: str | None,
        description: str | None,
    ) -> ProcessBpmnRevision:
        """Checkpoint explícito e imutável do working copy corrente —
        autosave NUNCA cria revisão (invariante ADR-006)."""
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._require_doc(pid)
        rev = self._docs.create_revision(
            document_id=doc.id,
            artifact_xml=doc.working_copy_xml,
            artifact_sha256=doc.working_copy_sha256,
            origin="explicit",
            restored_from_revision_id=None,
            name=name,
            description=description,
            actor_user_id=str(getattr(user, "id", "") or getattr(user, "sub", "")),
            actor_name=str(
                getattr(user, "name", "") or getattr(user, "display_name", "") or ""
            )
            or None,
            expected_version=expected_version,
        )
        if rev is None:
            raise VersionConflict(
                "O documento foi alterado por outra sessão; recarregue antes de versionar."
            )
        return rev

    def restore_revision(
        self,
        user: Any,
        processo_id: str,
        revision_number: int,
        *,
        expected_version: int,
    ) -> tuple[ProcessBpmnDocument, ProcessBpmnRevision]:
        """working_copy ← artefato histórico + nova revisão origin='restore'
        com proveniência — atomicamente (mesma semântica do Modeler)."""
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        doc = self._require_doc(pid)
        outcome = self._docs.restore_revision(
            document_id=doc.id,
            revision_number=int(revision_number),
            expected_version=expected_version,
            actor_user_id=str(getattr(user, "id", "") or getattr(user, "sub", "")),
            actor_name=str(
                getattr(user, "name", "") or getattr(user, "display_name", "") or ""
            )
            or None,
        )
        if outcome is None:
            raise VersionConflict(
                "Restore abortado: documento alterado por outra sessão ou revisão ausente."
            )
        return outcome
