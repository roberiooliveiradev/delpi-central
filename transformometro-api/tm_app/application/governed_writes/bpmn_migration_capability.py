"""G8 — governed capability: migrate_legacy_diagram_to_native_bpmn.

PREPARE (never persists):
    read process → compose current legacy state (macro + vigentes
    overlays via DiagramaCompositionService — the same "visão vigente"
    the UI derives) → run the pure LegacyFlowchartToBpmnMapper →
    validate the candidate with the shared bpmn_validation pipeline →
    seal the exact change (candidate XML + checksum + legacy source
    fingerprint) into the proposal.

ACT (commit_proposal choke point):
    orchestrator recomputes the source fingerprint → stale → refused;
    fresh XOR revalidation inside MigrateLegacyDiagramToBpmnUseCase →
    native document + Revision 1 (origin='migration') + external
    migration metadata → authoritative read-back verify.

The legacy flowchart_v1, instance_diagram_scope and
revision_diagram_overlay are NEVER mutated. Nothing is written to
bpmn_modeler.* — the artifact stays Transformômetro-owned.
"""

from __future__ import annotations

from typing import Any, NamedTuple

from fastapi import Request

from bpmn_validation import LxmlBpmnValidator, intake_bytes

from tm_app.application.governed_writes.errors import (
    BUSINESS_RULE,
    NOT_FOUND,
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.proposal import fingerprint
from tm_app.application.services.diagram_composition_service import (
    DiagramaCompositionService,
)
from tm_app.application.use_cases.manage_process_bpmn_document import (
    DualModeConflict,
)
from tm_app.application.use_cases.migrate_legacy_diagram_to_bpmn import (
    MigrationExecutionError,
    MigrateLegacyDiagramToBpmnUseCase,
)
from tm_app.domain.diagram.flowchart_v1 import FlowchartValidationError
from tm_app.domain.diagram.legacy_bpmn_migration import (
    STATUS_READY,
    LegacyFlowchartToBpmnMapper,
)
from tm_app.domain.ports.process_bpmn_document_repository_port import (
    ProcessBpmnDocumentRepositoryPort,
)
from tm_app.domain.ports.process_bpmn_migration_repository_port import (
    ProcessBpmnMigrationRepositoryPort,
)
from tm_app.domain.ports.process_bpmn_reference_repository_port import (
    ProcessBpmnReferenceRepositoryPort,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.interface.http.branch_access_http import (
    check_processo_manage_access,
)

MIGRATE_CAPABILITY = "migrate_legacy_diagram_to_native_bpmn"

LEGACY_EMPTY = "LEGACY_DIAGRAM_EMPTY"
NATIVE_EXISTS = "NATIVE_BPMN_ALREADY_EXISTS"
DUAL_MODE = "dual_mode_forbidden"
COMPOSITION_CONFLICT = "LEGACY_COMPOSITION_CONFLICT"
COMPOSITION_INVALID = "LEGACY_COMPOSITION_INVALID"


class MigrationWriteStack(NamedTuple):
    """Composition bundle: canonical write path + read ports.

    Composed at the interface layer (tm_app.infrastructure.
    bpmn_migration_composition) — application never instantiates
    infrastructure.
    """

    use_case: MigrateLegacyDiagramToBpmnUseCase
    docs: ProcessBpmnDocumentRepositoryPort
    refs: ProcessBpmnReferenceRepositoryPort
    migrations: ProcessBpmnMigrationRepositoryPort


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


def _compose_source(processo_id: str) -> dict[str, Any]:
    """Current composed legacy state — base + vigentes overlays."""
    return DiagramaCompositionService().compose_for_processo(processo_id)


def _source_fingerprint(
    stack: MigrationWriteStack, processo_id: str
) -> str:
    """Sealable fingerprint: composed legacy + XOR absence state."""
    composed = _compose_source(processo_id)
    return fingerprint(
        {
            "processo_id": processo_id,
            "legacy": composed.get("flowchart"),
            "applied_revisoes": [
                r.get("revisao_id") for r in composed.get("applied_revisoes") or []
            ],
            # G8-COMP-1 — per-revision contribution hashes keep the seal
            # sensitive to every contributing overlay, including ones whose
            # elements were deduplicated as semantically equivalent.
            "contributions": [
                {
                    "revisao_id": c.get("revisao_id"),
                    "overlay_sha256": c.get("overlay_sha256"),
                }
                for c in composed.get("contributions") or []
            ],
            "native_document_present": stack.docs.has_active(processo_id),
            "external_reference_present": stack.refs.get_active(processo_id)
            is not None,
        }
    )


def require_prepare_authz(request: Request, processo_id: str) -> None:
    _raise_http_err(check_processo_manage_access(request, processo_id))


def prepare(
    stack: MigrationWriteStack, request: Request, args: dict[str, Any]
) -> dict[str, Any]:
    """PREPARE — read + map + report + validate. Never persists."""
    processo_id = str(
        args.get("processo_id") or args.get("id") or ""
    ).strip()
    if not processo_id:
        raise GovernedWriteError(
            "processo_id is required.", code=VALIDATION, status_code=400
        )
    require_prepare_authz(request, processo_id)

    processo = ProcessoRepository().get(processo_id)
    if not processo:
        raise GovernedWriteError(
            "Processo não encontrado.", code=NOT_FOUND, status_code=404
        )
    processo_name = str(
        processo.get("nome_processo") or processo.get("nome") or processo_id
    )

    # ---- XOR gates (fail fast, before any mapping work) -------------------
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

    composed = _compose_source(processo_id)
    flowchart = composed.get("flowchart") or {}
    if not (flowchart.get("nodes") or []):
        raise GovernedWriteError(
            "O processo não possui mapeamento legado para migrar.",
            code=LEGACY_EMPTY,
            status_code=409,
            data={"error_kind": LEGACY_EMPTY},
        )

    source_fp = _source_fingerprint(stack, processo_id)

    # ---- candidate: override (edited preview) or fresh map ----------------
    override_xml = str(args.get("candidate_xml_override") or "").strip()
    resolutions = args.get("resolutions")
    if not isinstance(resolutions, dict):
        resolutions = {}

    source_summary = {
        "processo_id": processo_id,
        "processo_nome": processo_name,
        "applied_revisoes": [
            str(r.get("revisao_id"))
            for r in composed.get("applied_revisoes") or []
        ],
        "base_node_count": composed.get("base_node_count"),
        "composed_at": composed.get("at"),
        "legacy_nodes": len(flowchart.get("nodes") or []),
        "legacy_edges": len(flowchart.get("edges") or []),
        "composition_provenance": composed.get("provenance") or {},
        "contributions": composed.get("contributions") or [],
        "composition_conflicts": composed.get("conflicts") or [],
        "composition_notes": composed.get("composition_notes") or [],
    }

    # G8-COMP-1 — divergent same-id contributions across instances are an
    # explicit composition conflict: block before mapping, report who
    # contributed and how the variants diverge. Never pick a winner.
    composition_conflicts = composed.get("conflicts") or []
    if composition_conflicts:
        candidate_report = {
            "status": "BLOCKED",
            "error_kind": COMPOSITION_CONFLICT,
            "composition_conflicts": composition_conflicts,
            "warnings": [
                "Contribuições legadas com mesmo id e semântica divergente. "
                "Resolva o conflito nas revisões/overlays legados antes de "
                "migrar — a migração não escolhe vencedor."
            ],
        }
        return {
            "resource_type": "process_bpmn_document",
            "resource_id": processo_id,
            "current_state_fingerprint": source_fp,
            "exact_change": {
                "processo_id": processo_id,
                "candidate_xml": None,
                "candidate_sha256": None,
                "legacy_source_fingerprint": source_fp,
                "mapping_report": candidate_report,
                "source_summary": source_summary,
            },
            "validation_result": {
                "ready": False,
                "migration_report": candidate_report,
                "bpmn_validation": {"stage": "composition_conflict", "passed": False},
            },
            "consequential_impact": {
                "persists": False,
                "operation": MIGRATE_CAPABILITY,
                "blocked_by": COMPOSITION_CONFLICT,
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "native_bpmn_created_from_migration",
                "processo_id": processo_id,
            },
            "meta": {
                "applied_revisoes": composed.get("applied_revisoes") or [],
                "base_node_count": composed.get("base_node_count"),
            },
        }

    if override_xml:
        candidate_xml = override_xml
        import hashlib as _h

        candidate_sha = _h.sha256(candidate_xml.encode("utf-8")).hexdigest()
        candidate_report = {
            "status": STATUS_READY,
            "candidate_sha256": candidate_sha,
            "edited_by_user": True,
            "warnings": ["Candidato ajustado manualmente no preview."],
        }
        ready = True
    else:
        try:
            candidate = LegacyFlowchartToBpmnMapper().map(
                flowchart,
                process_name=processo_name,
                resolutions=resolutions,
            )
        except FlowchartValidationError as exc:
            # Composed legacy is structurally invalid — governed BLOCKED
            # instead of a raw validator traceback.
            candidate_xml = None
            candidate_sha = None
            candidate_report = {
                "status": "BLOCKED",
                "error_kind": COMPOSITION_INVALID,
                "warnings": [str(exc)],
            }
            ready = False
        else:
            candidate_xml = candidate.bpmn_xml
            candidate_sha = candidate.checksum_sha256
            candidate_report = candidate.to_report_dict()
            ready = candidate.status == STATUS_READY

    # ---- shared BPMN validation (G7 pipeline) ------------------------------
    # Same canonical intake boundary as manage_process_bpmn_document:
    # intake_bytes → artifact+evidence → validate(artifact, evidence).
    validation_summary: dict[str, Any] = {"stage": "skipped"}
    if candidate_xml is None:
        validation_summary = {
            "stage": "composition_invalid",
            "passed": False,
        }
    else:
        try:
            intake = intake_bytes(candidate_xml.encode("utf-8"))
            if intake.artifact is None:
                validation_summary = {
                    "stage": "intake",
                    "passed": False,
                    "error": "Candidato não é XML BPMN decodificável.",
                }
                ready = False
            else:
                report = LxmlBpmnValidator().validate(
                    intake.artifact, evidence=intake.evidence
                )
                blocking = [
                    i
                    for i in report.issues
                    if getattr(i.severity, "value", i.severity) == "error"
                ]
                validation_summary = {
                    "evaluated_stages": sorted(
                        s.value for s in report.evaluated_stages
                    ),
                    "issues": [
                        {
                            "rule_id": i.rule_id,
                            "rule_source": i.source.value,
                            "stage": i.stage.value,
                            "severity": i.severity.value,
                            "message": i.message,
                        }
                        for i in report.issues
                    ],
                    "blocking_issues": len(blocking),
                    "passed": len(blocking) == 0,
                }
                if blocking:
                    ready = False
        except Exception as exc:  # validation infra failure → never auto-READY
            validation_summary = {
                "stage": "failed",
                "passed": False,
                "error": str(exc),
            }
            ready = False

    return {
        "resource_type": "process_bpmn_document",
        "resource_id": processo_id,
        "current_state_fingerprint": source_fp,
        "exact_change": {
            "processo_id": processo_id,
            "candidate_xml": candidate_xml,
            "candidate_sha256": candidate_sha,
            "legacy_source_fingerprint": source_fp,
            "mapping_report": candidate_report,
            "source_summary": source_summary,
        },
        "validation_result": {
            "ready": ready,
            "migration_report": candidate_report,
            "bpmn_validation": validation_summary,
        },
        "consequential_impact": {
            "persists": True,
            "operation": MIGRATE_CAPABILITY,
            "creates_native_bpmn_document": True,
            "creates_bpmn_revision": 1,
            "revision_origin": "migration",
            "mutates_legacy": False,
            "writes_to_bpmn_modeler": False,
        },
        "confirmation_requirement": {
            "message": (
                "O desenho legado será preservado. O novo BPMN passará a "
                "ser o mapeamento vigente do processo."
            )
        },
        "expected_postcondition": {
            "type": "native_bpmn_created_from_migration",
            "processo_id": processo_id,
        },
        "meta": {
            "applied_revisoes": composed.get("applied_revisoes") or [],
            "base_node_count": composed.get("base_node_count"),
        },
    }


def recompute_fingerprint(
    stack: MigrationWriteStack, change: dict[str, Any]
) -> str:
    """ACT-time re-read of the sealed source state."""
    return _source_fingerprint(stack, str(change["processo_id"]))


def execute(
    stack: MigrationWriteStack, request: Request, change: dict[str, Any]
) -> dict[str, Any]:
    """ACT — revalidate AuthZ, then canonical write via the use case."""
    processo_id = str(change["processo_id"])
    require_prepare_authz(request, processo_id)
    try:
        result = stack.use_case.commit(
            request.state.user,
            processo_id=processo_id,
            candidate_xml=str(change["candidate_xml"]),
            candidate_sha256=str(change["candidate_sha256"]),
            legacy_source_fingerprint=str(change["legacy_source_fingerprint"]),
            mapping_report=dict(change.get("mapping_report") or {}),
            source_summary=dict(change.get("source_summary") or {}),
        )
    except DualModeConflict as exc:
        kind = str(exc) or DUAL_MODE
        raise GovernedWriteError(
            str(exc), code=kind, status_code=409, data={"error_kind": kind}
        ) from exc
    except MigrationExecutionError as exc:
        raise GovernedWriteError(
            str(exc), code=BUSINESS_RULE, status_code=409
        ) from exc
    return result


def verify(
    stack: MigrationWriteStack, change: dict[str, Any], write_result: Any
) -> dict[str, Any]:
    """Authoritative read-back: document + R1 + migration record."""
    if not isinstance(write_result, dict) or not write_result.get("verified"):
        raise GovernedWriteError(
            "Migration not verified by authoritative read-back.",
            code="OUTCOME_VERIFICATION_FAILED",
            status_code=409,
            data={"write_result": write_result},
        )
    read_back = stack.docs.get_active(str(change["processo_id"]))
    if read_back is None:
        raise GovernedWriteError(
            "Migration read-back: document not found.",
            code="OUTCOME_VERIFICATION_FAILED",
            status_code=409,
        )
    if read_back.working_copy_sha256 != str(change["candidate_sha256"]):
        raise GovernedWriteError(
            "Migration read-back: checksum mismatch.",
            code="OUTCOME_VERIFICATION_FAILED",
            status_code=409,
        )
    migration = stack.migrations.latest_for_processo(str(change["processo_id"]))
    return {
        "processo_id": change["processo_id"],
        "document_id": read_back.id,
        "version": read_back.version,
        "working_copy_sha256": read_back.working_copy_sha256,
        "migration": migration,
        "write_result": write_result,
    }
