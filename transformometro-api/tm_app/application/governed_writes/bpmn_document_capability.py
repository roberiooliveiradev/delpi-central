"""Governed native BPMN 2.0 authoring — PREPARE/EXECUTE/VERIFY hooks.

Ports & adapters: the orchestrator composes a BpmnDocumentWriteStack
(document + reference read ports and the canonical
ProcessBpmnDocumentUseCases) and calls the hooks below. The capability
NEVER writes bpmn_modeler.* or legacy flowchart entities directly —
the Transformômetro application use case owns every authoritative
write, validation, versioning and XOR dual-mode enforcement.

Mirrors bpmn_migration_capability: PREPARE reads current state, runs
the same candidate-XML validation pipeline as the Portal editor save
path, and seals the exact change + fingerprint into the proposal;
EXECUTE performs the canonical write via the use case; VERIFY reads
back the active document/revision and proves the sealed postcondition.

Capabilities (same PREPARE surface, action selects the operation):

- create_bpmn_document — creates the native document (blank artifact
  or caller-supplied BPMN XML). Fails 409 when a native document or an
  external BPMN reference is already active (canonical XOR).
- save_bpmn_working_copy — governed autosave; requires expected_version
  matching the canonical If-Match semantics of the shared SaveMachine.
- create_bpmn_revision — immutable checkpoint of the current working
  copy; autosave NEVER creates revisions (ADR-006 invariant).

Reads of existing state are fail-closed: absent document, dual mode,
stale version, unsafe/oversized XML surface as ready=false proposals
or typed GovernedWriteError so COMMIT cannot silently drift. The
legacy flowchart_v1 entities are untouched — LEGACY_DIAGRAM_READ_ONLY
remains in force and nothing in this stack can reach legacy writes.
"""

from __future__ import annotations

import hashlib
from typing import Any, NamedTuple
from uuid import UUID

from fastapi import Request

from bpmn_validation import LxmlBpmnValidator, intake_bytes

from tm_app.application.governed_writes.errors import (
    NOT_FOUND,
    OUTCOME_VERIFICATION_FAILED,
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.proposal import fingerprint
from tm_app.application.ports.bpmn_layout_port import (
    BpmnLayoutError,
    BpmnLayoutPort,
)
from tm_app.application.use_cases.manage_process_bpmn_document import (
    MAX_XML_BYTES,
    DualModeConflict,
    ProcessBpmnDocumentUseCases,
    UnsafeArtifact,
    VersionConflict,
)
from tm_app.domain.ports.process_bpmn_document_repository_port import (
    ProcessBpmnDocumentRepositoryPort,
)
from tm_app.domain.ports.process_bpmn_reference_repository_port import (
    ProcessBpmnReferenceRepositoryPort,
)
from tm_app.interface.http.branch_access_http import (
    check_processo_manage_access,
)

CREATE_BPMN_DOCUMENT_CAPABILITY = "create_bpmn_document"
SAVE_BPMN_WORKING_COPY_CAPABILITY = "save_bpmn_working_copy"
CREATE_BPMN_REVISION_CAPABILITY = "create_bpmn_revision"
ORGANIZE_BPMN_DOCUMENT_CAPABILITY = "organize_bpmn_document"

BPMN_DOCUMENT_CAPABILITIES = frozenset(
    {
        CREATE_BPMN_DOCUMENT_CAPABILITY,
        SAVE_BPMN_WORKING_COPY_CAPABILITY,
        CREATE_BPMN_REVISION_CAPABILITY,
        ORGANIZE_BPMN_DOCUMENT_CAPABILITY,
    }
)

NATIVE_EXISTS = "NATIVE_BPMN_ALREADY_EXISTS"
NATIVE_NOT_FOUND = "NATIVE_BPMN_NOT_FOUND"
DUAL_MODE = "dual_mode_forbidden"
VERSION_STALE = "VERSION_CONFLICT"


class BpmnDocumentWriteStack(NamedTuple):
    """Composition bundle: canonical write path + read ports.

    Composed at the interface layer (tm_app.infrastructure.
    bpmn_migration_composition) — application never instantiates
    infrastructure. refs is read-only here: it exists solely so the
    canonical native-vs-external XOR can be checked. No port exposes
    legacy diagram persistence."""

    use_case: ProcessBpmnDocumentUseCases
    docs: ProcessBpmnDocumentRepositoryPort
    refs: ProcessBpmnReferenceRepositoryPort
    layout: BpmnLayoutPort


def _raise_http_err(response: Any) -> None:
    """Mirror dispatch_service._raise_http_err for JSONResponse auth denials."""
    if response is None:
        return
    status = getattr(response, "status_code", 200) or 200
    if status < 400:
        return
    raise GovernedWriteError(
        "Access denied for this process.",
        code="FORBIDDEN",
        status_code=status,
    )


def require_prepare_authz(request: Request, processo_id: str) -> None:
    _raise_http_err(check_processo_manage_access(request, processo_id))


def _normalize_processo_id(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        raise GovernedWriteError(
            "processo_id is required.", code=VALIDATION, status_code=400
        )
    try:
        return str(UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise GovernedWriteError(
            "processo_id inválido.", code=VALIDATION, status_code=400
        ) from None


def _require_processo(stack: BpmnDocumentWriteStack, raw: Any) -> str:
    """Same canonical gate as the use case: normalize + existence."""
    processo_id = _normalize_processo_id(raw)
    if not stack.docs.process_exists(processo_id):
        raise GovernedWriteError(
            "Processo não encontrado.", code=NOT_FOUND, status_code=404
        )
    return processo_id


def _require_expected_version(raw: Any) -> int:
    try:
        version = int(raw)
    except (TypeError, ValueError):
        version = 0
    if version < 1:
        raise GovernedWriteError(
            "expected_version is required (canonical If-Match semantics "
            "— read the document first).",
            code=VALIDATION,
            status_code=400,
        )
    return version


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _auto_organize(
    stack: BpmnDocumentWriteStack, xml: str
) -> tuple[str, dict[str, Any]]:
    """Modality B — every structural write authored through the TÉO
    governed surface gets the CANONICAL Organizar pipeline applied to
    its BPMN-DI before sealing. Fallback policy (product decision): a
    layout failure NEVER blocks the write — the unorganized candidate
    is kept and the summary records the reason."""
    try:
        result = stack.layout.organize(xml)
    except BpmnLayoutError as exc:
        return xml, {"applied": False, "reason": str(exc)}
    if not result.changed:
        return xml, {
            "applied": False,
            "reason": "already_organized",
            "moved_elements": 0,
        }
    # Never seal a layout output that broke the artifact — keep the
    # original candidate (semantics are preserved by construction, but
    # the organized XML still goes through the canonical validator).
    check = _validate_candidate_xml(result.xml)
    if not check.get("passed"):
        return xml, {
            "applied": False,
            "reason": "organized_xml_failed_validation",
            "moved_elements": result.moved_elements,
        }
    return result.xml, {
        "applied": True,
        "moved_elements": result.moved_elements,
    }


# ---------------------------------------------------------------------
# PREPARE — shared candidate-XML validation (same pipeline as the
# Portal editor import/save and the migration capability).
# ---------------------------------------------------------------------


def _validate_candidate_xml(xml: str) -> dict[str, Any]:
    """intake_bytes → artifact+evidence → LxmlBpmnValidator, plus the
    canonical MAX_XML_BYTES boundary. Never raises: issues become a
    validation summary so the proposal is sealed ready=false."""
    if len(xml.encode("utf-8")) > MAX_XML_BYTES:
        return {
            "stage": "boundary",
            "passed": False,
            "issues": [
                {
                    "rule_id": "MAX_XML_BYTES",
                    "severity": "error",
                    "message": "Artefato BPMN excede o limite de tamanho.",
                }
            ],
        }
    try:
        intake = intake_bytes(xml.encode("utf-8"))
        if intake.artifact is None:
            return {
                "stage": "intake",
                "passed": False,
                "issues": [
                    {
                        "rule_id": "UNSAFE_ARTIFACT",
                        "severity": "error",
                        "message": "O artefato BPMN enviado não é XML utilizável.",
                    }
                ],
            }
        report = LxmlBpmnValidator().validate(
            intake.artifact, evidence=intake.evidence
        )
        issues = [
            {
                "rule_id": i.rule_id,
                "rule_source": i.source.value,
                "stage": i.stage.value,
                "severity": i.severity.value,
                "message": i.message,
            }
            for i in report.issues
        ]
        blocking = [i for i in issues if i["severity"] == "error"]
        return {
            "evaluated_stages": sorted(
                s.value for s in report.evaluated_stages
            ),
            "issues": issues,
            "blocking_issues": len(blocking),
            "passed": not blocking,
        }
    except Exception as exc:  # validation infra failure → never READY
        return {"stage": "failed", "passed": False, "error": str(exc)}


def _bpmn_state_fingerprint(
    stack: BpmnDocumentWriteStack, processo_id: str
) -> str:
    """Sealable fingerprint: native document presence + version +
    working-copy checksum + external reference presence."""
    doc = stack.docs.get_active(processo_id)
    return fingerprint(
        {
            "processo_id": processo_id,
            "native_document_present": doc is not None,
            "native_version": getattr(doc, "version", None),
            "native_working_copy_sha256": getattr(
                doc, "working_copy_sha256", None
            ),
            "external_reference_present": stack.refs.get_active(processo_id)
            is not None,
        }
    )


def _prepare_create(
    stack: BpmnDocumentWriteStack, processo_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    if stack.docs.has_active(processo_id):
        raise GovernedWriteError(
            "O processo já possui documento BPMN nativo.",
            code=NATIVE_EXISTS,
            status_code=409,
            data={"error_kind": NATIVE_EXISTS},
        )
    if stack.refs.get_active(processo_id) is not None:
        raise GovernedWriteError(
            "O processo referencia um modelo BPMN externo (G5).",
            code=DUAL_MODE,
            status_code=409,
            data={"error_kind": DUAL_MODE},
        )

    xml_arg = str(args.get("xml") or "").strip()
    candidate_xml = xml_arg or None
    candidate_sha = _sha256(candidate_xml) if candidate_xml else None
    bpmn_validation: dict[str, Any] = {"stage": "blank_artifact", "passed": True}
    auto_layout: dict[str, Any] = {"applied": False}
    ready = True
    if candidate_xml is not None:
        bpmn_validation = _validate_candidate_xml(candidate_xml)
        ready = bool(bpmn_validation.get("passed"))
        if ready:
            candidate_xml, auto_layout = _auto_organize(
                stack, candidate_xml
            )
            candidate_sha = _sha256(candidate_xml)
            if auto_layout.get("applied"):
                bpmn_validation = _validate_candidate_xml(candidate_xml)

    return {
        "resource_type": "process_bpmn_document",
        "resource_id": processo_id,
        "current_state_fingerprint": _bpmn_state_fingerprint(
            stack, processo_id
        ),
        "exact_change": {
            "capability": CREATE_BPMN_DOCUMENT_CAPABILITY,
            "processo_id": processo_id,
            "candidate_xml": candidate_xml,
            "candidate_sha256": candidate_sha,
        },
        "validation_result": {
            "ready": ready,
            "bpmn_validation": bpmn_validation,
        },
        "consequential_impact": {
            "persists": True,
            "operation": CREATE_BPMN_DOCUMENT_CAPABILITY,
            "creates_native_bpmn_document": True,
            "creates_bpmn_revision": 0,
            "mutates_legacy": False,
            "writes_to_bpmn_modeler": False,
        },
        "confirmation_requirement": {
            "message": (
                "Um novo documento BPMN nativo será criado como o "
                "mapeamento vigente do processo."
            )
        },
        "expected_postcondition": {
            "type": "native_bpmn_document_created",
            "processo_id": processo_id,
        },
        "meta": {"auto_layout": auto_layout},
    }


def _require_active_doc(stack: BpmnDocumentWriteStack, processo_id: str):
    doc = stack.docs.get_active(processo_id)
    if doc is None:
        raise GovernedWriteError(
            "O processo não possui documento BPMN nativo.",
            code=NATIVE_NOT_FOUND,
            status_code=404,
            data={"error_kind": NATIVE_NOT_FOUND},
        )
    return doc


def _require_version_match(doc: Any, expected_version: int) -> None:
    if int(doc.version) != expected_version:
        raise GovernedWriteError(
            "expected_version diverge da versão vigente do documento; "
            "releia o BPMN antes de preparar a alteração.",
            code=VERSION_STALE,
            status_code=409,
            data={
                "error_kind": VERSION_STALE,
                "current_version": doc.version,
            },
        )


def _prepare_save(
    stack: BpmnDocumentWriteStack, processo_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    doc = _require_active_doc(stack, processo_id)
    xml = str(args.get("xml") or "")
    if not xml.strip():
        raise GovernedWriteError(
            "xml (BPMN 2.0 XML) is required for save_bpmn_working_copy.",
            code=VALIDATION,
            status_code=400,
        )
    expected_version = _require_expected_version(args.get("expected_version"))
    _require_version_match(doc, expected_version)

    candidate_sha = _sha256(xml)
    bpmn_validation = _validate_candidate_xml(xml)
    ready = bool(bpmn_validation.get("passed"))
    auto_layout: dict[str, Any] = {"applied": False}
    if ready:
        xml, auto_layout = _auto_organize(stack, xml)
        candidate_sha = _sha256(xml)
        if auto_layout.get("applied"):
            bpmn_validation = _validate_candidate_xml(xml)

    return {
        "resource_type": "process_bpmn_document",
        "resource_id": processo_id,
        "current_state_fingerprint": _bpmn_state_fingerprint(
            stack, processo_id
        ),
        "exact_change": {
            "capability": SAVE_BPMN_WORKING_COPY_CAPABILITY,
            "processo_id": processo_id,
            "expected_version": expected_version,
            "candidate_xml": xml,
            "candidate_sha256": candidate_sha,
        },
        "validation_result": {
            "ready": ready,
            "bpmn_validation": bpmn_validation,
        },
        "consequential_impact": {
            "persists": True,
            "operation": SAVE_BPMN_WORKING_COPY_CAPABILITY,
            "updates_working_copy": True,
            "version_bump": f"{doc.version} → {doc.version + 1}",
            "creates_bpmn_revision": 0,
            "mutates_legacy": False,
            "writes_to_bpmn_modeler": False,
        },
        "confirmation_requirement": {
            "message": (
                "O working copy do documento BPMN nativo será "
                "substituído (autosave governado, mesma semântica do "
                "editor do Portal)."
            )
        },
        "expected_postcondition": {
            "type": "bpmn_working_copy_saved",
            "processo_id": processo_id,
            "expected_version": expected_version,
        },
        "meta": {"auto_layout": auto_layout},
    }


def _prepare_organize(
    stack: BpmnDocumentWriteStack, processo_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Modality A — explicit 'organize this BPMN' request. Reads the
    active native document, runs the canonical Organizar pipeline and
    seals either the organized candidate or an idempotent no-op."""
    doc = _require_active_doc(stack, processo_id)
    xml = doc.working_copy_xml
    layout_report: dict[str, Any]
    try:
        result = stack.layout.organize(xml)
    except BpmnLayoutError as exc:
        return {
            "resource_type": "process_bpmn_document",
            "resource_id": processo_id,
            "current_state_fingerprint": _bpmn_state_fingerprint(
                stack, processo_id
            ),
            "exact_change": {
                "capability": ORGANIZE_BPMN_DOCUMENT_CAPABILITY,
                "processo_id": processo_id,
                "expected_version": doc.version,
                "candidate_xml": None,
                "candidate_sha256": None,
                "layout_error": str(exc),
            },
            "validation_result": {
                "ready": False,
                "auto_layout": {
                    "applied": False,
                    "reason": str(exc),
                },
            },
            "consequential_impact": {
                "persists": False,
                "operation": ORGANIZE_BPMN_DOCUMENT_CAPABILITY,
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "bpmn_document_organized",
                "processo_id": processo_id,
            },
            "meta": {},
        }

    layout_report = {
        "applied": result.changed,
        "moved_elements": result.moved_elements,
        "reason": None if result.changed else "already_organized",
    }
    if not result.changed:
        # Idempotent no-op: already organized — seal a no-write change.
        return {
            "resource_type": "process_bpmn_document",
            "resource_id": processo_id,
            "current_state_fingerprint": _bpmn_state_fingerprint(
                stack, processo_id
            ),
            "exact_change": {
                "capability": ORGANIZE_BPMN_DOCUMENT_CAPABILITY,
                "processo_id": processo_id,
                "expected_version": doc.version,
                "candidate_xml": None,
                "candidate_sha256": doc.working_copy_sha256,
                "no_op": True,
            },
            "validation_result": {
                "ready": True,
                "auto_layout": layout_report,
            },
            "consequential_impact": {
                "persists": False,
                "operation": ORGANIZE_BPMN_DOCUMENT_CAPABILITY,
                "already_organized": True,
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "bpmn_document_organized",
                "processo_id": processo_id,
                "no_op": True,
            },
            "meta": {},
        }

    organized_xml = result.xml
    bpmn_validation = _validate_candidate_xml(organized_xml)
    ready = bool(bpmn_validation.get("passed"))
    return {
        "resource_type": "process_bpmn_document",
        "resource_id": processo_id,
        "current_state_fingerprint": _bpmn_state_fingerprint(
            stack, processo_id
        ),
        "exact_change": {
            "capability": ORGANIZE_BPMN_DOCUMENT_CAPABILITY,
            "processo_id": processo_id,
            "expected_version": doc.version,
            "candidate_xml": organized_xml if ready else None,
            "candidate_sha256": (
                _sha256(organized_xml) if ready else None
            ),
        },
        "validation_result": {
            "ready": ready,
            "bpmn_validation": bpmn_validation,
            "auto_layout": layout_report,
        },
        "consequential_impact": {
            "persists": True,
            "operation": ORGANIZE_BPMN_DOCUMENT_CAPABILITY,
            "updates_working_copy": True,
            "version_bump": f"{doc.version} → {doc.version + 1}",
            "moves_bpmn_di_only": True,
            "mutates_legacy": False,
            "writes_to_bpmn_modeler": False,
        },
        "confirmation_requirement": {},
        "expected_postcondition": {
            "type": "bpmn_document_organized",
            "processo_id": processo_id,
            "expected_version": doc.version,
        },
        "meta": {},
    }


def _prepare_revision(
    stack: BpmnDocumentWriteStack, processo_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    doc = _require_active_doc(stack, processo_id)
    expected_version = _require_expected_version(args.get("expected_version"))
    _require_version_match(doc, expected_version)

    return {
        "resource_type": "process_bpmn_revision",
        "resource_id": processo_id,
        "current_state_fingerprint": _bpmn_state_fingerprint(
            stack, processo_id
        ),
        "exact_change": {
            "capability": CREATE_BPMN_REVISION_CAPABILITY,
            "processo_id": processo_id,
            "expected_version": expected_version,
            "name": args.get("name"),
            "description": args.get("description"),
            "artifact_sha256": doc.working_copy_sha256,
        },
        "validation_result": {"ready": True, "issues": []},
        "consequential_impact": {
            "persists": True,
            "operation": CREATE_BPMN_REVISION_CAPABILITY,
            "creates_bpmn_revision": 1,
            "revision_origin": "explicit",
            "immutable_checkpoint": True,
            "mutates_working_copy": False,
            "mutates_legacy": False,
        },
        "confirmation_requirement": {
            "message": (
                "Uma revisão imutável do working copy vigente será "
                "registrada (checkpoint explícito, ADR-006)."
            )
        },
        "expected_postcondition": {
            "type": "bpmn_revision_created",
            "processo_id": processo_id,
            "artifact_sha256": doc.working_copy_sha256,
        },
        "meta": {},
    }


def prepare(
    stack: BpmnDocumentWriteStack, request: Request, args: dict[str, Any],
    *, capability: str,
) -> dict[str, Any]:
    """PREPARE — read + validate + seal. Never persists."""
    if capability not in BPMN_DOCUMENT_CAPABILITIES:
        raise GovernedWriteError(
            f"Unsupported BPMN document capability '{capability}'.",
            code=VALIDATION,
            status_code=400,
        )
    raw_pid = _normalize_processo_id(
        args.get("processo_id") or args.get("id")
    )
    require_prepare_authz(request, raw_pid)
    processo_id = _require_processo(stack, raw_pid)

    if capability == CREATE_BPMN_DOCUMENT_CAPABILITY:
        return _prepare_create(stack, processo_id, args)
    if capability == SAVE_BPMN_WORKING_COPY_CAPABILITY:
        return _prepare_save(stack, processo_id, args)
    if capability == ORGANIZE_BPMN_DOCUMENT_CAPABILITY:
        return _prepare_organize(stack, processo_id, args)
    return _prepare_revision(stack, processo_id, args)


def recompute_fingerprint(
    stack: BpmnDocumentWriteStack, change: dict[str, Any]
) -> str:
    """ACT-time re-read of the sealed native-document state."""
    return _bpmn_state_fingerprint(stack, str(change["processo_id"]))


def execute(
    stack: BpmnDocumentWriteStack, request: Request, change: dict[str, Any]
) -> dict[str, Any]:
    """ACT — revalidate AuthZ, then canonical write via the use case."""
    processo_id = str(change["processo_id"])
    require_prepare_authz(request, processo_id)
    capability = str(change.get("capability") or "")
    user = request.state.user
    try:
        if capability == CREATE_BPMN_DOCUMENT_CAPABILITY:
            doc = stack.use_case.create_document(
                user, processo_id, change.get("candidate_xml") or None
            )
            return {"document": doc.to_dict()}
        if capability == SAVE_BPMN_WORKING_COPY_CAPABILITY:
            doc = stack.use_case.save_working_copy(
                user,
                processo_id,
                xml=str(change.get("candidate_xml") or ""),
                expected_version=int(change.get("expected_version") or 0),
            )
            return {"document": doc.to_dict()}
        if capability == ORGANIZE_BPMN_DOCUMENT_CAPABILITY:
            if change.get("no_op"):
                return {
                    "skipped": True,
                    "reason": "already_organized",
                    "processo_id": processo_id,
                }
            doc = stack.use_case.save_working_copy(
                user,
                processo_id,
                xml=str(change.get("candidate_xml") or ""),
                expected_version=int(change.get("expected_version") or 0),
            )
            return {"document": doc.to_dict()}
        if capability == CREATE_BPMN_REVISION_CAPABILITY:
            rev = stack.use_case.create_revision(
                user,
                processo_id,
                expected_version=int(change.get("expected_version") or 0),
                name=change.get("name"),
                description=change.get("description"),
            )
            return {"revision": rev.to_dict()}
    except DualModeConflict as exc:
        kind = str(exc) or DUAL_MODE
        raise GovernedWriteError(
            str(exc), code=DUAL_MODE, status_code=409,
            data={"error_kind": kind},
        ) from exc
    except VersionConflict as exc:
        raise GovernedWriteError(
            str(exc), code=VERSION_STALE, status_code=409,
            data={"error_kind": VERSION_STALE},
        ) from exc
    except UnsafeArtifact as exc:
        raise GovernedWriteError(
            str(exc), code=VALIDATION, status_code=400,
            data={"error_kind": "UNSAFE_ARTIFACT"},
        ) from exc
    except LookupError as exc:
        raise GovernedWriteError(
            str(exc), code=NOT_FOUND, status_code=404
        ) from exc
    raise GovernedWriteError(
        f"Unsupported BPMN document capability '{capability}'.",
        code=VALIDATION,
        status_code=400,
    )


def verify(
    stack: BpmnDocumentWriteStack, change: dict[str, Any], write_result: Any
) -> dict[str, Any]:
    """Authoritative read-back: persisted document/revision must match
    the sealed change exactly, else OUTCOME_VERIFICATION_FAILED."""
    processo_id = str(change["processo_id"])
    capability = str(change.get("capability") or "")
    doc = stack.docs.get_active(processo_id)
    if doc is None:
        raise GovernedWriteError(
            "Read-back: native BPMN document not found.",
            code=OUTCOME_VERIFICATION_FAILED,
            status_code=409,
        )

    if capability in (
        CREATE_BPMN_DOCUMENT_CAPABILITY,
        SAVE_BPMN_WORKING_COPY_CAPABILITY,
        ORGANIZE_BPMN_DOCUMENT_CAPABILITY,
    ):
        sealed_sha = str(change.get("candidate_sha256") or "")
        if sealed_sha and doc.working_copy_sha256 != sealed_sha:
            raise GovernedWriteError(
                "Read-back: working-copy checksum mismatch.",
                code=OUTCOME_VERIFICATION_FAILED,
                status_code=409,
            )
        return {
            "processo_id": processo_id,
            "document_id": doc.id,
            "version": doc.version,
            "working_copy_sha256": doc.working_copy_sha256,
            "verified": True,
            "write_result": write_result,
        }

    if capability == CREATE_BPMN_REVISION_CAPABILITY:
        revision = (write_result or {}).get("revision") or {}
        revision_id = revision.get("revision_id")
        matched = next(
            (
                r
                for r in stack.docs.list_revisions(doc.id)
                if str(getattr(r, "id", "")) == str(revision_id)
            ),
            None,
        )
        if matched is None or matched.artifact_sha256 != str(
            change.get("artifact_sha256") or ""
        ):
            raise GovernedWriteError(
                "Read-back: created revision not found or checksum "
                "mismatch.",
                code=OUTCOME_VERIFICATION_FAILED,
                status_code=409,
            )
        return {
            "processo_id": processo_id,
            "document_id": doc.id,
            "version": doc.version,
            "revision": matched.to_dict(),
            "verified": True,
            "write_result": write_result,
        }

    raise GovernedWriteError(
        "Read-back: unsupported capability.",
        code=OUTCOME_VERIFICATION_FAILED,
        status_code=409,
    )


__all__ = [
    "BPMN_DOCUMENT_CAPABILITIES",
    "BpmnDocumentWriteStack",
    "CREATE_BPMN_DOCUMENT_CAPABILITY",
    "CREATE_BPMN_REVISION_CAPABILITY",
    "ORGANIZE_BPMN_DOCUMENT_CAPABILITY",
    "SAVE_BPMN_WORKING_COPY_CAPABILITY",
    "execute",
    "prepare",
    "recompute_fingerprint",
    "require_prepare_authz",
    "verify",
]
