"""CLARA — governed writes (PREPARE → confirmação humana → ACT).

Padrão TÉO owner-local (CLARA-D04=A), nunca import de domínio alheio:

- PREPARE sela a operação server-side (handle opaco, ator, recurso,
  versão/estado esperado, expiração) — **nunca** persiste estado de
  negócio;
- ACT só executa após confirmação explícita do usuário: revalida
  ator, expiração, estado selado e delega à BFF (repositório canônico)
  que reaplica `access/eligibility/assignment/resource_scope/
  business_rule` fail-closed;
- verificação de pós-condição por read-back; divergência ⇒
  `OUTCOME_VERIFICATION_FAILED`, nunca sucesso afirmado;
- consumo single-use atômico; trilha `mcp/clara` na auditoria.

Sem capability nova de autorização: o executor é sempre o próprio
usuário humano — `actor_sub` do principal autenticado.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    MissingReason,
)
from controllership_finance_app.application.clara.operation_presentation import (
    present_operation,
)
from controllership_finance_app.application.clara.step_up_consent import (
    CONSENT_TYPE_PORTAL_STEP_UP,
    ConsentRequired,
    clara_consent_url,
    proposal_plan_hash,
)
from controllership_finance_app.application.services.closing_document_service import (
    ClosingDocumentService,
)
from controllership_finance_app.application.services.received_documents_service import (
    ReceivedDocumentsService,
)
from controllership_finance_app.infrastructure.persistence.clara_consent_challenge_repository import (
    ClaraConsentChallengeRepository,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    ClaraProposalRepository,
    IdempotencyConflict,
    ProposalExpired,
)
from controllership_finance_app.infrastructure.persistence.closing_catalog_repository import (
    ClosingCatalogRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    ClosingPackageRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    ClosingP3Repository,
)
from controllership_finance_app.infrastructure.persistence.closing_pendency_repository import (
    ClosingPendencyRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
    ClosingValidationRepository,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
)

logger = logging.getLogger(__name__)

_SCHEMA = SCHEMA_NAME

MCP_CHANNEL = "mcp/clara"

PROPOSAL_TTL_SECONDS = 900


class ProposalStale(ChecklistDomainError):
    code = "proposal_stale"
    status = 409


class OutcomeVerificationFailed(ChecklistDomainError):
    code = "outcome_verification_failed"
    status = 502


class SnapshotUnavailable(ChecklistDomainError):
    code = "snapshot_unavailable"
    status = 503


class UnknownCapability(ChecklistDomainError):
    code = "unknown_capability"
    status = 400


class GateUnavailable(ChecklistDomainError):
    code = "gate_unavailable"
    status = 503


class OperationForbidden(ChecklistDomainError):
    code = "forbidden"
    status = 403


def _require(params: dict, name: str) -> Any:
    value = params.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise MissingReason(f"{name} é obrigatório.")
    return value


def _audit_mcp(
    *,
    entity_type: str,
    entity_id: Any,
    competence_id: Any,
    event_type: str,
    actor: str,
    detail: dict,
) -> None:
    """Trilha suplementar na auditoria canônica — marca `mcp/clara`."""
    try:
        with plugins_db_connect() as conn:
            with conn.transaction():
                conn.execute(
                    f"""
                    INSERT INTO {_SCHEMA}.closing_audit_event
                        (entity_type, entity_id, competence_id,
                         event_type, actor_subject, detail)
                    VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                    """,
                    (
                        entity_type,
                        entity_id,
                        competence_id,
                        event_type,
                        actor,
                        json.dumps({**detail, "channel": MCP_CHANNEL}),
                    ),
                )
    except Exception:  # noqa: BLE001 — trilha best-effort, nunca reabre ACT
        logger.warning("clara_audit_write_failed type=%s", event_type)


def _state_present(state: dict) -> bool:
    """True se o snapshot conhece um state/status real do recurso.

    Ids ecoados dos params não provam existência — recurso
    inexistente devolve dict de Nones e é indisponível para
    selagem, não um estado válido.
    """
    for key, value in (state or {}).items():
        if isinstance(value, dict):
            if _state_present(value):
                return True
            continue
        if key in {"state", "status"} and value is not None:
            return True
    return False


class ClaraGovernedWrites:
    """Orquestrador PREPARE/ACT — delega execução aos repositórios canônicos."""

    def __init__(
        self,
        *,
        proposals: ClaraProposalRepository | None = None,
        packages: ClosingPackageRepository | None = None,
        validations: ClosingValidationRepository | None = None,
        checklist: ClosingChecklistRepository | None = None,
        pendencies: ClosingPendencyRepository | None = None,
        p3: ClosingP3Repository | None = None,
        catalogs: ClosingCatalogRepository | None = None,
        documents_service: Any = None,
        received_service: Any = None,
        identity_provider: Any = None,
    ) -> None:
        self._proposals = proposals or ClaraProposalRepository()
        self._packages = packages or ClosingPackageRepository()
        self._validations = validations or ClosingValidationRepository()
        self._checklist = checklist or ClosingChecklistRepository()
        self._pendencies = pendencies or ClosingPendencyRepository()
        self._p3 = p3 or ClosingP3Repository()
        self._catalogs = catalogs or ClosingCatalogRepository()
        self._documents_service = documents_service
        self._received_service = received_service
        self._identity_provider = identity_provider
        self._challenges = ClaraConsentChallengeRepository()

    # -- identidade efetiva do canal (injetada pela interface) --------------

    def _identity(self) -> dict:
        """Identidade/permissions efetivas do chamador — fornecida pela
        camada MCP (request reconstruída + Core). Sem provider, gates
        não-`access` falham fechados."""
        if self._identity_provider is None:
            raise GateUnavailable(
                "Identidade efetiva indisponível para checar o gate "
                "da operação."
            )
        return dict(self._identity_provider() or {})

    def _check_gate(self, capability: str) -> dict:
        """Reaplica o gate de permission da rota Portal equivalente.

        ``access`` já é garantido pelo entry-point MCP; ``manage`` e
        ``dre`` são revalidados na identidade efetiva em PREPARE e ACT.
        """
        spec = self._capability_table()[capability]
        gate = spec.get("gate", "access")
        if gate == "access":
            return {}
        identity = self._identity()
        flag = {
            "manage": bool(identity.get("is_manage")),
            "dre": bool(identity.get("is_dre")),
        }.get(gate, False)
        if not flag:
            raise OperationForbidden(
                "Permission efetiva ausente para a operação."
            )
        return identity

    def _manage_flag(self) -> bool:
        """`is_manage` para repositórios que diferenciam transições
        administrativas — fail-closed quando a identidade é ausente."""
        if self._identity_provider is None:
            return False
        try:
            return bool(self._identity().get("is_manage"))
        except Exception:  # noqa: BLE001 — dúvida ⇒ não é manage
            return False

    def _author_name(self) -> str | None:
        try:
            return self._identity().get("name")
        except Exception:  # noqa: BLE001 — nome é best-effort
            return None

    # -- snapshots para staleness -------------------------------------------

    def _snapshot(self, capability: str, params: dict) -> dict:
        """Estado vigente do recurso no momento do PREPARE."""
        period = params.get("period")
        try:
            if capability in (
                "evidence.decide_version",
                "evidence.decide_item_set",
            ):
                item_key = params.get("item_key")
                if capability == "evidence.decide_version":
                    item_key = self._item_key_of_document(
                        period, params.get("document_id")
                    )
                if item_key is None:
                    return {}
                item = self._item_state(period, item_key)
                return {"item_key": item_key, "item": item}
            if capability == "clarification.resolve":
                cid = params.get("clarification_id")
                if cid is None:
                    return {}
                state = self._clarification_state(period, cid)
                return {
                    "clarification_id": str(cid),
                    "clarification": state,
                }
            if capability in (
                "review.record_decision",
                "clarification.open",
                "package.reopen",
                "package.complement",
                "package.submit_review",
                "package.start_review",
            ):
                version_id = params.get("package_version_id")
                if version_id is None:
                    return {}
                version = self._version_state(period, version_id)
                return {
                    "package_version_id": str(version_id),
                    "version": version,
                }
            if capability in (
                "competence.open",
                "pendency.create",
                "item.create_exceptional",
                "package.assignment_create",
            ):
                return {"competence": self._competence_state(period)}
            if capability in (
                "pendency.claim",
                "pendency.reassign",
                "pendency.transition",
                "pendency.confirm_classification",
            ):
                pid = params.get("pendency_id")
                if pid is None:
                    return {}
                return {
                    "pendency_id": str(pid),
                    "pendency": self._pendency_state(period, pid),
                }
            if capability in (
                "p3.confirm_cutoff",
                "p3.upsert_reconciliation",
                "p3.revalidate",
            ):
                return {"p3": self._p3_state(period)}
            if capability == "package.finalize":
                area = params.get("recipient_area")
                if area is None:
                    return {}
                return {
                    "recipient_area": str(area),
                    "package": self._package_state(period, area),
                }
            if capability == "package.assignment_deactivate":
                aid = params.get("assignment_id")
                if aid is None:
                    return {}
                return {
                    "assignment_id": str(aid),
                    "assignment": self._assignment_state(period, aid),
                }
            if capability in (
                "package.confirm_terminal_rejection",
                "package.revert_terminal_rejection",
            ):
                return {"terminal": self._terminal_state(period)}
            if capability == "item.reverse_decision":
                did = params.get("decision_id")
                if did is None:
                    return {}
                return {
                    "decision_id": str(did),
                    "decision": self._decision_state(period, did),
                }
            if capability in (
                "item.mark_not_applicable",
                "item.revert_not_applicable",
                "item.cancel",
                "item.request_correction",
            ):
                item_key = params.get("item_key")
                if item_key is None:
                    return {}
                return {
                    "item_key": item_key,
                    "item": self._item_state(period, item_key),
                }
            if capability == "item.review_correction":
                cid = params.get("correction_id")
                if cid is None:
                    return {}
                return {
                    "correction_id": str(cid),
                    "correction": self._correction_state(period, cid),
                }
            if capability in (
                "document.post_message",
                "document.cancel",
                "received.post_message",
                "received.create_adjustment",
            ):
                did = params.get("document_id")
                if did is None:
                    return {}
                return {
                    "document_id": str(did),
                    "document": self._document_state(period, did),
                }
            if capability in (
                "document.answer_adjustment",
                "received.confirm_adjustment",
            ):
                rid = params.get("request_id")
                if rid is None:
                    return {}
                return {
                    "request_id": str(rid),
                    "request": self._request_state(period, rid),
                }
            if capability.startswith("catalog.entry_"):
                catalog_key = params.get("catalog_key")
                code = params.get("code")
                if not catalog_key or not code:
                    return {}
                return {
                    "catalog_key": str(catalog_key),
                    "code": str(code),
                    "entry": self._catalog_entry_state(
                        catalog_key, code
                    ),
                }
            if capability == "checklist.draft_create":
                template_id = params.get("template_id")
                if template_id is None:
                    return {}
                return {
                    "template_id": str(template_id),
                    "template": self._template_state(template_id),
                }
            if capability.startswith("checklist."):
                template_id = params.get("template_id")
                version = params.get("version")
                if template_id is None or version is None:
                    return {}
                return {
                    "template_id": str(template_id),
                    "version": self._template_version_state(
                        template_id, version
                    ),
                }
        except ChecklistDomainError:
            raise
        except Exception as exc:  # noqa: BLE001 — fail-closed
            raise SnapshotUnavailable(
                "Snapshot do recurso indisponível — operação bloqueada."
            ) from exc
        raise SnapshotUnavailable(
            "Snapshot do recurso indisponível — operação bloqueada."
        )

    def _item_key_of_document(self, period: str, document_id: Any) -> Any:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT d.snapshot_item_id, i.item_key
                  FROM {_SCHEMA}.closing_document d
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = d.competence_id
                  LEFT JOIN {_SCHEMA}.competence_checklist_item i
                    ON i.snapshot_item_id = d.snapshot_item_id
                 WHERE d.document_id = %s AND mc.period = %s
                """,
                (str(document_id), period),
            ).fetchone()
        return row[1] if row else None

    def _item_state(self, period: str, item_key: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT i.state
                  FROM {_SCHEMA}.competence_checklist_item i
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = i.competence_id
                 WHERE mc.period = %s AND i.item_key = %s
                """,
                (period, item_key),
            ).fetchone()
        return {"state": row[0] if row else None}

    def _version_state(self, period: str, version_id: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT v.status
                  FROM {_SCHEMA}.closing_package_version v
                  JOIN {_SCHEMA}.closing_package p
                    ON p.package_id = v.package_id
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = p.competence_id
                 WHERE v.package_version_id = %s AND mc.period = %s
                 ORDER BY v.version_no DESC LIMIT 1
                """,
                (str(version_id), period),
            ).fetchone()
        return {"status": row[0] if row else None}

    def _clarification_state(
        self, period: str, clarification_id: Any
    ) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT c.state, c.package_version_id
                  FROM {_SCHEMA}.closing_clarification c
                  JOIN {_SCHEMA}.closing_package_version v
                    ON v.package_version_id = c.package_version_id
                  JOIN {_SCHEMA}.closing_package p
                    ON p.package_id = v.package_id
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = p.competence_id
                 WHERE c.clarification_id = %s AND mc.period = %s
                """,
                (str(clarification_id), period),
            ).fetchone()
        return {
            "state": row[0] if row else None,
            "package_version_id": str(row[1]) if row else None,
        }

    def _competence_state(self, period: str) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT status FROM {_SCHEMA}.monthly_competence
                 WHERE period = %s
                """,
                (period,),
            ).fetchone()
        return {"status": row[0] if row else "NOT_OPEN"}

    def _pendency_state(self, period: str, pendency_id: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT p.state, p.revision
                  FROM {_SCHEMA}.closing_pendency p
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = p.competence_id
                 WHERE p.pendency_id = %s AND mc.period = %s
                """,
                (str(pendency_id), period),
            ).fetchone()
        return {
            "state": row[0] if row else None,
            "revision": row[1] if row else None,
        }

    def _document_state(self, period: str, document_id: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT d.state, d.revision
                  FROM {_SCHEMA}.closing_document d
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = d.competence_id
                 WHERE d.document_id = %s AND mc.period = %s
                """,
                (str(document_id), period),
            ).fetchone()
        return {
            "state": row[0] if row else None,
            "revision": row[1] if row else None,
        }

    def _package_state(self, period: str, recipient_area: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT p.status
                  FROM {_SCHEMA}.closing_package p
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = p.competence_id
                 WHERE p.recipient_area = %s AND mc.period = %s
                """,
                (str(recipient_area), period),
            ).fetchone()
        return {"status": row[0] if row else "MISSING"}

    def _assignment_state(self, period: str, assignment_id: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT a.active
                  FROM {_SCHEMA}.closing_review_assignment a
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = a.competence_id
                 WHERE a.assignment_id = %s AND mc.period = %s
                """,
                (str(assignment_id), period),
            ).fetchone()
        return {
            "state": (
                ("ACTIVE" if row[0] else "INACTIVE")
                if row is not None
                else "MISSING"
            )
        }

    def _terminal_state(self, period: str) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT t.state
                  FROM {_SCHEMA}.closing_terminal_rejection t
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = t.competence_id
                 WHERE mc.period = %s
                """,
                (period,),
            ).fetchone()
        return {"state": row[0] if row else "ABSENT"}

    def _decision_state(self, period: str, decision_id: Any) -> dict:
        """Estado aferível da decisão: decisão vigente + já revertida?"""
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT d.decision,
                       EXISTS (
                         SELECT 1 FROM {_SCHEMA}.evidence_decision r
                          WHERE r.reverses_decision_id = d.decision_id
                       )
                  FROM {_SCHEMA}.evidence_decision d
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = d.competence_id
                 WHERE d.decision_id = %s AND mc.period = %s
                """,
                (str(decision_id), period),
            ).fetchone()
        return {
            "state": row[0] if row else None,
            "reversed": row[1] if row else None,
        }

    def _correction_state(self, period: str, correction_id: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT c.status
                  FROM {_SCHEMA}.item_correction c
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = c.competence_id
                 WHERE c.correction_id = %s AND mc.period = %s
                """,
                (str(correction_id), period),
            ).fetchone()
        return {"status": row[0] if row else None}

    def _request_state(self, period: str, request_id: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT r.state
                  FROM {_SCHEMA}.document_adjustment_request r
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = r.competence_id
                 WHERE r.request_id = %s AND mc.period = %s
                """,
                (str(request_id), period),
            ).fetchone()
        return {"state": row[0] if row else None}

    def _p3_state(self, period: str) -> dict:
        with plugins_db_connect() as conn:
            cutoff = conn.execute(
                f"""
                SELECT 1 FROM {_SCHEMA}.closing_cutoff c
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = c.competence_id
                 WHERE mc.period = %s
                """,
                (period,),
            ).fetchone()
            rows = conn.execute(
                f"""
                SELECT r.domain, r.source_state, r.revision
                  FROM {_SCHEMA}.closing_reconciliation r
                  JOIN {_SCHEMA}.monthly_competence mc
                    ON mc.competence_id = r.competence_id
                 WHERE mc.period = %s
                 ORDER BY r.domain
                """,
                (period,),
            ).fetchall()
        return {
            "cutoff": "CONFIRMED" if cutoff else "PENDING",
            "domains": {
                r[0]: {"state": r[1], "revision": r[2]} for r in rows
            },
        }

    def _catalog_entry_state(
        self, catalog_key: Any, code: Any
    ) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT active, revision
                  FROM {_SCHEMA}.closing_catalog_entry
                 WHERE catalog_key = %s AND code = %s
                """,
                (str(catalog_key), str(code)),
            ).fetchone()
        return {
            "state": (
                ("ACTIVE" if row[0] else "INACTIVE")
                if row is not None
                else "ABSENT"
            ),
            "revision": row[1] if row else 0,
        }

    def _template_state(self, template_id: Any) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT 1 FROM {_SCHEMA}.checklist_template
                 WHERE template_id = %s
                """,
                (str(template_id),),
            ).fetchone()
        return {"status": "EXISTS" if row else "MISSING"}

    def _template_version_state(
        self, template_id: Any, version: Any
    ) -> dict:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT status
                  FROM {_SCHEMA}.checklist_template_version
                 WHERE template_id = %s AND version = %s
                """,
                (str(template_id), int(version)),
            ).fetchone()
        return {"status": row[0] if row else "MISSING"}

    # -- read-back independente (S3) ------------------------------------------
    # `verify` confere o shape do retorno; `postcondition` relê o
    # recurso no banco e valida a pós-condição de negócio. Nunca
    # declarar sucesso pelo identificador retornado.

    def _pc_review_decision(self, decision_id: Any) -> bool:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT 1 FROM {_SCHEMA}.closing_review_decision
                 WHERE decision_id = %s
                """,
                (str(decision_id),),
            ).fetchone()
        return row is not None

    def _pc_clarification_state(
        self, clarification_id: Any, expected: str
    ) -> bool:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT state FROM {_SCHEMA}.closing_clarification
                 WHERE clarification_id = %s
                """,
                (str(clarification_id),),
            ).fetchone()
        return bool(row) and row[0] == expected

    # -- capabilities --------------------------------------------------------

    def _capability_table(self) -> dict[str, dict]:
        packages = self._packages
        validations = self._validations
        return {
            "evidence.decide_version": {
                "gate": "manage",
                "resource_type": "closing_document",
                "resource_key": lambda p: str(_require(p, "document_id")),
                "required_params": ("period", "document_id", "decision"),
                "describe": lambda p: (
                    f"{p['decision']} evidência "
                    f"{p.get('document_id')} da competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: validations.decide_version(
                    p["period"],
                    str(p["document_id"]),
                    actor,
                    decision=p["decision"],
                    reason_code=p.get("reason_code"),
                    comment=p.get("comment"),
                    request_scope=p.get("request_scope", "BOTH"),
                ),
                "verify": lambda p, result: result.get("item_state")
                in {"ACCEPTED", "REJECTED", "EXPECTED", "NEEDS_REVIEW",
                    "PARTIAL"},
                "postcondition": lambda p, result, actor: (
                    self._item_state(
                        p["period"],
                        self._item_key_of_document(
                            p["period"], p["document_id"]
                        ),
                    ).get("state")
                    == result.get("item_state")
                ),
            },
            "evidence.decide_item_set": {
                "gate": "manage",
                "resource_type": "competence_checklist_item",
                "resource_key": lambda p: str(_require(p, "item_key")),
                "required_params": ("period", "item_key", "decision"),
                "describe": lambda p: (
                    f"{p['decision']} o conjunto do item "
                    f"{p.get('item_key')} da competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: validations.decide_item_set(
                    p["period"],
                    p["item_key"],
                    actor,
                    decision=p["decision"],
                    reason_code=p.get("reason_code"),
                    comment=p.get("comment"),
                    request_scope=p.get("request_scope", "BOTH"),
                ),
                "verify": lambda p, result: result.get("item_state")
                in {"ACCEPTED", "REJECTED", "EXPECTED", "NEEDS_REVIEW",
                    "PARTIAL"},
                "postcondition": lambda p, result, actor: (
                    self._item_state(p["period"], p["item_key"]).get(
                        "state"
                    )
                    == result.get("item_state")
                ),
            },
            "review.record_decision": {
                "gate": "access",
                "resource_type": "closing_package_version",
                "resource_key": lambda p: str(
                    _require(p, "package_version_id")
                ),
                "required_params": (
                    "period", "package_version_id", "area", "outcome"
                ),
                "describe": lambda p: (
                    f"{p['outcome']} revisão da área {p['area']} na "
                    f"versão {p.get('package_version_id')} da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: packages.record_decision(
                    p["period"],
                    str(p["package_version_id"]),
                    actor=actor,
                    area=p["area"],
                    outcome=p["outcome"],
                    note=p.get("note"),
                    user_groups=groups,
                ),
                "verify": lambda p, result: bool(
                    result.get("decision_id")
                ),
                "postcondition": lambda p, result, actor: (
                    self._pc_review_decision(
                        result.get("decision_id")
                    )
                ),
            },
            "clarification.open": {
                "gate": "access",
                "direct": True,
                "resource_type": "closing_package_version",
                "resource_key": lambda p: str(
                    _require(p, "package_version_id")
                ),
                "required_params": ("period", "package_version_id", "question"),
                "describe": lambda p: (
                    f"abrir esclarecimento na versão "
                    f"{p.get('package_version_id')} da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: packages.open_clarification(
                    p["period"],
                    str(p["package_version_id"]),
                    actor=actor,
                    question=p["question"],
                    area=p.get("area"),
                    user_groups=groups,
                ),
                "verify": lambda p, result: bool(
                    result.get("clarification_id")
                ),
                "postcondition": lambda p, result, actor: (
                    self._pc_clarification_state(
                        result.get("clarification_id"), "OPEN"
                    )
                ),
            },
            "clarification.resolve": {
                "gate": "manage",
                "resource_type": "closing_clarification",
                "resource_key": lambda p: str(
                    _require(p, "clarification_id")
                ),
                "required_params": ("period", "clarification_id", "response"),
                "describe": lambda p: (
                    f"responder esclarecimento "
                    f"{p.get('clarification_id')} da competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: packages.resolve_clarification(
                    p["period"],
                    str(p["clarification_id"]),
                    actor=actor,
                    response=p["response"],
                ),
                "verify": lambda p, result: result.get("state")
                == "RESOLVED",
                "postcondition": lambda p, result, actor: (
                    self._pc_clarification_state(
                        p["clarification_id"], "RESOLVED"
                    )
                ),
            },
            "competence.open": {
                "gate": "access",
                "resource_type": "monthly_competence",
                "resource_key": lambda p: str(_require(p, "period")),
                "required_params": ("period",),
                "describe": lambda p: (
                    f"abrir a competência {p['period']} "
                    "(clonagem do checklist vigente)"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.open_competence(
                        p["period"], actor
                    )[0]
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._competence_state(p["period"]).get("status")
                    == "OPEN"
                ),
            },
            "pendency.create": {
                "gate": "access",
                "direct": True,
                "resource_type": "closing_pendency",
                "resource_key": lambda p: str(_require(p, "title")),
                "required_params": ("period", "kind", "title"),
                "describe": lambda p: (
                    f"criar a pendência «{p['title']}» na competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._pendencies.create_pendency(
                        p["period"],
                        actor=actor,
                        kind=p["kind"],
                        title=p["title"],
                        description=p.get("description"),
                        snapshot_item_id=p.get("snapshot_item_id"),
                        queue=p.get("queue"),
                        responsible_subject=p.get("responsible_subject"),
                        branch_scope=p.get("branch_scope"),
                        suggested_classification=p.get(
                            "suggested_classification"
                        ),
                        suggestion_rationale=p.get(
                            "suggestion_rationale"
                        ),
                        suggestion_source=p.get("suggestion_source"),
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(
                    (result or {}).get("pendency_id")
                    or (result or {}).get("pendency", {}).get(
                        "pendency_id"
                    )
                ),
                "postcondition": lambda p, result, actor: (
                    self._pendency_state(
                        p["period"],
                        (result or {}).get("pendency_id")
                        or (result or {}).get("pendency", {}).get(
                            "pendency_id"
                        ),
                    ).get("state")
                    is not None
                ),
            },
            "pendency.claim": {
                "gate": "access",
                "direct": True,
                "resource_type": "closing_pendency",
                "resource_key": lambda p: str(
                    _require(p, "pendency_id")
                ),
                "required_params": (
                    "period", "pendency_id", "expected_revision"
                ),
                "describe": lambda p: (
                    f"assumir a pendência {p.get('pendency_id')} da "
                    f"competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._pendencies.claim_pendency(
                        p["period"],
                        str(p["pendency_id"]),
                        actor,
                        expected_revision=int(p["expected_revision"]),
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._pendency_state(
                        p["period"], p["pendency_id"]
                    ).get("state")
                    == (result or {}).get("state")
                ),
            },
            "pendency.reassign": {
                "gate": "manage",
                "resource_type": "closing_pendency",
                "resource_key": lambda p: str(
                    _require(p, "pendency_id")
                ),
                "required_params": (
                    "period", "pendency_id", "new_responsible",
                    "expected_revision",
                ),
                "describe": lambda p: (
                    f"reatribuir a pendência {p.get('pendency_id')} "
                    f"para {p.get('new_responsible')} na competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._pendencies.reassign_pendency(
                        p["period"],
                        str(p["pendency_id"]),
                        actor,
                        new_responsible=p["new_responsible"],
                        expected_revision=int(p["expected_revision"]),
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._pendency_state(
                        p["period"], p["pendency_id"]
                    ).get("revision")
                    == (result or {}).get("revision")
                ),
            },
            "pendency.transition": {
                "gate": "access",
                "direct": True,
                "resource_type": "closing_pendency",
                "resource_key": lambda p: str(
                    _require(p, "pendency_id")
                ),
                "required_params": (
                    "period", "pendency_id", "to_state",
                    "expected_revision",
                ),
                "describe": lambda p: (
                    f"mover a pendência {p.get('pendency_id')} para "
                    f"{p.get('to_state')} na competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._pendencies.transition_pendency(
                        p["period"],
                        str(p["pendency_id"]),
                        actor,
                        to_state=p["to_state"],
                        expected_revision=int(p["expected_revision"]),
                        justification=p.get("justification"),
                        notes=p.get("notes"),
                        request_scope=p.get("request_scope", "BOTH"),
                        is_manage=self._manage_flag(),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._pendency_state(
                        p["period"], p["pendency_id"]
                    ).get("state")
                    == p["to_state"]
                ),
            },
            "pendency.confirm_classification": {
                "gate": "manage",
                "resource_type": "closing_pendency",
                "resource_key": lambda p: str(
                    _require(p, "pendency_id")
                ),
                "required_params": (
                    "period", "pendency_id", "classification",
                    "expected_revision",
                ),
                "describe": lambda p: (
                    f"confirmar classificação "
                    f"«{p.get('classification')}» da pendência "
                    f"{p.get('pendency_id')} na competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._pendencies.confirm_classification(
                        p["period"],
                        str(p["pendency_id"]),
                        actor,
                        classification=p["classification"],
                        reason=p.get("reason"),
                        expected_revision=int(p["expected_revision"]),
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._pendency_state(
                        p["period"], p["pendency_id"]
                    ).get("revision")
                    == (result or {}).get("revision")
                ),
            },
            "p3.confirm_cutoff": {
                "gate": "manage",
                "resource_type": "closing_cutoff",
                "resource_key": lambda p: str(_require(p, "period")),
                "required_params": ("period",),
                "describe": lambda p: (
                    f"confirmar o cutoff P3 da competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._p3.confirm_cutoff(
                        p["period"], actor=actor, notes=p.get("notes")
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._p3_state(p["period"]).get("cutoff")
                    == "CONFIRMED"
                ),
            },
            "p3.upsert_reconciliation": {
                "gate": "manage",
                "resource_type": "closing_reconciliation",
                "resource_key": lambda p: (
                    f"{p.get('period')}:{p.get('domain')}"
                ),
                "required_params": ("period", "domain", "source_state"),
                "describe": lambda p: (
                    f"registrar a fonte {p.get('domain')} como "
                    f"{p.get('source_state')} na competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._p3.upsert_reconciliation(
                        p["period"],
                        p["domain"],
                        actor=actor,
                        source_state=p["source_state"],
                        expected_amount=p.get("expected_amount"),
                        reported_amount=p.get("reported_amount"),
                        rule_version=p.get("rule_version"),
                        provenance=p.get("provenance"),
                        provenance_kind=p.get(
                            "provenance_kind", "DECLARED"
                        ),
                        official_document_id=p.get(
                            "official_document_id"
                        ),
                        expected_revision=(
                            int(p["expected_revision"])
                            if p.get("expected_revision") is not None
                            else None
                        ),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._p3_state(p["period"])
                    .get("domains", {})
                    .get(p["domain"], {})
                    .get("state")
                    == p["source_state"]
                ),
            },
            "p3.revalidate": {
                "gate": "manage",
                "resource_type": "closing_revalidation",
                "resource_key": lambda p: str(_require(p, "period")),
                "required_params": ("period",),
                "describe": lambda p: (
                    f"revalidar a conciliação P3 da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._p3.revalidate(
                        p["period"], actor=actor, notes=p.get("notes")
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: bool(result),
            },
            "package.finalize": {
                "gate": "manage",
                "resource_type": "closing_package",
                "resource_key": lambda p: (
                    f"{p.get('period')}:{p.get('recipient_area')}"
                ),
                "required_params": ("period", "recipient_area"),
                "describe": lambda p: (
                    f"finalizar o pacote {p.get('recipient_area')} da "
                    f"competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.finalize_package(
                        p["period"],
                        p["recipient_area"],
                        actor=actor,
                        notes=p.get("notes"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._package_state(
                        p["period"], p["recipient_area"]
                    ).get("status")
                    == "FINALIZED"
                ),
            },
            "package.reopen": {
                "gate": "manage",
                "resource_type": "closing_package_version",
                "resource_key": lambda p: str(
                    _require(p, "package_version_id")
                ),
                "required_params": (
                    "period", "package_version_id", "reason"
                ),
                "describe": lambda p: (
                    f"reabrir a versão {p.get('package_version_id')} da "
                    f"competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.reopen_version(
                        p["period"],
                        str(p["package_version_id"]),
                        actor=actor,
                        reason=p["reason"],
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._version_state(
                        p["period"], p["package_version_id"]
                    ).get("status")
                    == (result or {}).get("status")
                ),
            },
            "package.complement": {
                "gate": "manage",
                "resource_type": "closing_package_version",
                "resource_key": lambda p: str(
                    _require(p, "package_version_id")
                ),
                "required_params": (
                    "period", "package_version_id", "reason"
                ),
                "describe": lambda p: (
                    f"criar complemento da versão "
                    f"{p.get('package_version_id')} da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.create_complement(
                        p["period"],
                        str(p["package_version_id"]),
                        actor=actor,
                        reason=p["reason"],
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: bool(result),
            },
            "package.submit_review": {
                "gate": "manage",
                "resource_type": "closing_package_version",
                "resource_key": lambda p: str(
                    _require(p, "package_version_id")
                ),
                "required_params": (
                    "period", "package_version_id", "expected_revision"
                ),
                "describe": lambda p: (
                    f"submeter a versão {p.get('package_version_id')} "
                    f"à revisão na competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.submit_for_review(
                        p["period"],
                        str(p["package_version_id"]),
                        actor=actor,
                        expected_revision=int(p["expected_revision"]),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._version_state(
                        p["period"], p["package_version_id"]
                    ).get("status")
                    == "SUBMITTED"
                ),
            },
            "package.assignment_create": {
                "gate": "manage",
                "resource_type": "closing_review_assignment",
                "resource_key": lambda p: (
                    f"{p.get('period')}:{p.get('role')}:"
                    f"{p.get('subject')}"
                ),
                "required_params": ("period", "role", "subject"),
                "describe": lambda p: (
                    f"atribuir {p.get('role')} a {p.get('subject')} na "
                    f"competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.assign_actor(
                        p["period"],
                        actor=actor,
                        role=p["role"],
                        subject=p["subject"],
                        recipient_area=p.get("recipient_area"),
                        area=p.get("area"),
                    )
                ),
                "verify": lambda p, result: bool(
                    (result or {}).get("assignment_id")
                ),
                "postcondition": lambda p, result, actor: (
                    self._assignment_state(
                        p["period"], (result or {}).get("assignment_id")
                    ).get("state")
                    == "ACTIVE"
                ),
            },
            "package.assignment_deactivate": {
                "gate": "manage",
                "resource_type": "closing_review_assignment",
                "resource_key": lambda p: str(
                    _require(p, "assignment_id")
                ),
                "required_params": ("period", "assignment_id"),
                "describe": lambda p: (
                    f"desativar a atribuição {p.get('assignment_id')} "
                    f"da competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.deactivate_assignment(
                        p["period"],
                        str(p["assignment_id"]),
                        actor=actor,
                        reason=p.get("reason"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._assignment_state(
                        p["period"], p["assignment_id"]
                    ).get("state")
                    == "INACTIVE"
                ),
            },
            "package.start_review": {
                "gate": "access",
                "resource_type": "closing_package_version",
                "resource_key": lambda p: str(
                    _require(p, "package_version_id")
                ),
                "required_params": ("period", "package_version_id"),
                "describe": lambda p: (
                    f"iniciar a revisão da versão "
                    f"{p.get('package_version_id')} da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.start_review(
                        p["period"],
                        str(p["package_version_id"]),
                        actor=actor,
                        user_groups=groups,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: bool(result),
            },
            "package.confirm_terminal_rejection": {
                "gate": "access",
                "destructive": True,
                "resource_type": "closing_terminal_rejection",
                "resource_key": lambda p: str(_require(p, "period")),
                "required_params": ("period", "reason"),
                "describe": lambda p: (
                    f"confirmar a rejeição terminal da competência "
                    f"{p['period']} (congela revisões)"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.confirm_terminal_rejection(
                        p["period"], actor=actor, reason=p["reason"]
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._terminal_state(p["period"]).get("state")
                    == "ACTIVE"
                ),
            },
            "package.revert_terminal_rejection": {
                "gate": "access",
                "resource_type": "closing_terminal_rejection",
                "resource_key": lambda p: str(_require(p, "period")),
                "required_params": ("period", "reason"),
                "describe": lambda p: (
                    f"reverter a rejeição terminal da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._packages.revert_terminal_rejection(
                        p["period"], actor=actor, reason=p["reason"]
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._terminal_state(p["period"]).get("state")
                    == "REVERTED"
                ),
            },
            "item.reverse_decision": {
                "gate": "manage",
                "resource_type": "evidence_decision",
                "resource_key": lambda p: str(
                    _require(p, "decision_id")
                ),
                "required_params": (
                    "period", "decision_id", "result_state",
                    "justification",
                ),
                "describe": lambda p: (
                    f"reverter a decisão {p.get('decision_id')} para "
                    f"{p.get('result_state')} na competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._validations.reverse_decision(
                        p["period"],
                        str(p["decision_id"]),
                        actor,
                        result_state=p["result_state"],
                        justification=p["justification"],
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._decision_state(
                        p["period"], p["decision_id"]
                    ).get("reversed")
                    is True
                ),
            },
            "item.mark_not_applicable": {
                "gate": "access",
                "direct": True,
                "resource_type": "competence_checklist_item",
                "resource_key": lambda p: str(_require(p, "item_key")),
                "required_params": (
                    "period", "item_key", "justification"
                ),
                "describe": lambda p: (
                    f"marcar o item {p.get('item_key')} como não "
                    f"aplicável na competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._validations.mark_not_applicable(
                        p["period"],
                        p["item_key"],
                        actor,
                        p["justification"],
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._item_state(
                        p["period"], p["item_key"]
                    ).get("state")
                    == "NOT_APPLICABLE"
                ),
            },
            "item.revert_not_applicable": {
                "gate": "access",
                "direct": True,
                "resource_type": "competence_checklist_item",
                "resource_key": lambda p: str(_require(p, "item_key")),
                "required_params": (
                    "period", "item_key", "justification"
                ),
                "describe": lambda p: (
                    f"reverter o não-aplicável do item "
                    f"{p.get('item_key')} na competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._validations.revert_not_applicable(
                        p["period"],
                        p["item_key"],
                        actor,
                        p["justification"],
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._item_state(
                        p["period"], p["item_key"]
                    ).get("state")
                    != "NOT_APPLICABLE"
                ),
            },
            "item.cancel": {
                "gate": "access",
                "destructive": True,
                "resource_type": "competence_checklist_item",
                "resource_key": lambda p: str(_require(p, "item_key")),
                "required_params": (
                    "period", "item_key", "justification"
                ),
                "describe": lambda p: (
                    f"cancelar o item {p.get('item_key')} da "
                    f"competência {p['period']} (irreversível)"
                ),
                "execute": lambda p, actor, groups: (
                    self._validations.cancel_item(
                        p["period"],
                        p["item_key"],
                        actor,
                        p["justification"],
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._item_state(
                        p["period"], p["item_key"]
                    ).get("state")
                    == "CANCELLED"
                ),
            },
            "item.create_exceptional": {
                "gate": "access",
                "resource_type": "competence_checklist_item",
                "resource_key": lambda p: (
                    f"{p.get('period')}:{p.get('sheet')}:"
                    f"{p.get('name')}"
                ),
                "required_params": (
                    "period", "sheet", "name", "justification"
                ),
                "describe": lambda p: (
                    f"criar o item excepcional «{p.get('name')}» "
                    f"({p.get('sheet')}) na competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._validations.create_exceptional_item(
                        p["period"],
                        actor,
                        sheet=p["sheet"],
                        name=p["name"],
                        justification=p["justification"],
                        purpose=p.get("purpose"),
                        origin_kind=p.get("origin_kind", "EXTERNAL"),
                        recipient_area=p.get("recipient_area"),
                        applicability=p.get(
                            "applicability", "REQUIRED"
                        ),
                        branch_scope=p.get("branch_scope", "BOTH"),
                        validation_scope=p.get(
                            "validation_scope", "PER_ATTACHMENT"
                        ),
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: bool(result),
            },
            "item.request_correction": {
                "gate": "access",
                "direct": True,
                "resource_type": "competence_checklist_item",
                "resource_key": lambda p: str(_require(p, "item_key")),
                "required_params": (
                    "period", "item_key", "changes", "justification"
                ),
                "describe": lambda p: (
                    f"solicitar correção do item {p.get('item_key')} "
                    f"na competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._validations.request_correction(
                        p["period"],
                        p["item_key"],
                        actor,
                        changes=p["changes"],
                        justification=p["justification"],
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: bool(result),
            },
            "item.review_correction": {
                "gate": "manage",
                "resource_type": "item_correction",
                "resource_key": lambda p: str(
                    _require(p, "correction_id")
                ),
                "required_params": (
                    "period", "item_key", "correction_id", "approve"
                ),
                "describe": lambda p: (
                    f"{'aprovar' if p.get('approve') else 'rejeitar'} "
                    f"a correção {p.get('correction_id')} do item "
                    f"{p.get('item_key')} na competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._validations.review_correction(
                        p["period"],
                        str(p["correction_id"]),
                        actor,
                        approve=bool(p["approve"]),
                        review_reason=p.get("review_reason"),
                        request_scope=p.get("request_scope", "BOTH"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._correction_state(
                        p["period"], p["correction_id"]
                    ).get("status")
                    in ("APPROVED", "REJECTED")
                ),
            },
            "document.post_message": {
                "gate": "access",
                "direct": True,
                "resource_type": "closing_document",
                "resource_key": lambda p: str(
                    _require(p, "document_id")
                ),
                "required_params": ("period", "document_id", "body"),
                "describe": lambda p: (
                    f"registrar mensagem no documento "
                    f"{p.get('document_id')} da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._docs().post_document_message(
                        period=p["period"],
                        document_id=str(p["document_id"]),
                        actor=actor,
                        author_name=self._author_name(),
                        body=p["body"],
                        idempotency_key=p.get("idempotency_key")
                        or f"clara-{uuid.uuid4().hex}",
                        branch_scope=p.get("branch_scope"),
                        audience=p.get("audience") or "INTERNAL",
                    )[0]
                ),
                "verify": lambda p, result: bool(
                    (result or {}).get("message_id")
                ),
                "postcondition": lambda p, result, actor: (
                    self._pc_message(result.get("message_id"))
                ),
            },
            "document.cancel": {
                "gate": "access",
                "destructive": True,
                "resource_type": "closing_document",
                "resource_key": lambda p: str(
                    _require(p, "document_id")
                ),
                "required_params": (
                    "period", "document_id", "expected_revision"
                ),
                "describe": lambda p: (
                    f"cancelar o documento {p.get('document_id')} da "
                    f"competência {p['period']} (irreversível)"
                ),
                "execute": lambda p, actor, groups: (
                    self._docs().cancel_document(
                        period=p["period"],
                        document_id=str(p["document_id"]),
                        actor=actor,
                        can_manage=self._manage_flag(),
                        expected_revision=int(p["expected_revision"]),
                        branch_scope=p.get("branch_scope"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._document_state(
                        p["period"], p["document_id"]
                    ).get("state")
                    == "CANCELLED"
                ),
            },
            "document.answer_adjustment": {
                "gate": "access",
                "direct": True,
                "resource_type": "document_adjustment_request",
                "resource_key": lambda p: str(
                    _require(p, "request_id")
                ),
                "required_params": (
                    "period", "document_id", "request_id", "answer_body"
                ),
                "describe": lambda p: (
                    f"responder a solicitação {p.get('request_id')} do "
                    f"documento {p.get('document_id')} na competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._docs().answer_adjustment_request(
                        period=p["period"],
                        document_id=str(p["document_id"]),
                        request_id=str(p["request_id"]),
                        actor=actor,
                        answer_name=self._author_name(),
                        answer_body=p["answer_body"],
                        branch_scope=p.get("branch_scope"),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._request_state(
                        p["period"], p["request_id"]
                    ).get("state")
                    == "ANSWERED"
                ),
            },
            "received.post_message": {
                "gate": "dre",
                "direct": True,
                "resource_type": "closing_document",
                "resource_key": lambda p: str(
                    _require(p, "document_id")
                ),
                "required_params": ("period", "document_id", "body"),
                "describe": lambda p: (
                    f"enviar mensagem ao documento recebido "
                    f"{p.get('document_id')} da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._recv().post_message(
                        period=p["period"],
                        document_id=str(p["document_id"]),
                        actor=actor,
                        author_name=self._author_name(),
                        body=p["body"],
                        idempotency_key=p.get("idempotency_key")
                        or f"clara-{uuid.uuid4().hex}",
                    )[0]
                ),
                "verify": lambda p, result: bool(
                    (result or {}).get("message_id")
                ),
                "postcondition": lambda p, result, actor: (
                    self._pc_message(result.get("message_id"))
                ),
            },
            "received.create_adjustment": {
                "gate": "dre",
                "direct": True,
                "resource_type": "document_adjustment_request",
                "resource_key": lambda p: str(
                    _require(p, "document_id")
                ),
                "required_params": ("period", "document_id", "body"),
                "describe": lambda p: (
                    f"abrir solicitação de ajuste no documento "
                    f"recebido {p.get('document_id')} da competência "
                    f"{p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._recv().create_request(
                        period=p["period"],
                        document_id=str(p["document_id"]),
                        actor=actor,
                        author_name=self._author_name(),
                        body=p["body"],
                        idempotency_key=p.get("idempotency_key")
                        or f"clara-{uuid.uuid4().hex}",
                    )[0]
                ),
                "verify": lambda p, result: bool(
                    (result or {}).get("request_id")
                ),
                "postcondition": lambda p, result, actor: (
                    self._request_state(
                        p["period"], result.get("request_id")
                    ).get("state")
                    == "OPEN"
                ),
            },
            "received.confirm_adjustment": {
                "gate": "dre",
                "resource_type": "document_adjustment_request",
                "resource_key": lambda p: str(
                    _require(p, "request_id")
                ),
                "required_params": (
                    "period", "document_id", "request_id"
                ),
                "describe": lambda p: (
                    f"confirmar a solicitação {p.get('request_id')} do "
                    f"documento recebido {p.get('document_id')} na "
                    f"competência {p['period']}"
                ),
                "execute": lambda p, actor, groups: (
                    self._recv().confirm_request(
                        period=p["period"],
                        document_id=str(p["document_id"]),
                        request_id=str(p["request_id"]),
                        actor=actor,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._request_state(
                        p["period"], p["request_id"]
                    ).get("state")
                    == "CONFIRMED"
                ),
            },
            "catalog.entry_create": {
                "gate": "manage",
                "resource_type": "closing_catalog_entry",
                "resource_key": lambda p: (
                    f"{p.get('catalog_key')}:{p.get('code')}"
                ),
                "required_params": ("catalog_key", "code", "label"),
                "describe": lambda p: (
                    f"criar a entrada {p.get('code')} "
                    f"«{p.get('label')}» no catálogo "
                    f"{p.get('catalog_key')}"
                ),
                "execute": lambda p, actor, groups: (
                    self._catalogs.create_entry(
                        p["catalog_key"],
                        code=p["code"],
                        label=p["label"],
                        attributes=p.get("attributes"),
                        effective_from_period=p.get(
                            "effective_from_period"
                        ),
                        actor=actor,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._catalog_entry_state(
                        p["catalog_key"], p["code"]
                    ).get("state")
                    == "ACTIVE"
                ),
            },
            "catalog.entry_update": {
                "gate": "manage",
                "resource_type": "closing_catalog_entry",
                "resource_key": lambda p: (
                    f"{p.get('catalog_key')}:{p.get('code')}"
                ),
                "required_params": (
                    "catalog_key", "code", "expected_revision"
                ),
                "describe": lambda p: (
                    f"atualizar a entrada {p.get('code')} do catálogo "
                    f"{p.get('catalog_key')}"
                ),
                "execute": lambda p, actor, groups: (
                    self._catalogs.update_entry(
                        p["catalog_key"],
                        p["code"],
                        label=p.get("label"),
                        attributes=p.get("attributes"),
                        expected_revision=int(p["expected_revision"]),
                        actor=actor,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._catalog_entry_state(
                        p["catalog_key"], p["code"]
                    ).get("revision")
                    == (result or {}).get("revision")
                ),
            },
            "catalog.entry_deactivate": {
                "gate": "manage",
                "destructive": True,
                "resource_type": "closing_catalog_entry",
                "resource_key": lambda p: (
                    f"{p.get('catalog_key')}:{p.get('code')}"
                ),
                "required_params": (
                    "catalog_key", "code", "expected_revision"
                ),
                "describe": lambda p: (
                    f"desativar a entrada {p.get('code')} do catálogo "
                    f"{p.get('catalog_key')} (reversível por reativação)"
                ),
                "execute": lambda p, actor, groups: (
                    self._catalogs.deactivate_entry(
                        p["catalog_key"],
                        p["code"],
                        expected_revision=int(p["expected_revision"]),
                        actor=actor,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._catalog_entry_state(
                        p["catalog_key"], p["code"]
                    ).get("state")
                    == "INACTIVE"
                ),
            },
            "catalog.entry_reactivate": {
                "gate": "manage",
                "resource_type": "closing_catalog_entry",
                "resource_key": lambda p: (
                    f"{p.get('catalog_key')}:{p.get('code')}"
                ),
                "required_params": ("catalog_key", "code"),
                "describe": lambda p: (
                    f"reativar a entrada {p.get('code')} do catálogo "
                    f"{p.get('catalog_key')}"
                ),
                "execute": lambda p, actor, groups: (
                    self._catalogs.reactivate_entry(
                        p["catalog_key"], p["code"], actor=actor
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._catalog_entry_state(
                        p["catalog_key"], p["code"]
                    ).get("state")
                    == "ACTIVE"
                ),
            },
            "checklist.draft_create": {
                "gate": "manage",
                "direct": True,
                "resource_type": "checklist_template_version",
                "resource_key": lambda p: str(
                    _require(p, "template_id")
                ),
                "required_params": ("template_id",),
                "describe": lambda p: (
                    f"criar rascunho de versão do template "
                    f"{p.get('template_id')}"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.create_draft_version(
                        str(p["template_id"]), actor
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: bool(result),
            },
            "checklist.draft_update": {
                "gate": "manage",
                "direct": True,
                "resource_type": "checklist_template_version",
                "resource_key": lambda p: (
                    f"{p.get('template_id')}:v{p.get('version')}"
                ),
                "required_params": (
                    "template_id", "version", "expected_revision",
                    "items",
                ),
                "describe": lambda p: (
                    f"editar itens do rascunho v{p.get('version')} do "
                    f"template {p.get('template_id')}"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.update_draft_items(
                        str(p["template_id"]),
                        int(p["version"]),
                        int(p["expected_revision"]),
                        list(p["items"]),
                        actor,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: bool(result),
            },
            "checklist.version_submit": {
                "gate": "manage",
                "resource_type": "checklist_template_version",
                "resource_key": lambda p: (
                    f"{p.get('template_id')}:v{p.get('version')}"
                ),
                "required_params": ("template_id", "version"),
                "describe": lambda p: (
                    f"submeter a versão v{p.get('version')} do "
                    f"template {p.get('template_id')} à revisão"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.submit_version_for_review(
                        str(p["template_id"]), int(p["version"]), actor
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._template_version_state(
                        p["template_id"], p["version"]
                    ).get("status")
                    == "IN_REVIEW"
                ),
            },
            "checklist.version_return": {
                "gate": "manage",
                "resource_type": "checklist_template_version",
                "resource_key": lambda p: (
                    f"{p.get('template_id')}:v{p.get('version')}"
                ),
                "required_params": (
                    "template_id", "version", "reason"
                ),
                "describe": lambda p: (
                    f"devolver a versão v{p.get('version')} do "
                    f"template {p.get('template_id')} a rascunho"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.return_version_to_draft(
                        str(p["template_id"]),
                        int(p["version"]),
                        reason=p["reason"],
                        actor=actor,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._template_version_state(
                        p["template_id"], p["version"]
                    ).get("status")
                    == "DRAFT"
                ),
            },
            "checklist.version_discard": {
                "gate": "manage",
                "destructive": True,
                "resource_type": "checklist_template_version",
                "resource_key": lambda p: (
                    f"{p.get('template_id')}:v{p.get('version')}"
                ),
                "required_params": (
                    "template_id", "version", "expected_revision"
                ),
                "describe": lambda p: (
                    f"descartar a versão v{p.get('version')} do "
                    f"template {p.get('template_id')} (irreversível)"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.discard_draft_version(
                        str(p["template_id"]),
                        int(p["version"]),
                        expected_revision=int(p["expected_revision"]),
                        actor=actor,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._template_version_state(
                        p["template_id"], p["version"]
                    ).get("status")
                    == "DISCARDED"
                ),
            },
            "checklist.version_publish": {
                "gate": "manage",
                "resource_type": "checklist_template_version",
                "resource_key": lambda p: (
                    f"{p.get('template_id')}:v{p.get('version')}"
                ),
                "required_params": (
                    "template_id", "version", "effective_from_period"
                ),
                "describe": lambda p: (
                    f"publicar a versão v{p.get('version')} do "
                    f"template {p.get('template_id')} a partir de "
                    f"{p.get('effective_from_period')}"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.publish_version(
                        str(p["template_id"]),
                        int(p["version"]),
                        p["effective_from_period"],
                        actor,
                        allow_empty=bool(p.get("allow_empty", False)),
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._template_version_state(
                        p["template_id"], p["version"]
                    ).get("status")
                    == "PUBLISHED"
                ),
            },
            "checklist.version_inactivate": {
                "gate": "manage",
                "destructive": True,
                "resource_type": "checklist_template_version",
                "resource_key": lambda p: (
                    f"{p.get('template_id')}:v{p.get('version')}"
                ),
                "required_params": ("template_id", "version"),
                "describe": lambda p: (
                    f"inativar a versão v{p.get('version')} do "
                    f"template {p.get('template_id')}"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.inactivate_version(
                        str(p["template_id"]), int(p["version"]), actor
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: (
                    self._template_version_state(
                        p["template_id"], p["version"]
                    ).get("status")
                    == "INACTIVE"
                ),
            },
            "checklist.doc_requirement": {
                "gate": "manage",
                "resource_type": "checklist_template_version",
                "resource_key": lambda p: (
                    f"{p.get('template_id')}:{p.get('item_key')}"
                ),
                "required_params": (
                    "template_id", "item_key", "effective_from",
                    "base_version", "idempotency_key",
                ),
                "describe": lambda p: (
                    f"atualizar o requisito documental do item "
                    f"{p.get('item_key')} do template "
                    f"{p.get('template_id')}"
                ),
                "execute": lambda p, actor, groups: (
                    self._checklist.apply_document_requirement(
                        str(p["template_id"]),
                        p["item_key"],
                        p.get("item"),
                        p["effective_from"],
                        p.get("effective_until"),
                        int(p["base_version"]),
                        bool(p.get("allow_empty", False)),
                        p["idempotency_key"],
                        actor,
                    )
                ),
                "verify": lambda p, result: bool(result),
                "postcondition": lambda p, result, actor: bool(result),
            },
        }

    def _docs(self) -> ClosingDocumentService:
        if self._documents_service is None:
            self._documents_service = ClosingDocumentService()
        return self._documents_service

    def _recv(self) -> ReceivedDocumentsService:
        if self._received_service is None:
            self._received_service = ReceivedDocumentsService()
        return self._received_service

    def _pc_message(self, message_id: Any) -> bool:
        if not message_id:
            return False
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT 1 FROM {_SCHEMA}.document_message
                 WHERE message_id = %s
                """,
                (str(message_id),),
            ).fetchone()
        return row is not None

    def _readback(
        self, spec: dict, payload: dict, result: dict, actor: str
    ) -> bool:
        # Pós-condição por leitura independente do recurso.
        pc = spec.get('postcondition')
        if pc is None:
            return bool(result)
        try:
            return bool(pc(payload, result, actor))
        except ChecklistDomainError:
            raise
        except Exception:  # noqa: BLE001
            return False

    def capabilities(self) -> list[dict]:
        return [
            {
                "capability": name,
                "resource_type": spec["resource_type"],
                "required_params": list(spec["required_params"]),
                "gate": spec.get("gate", "access"),
                "destructive": bool(spec.get("destructive")),
                "direct": bool(spec.get("direct")),
            }
            for name, spec in self._capability_table().items()
        ]

    # -- PREPARE -------------------------------------------------------------

    def prepare(
        self,
        *,
        capability: str,
        params: dict,
        actor_sub: str,
        user_groups: Any = (),
    ) -> dict:
        table = self._capability_table()
        spec = table.get(capability)
        if spec is None:
            raise UnknownCapability(
                f"Capability desconhecida: {capability}."
            )
        for name in spec["required_params"]:
            _require(params, name)
        # Gate de permission efetiva — mesmo nível exigido pela rota
        # Portal equivalente (access já garantido pelo entry-point).
        self._check_gate(capability)
        resource_key = spec["resource_key"](params)
        expected_state = self._snapshot(capability, params)
        if not expected_state or not _state_present(expected_state):
            raise SnapshotUnavailable(
                "Não foi possível selar o estado do recurso — "
                "PREPARE bloqueado."
            )
        handle = uuid.uuid4().hex + uuid.uuid4().hex
        proposal = self._proposals.create(
            handle=handle,
            actor_sub=actor_sub,
            capability=capability,
            resource_type=spec["resource_type"],
            resource_key=resource_key,
            payload=dict(params),
            expected_state=expected_state,
            ttl_seconds=PROPOSAL_TTL_SECONDS,
        )
        expires_at = proposal["expires_at"]
        # R-CLARA-01: desafio de consentimento emitido no PREPARE —
        # vincula ator + plano selado + expiração (V014).
        self._challenges.issue_for_proposal(
            proposal_id=str(proposal["proposal_id"]),
            actor_sub=actor_sub,
            plan_hash=proposal_plan_hash(
                capability, params, expected_state
            ),
            expires_at=expires_at,
        )
        return {
            "proposal_handle": handle,
            "proposal_id": str(proposal["proposal_id"]),
            "capability": capability,
            "resource_type": spec["resource_type"],
            "resource_key": resource_key,
            "operation": spec["describe"](params),
            "presentation": present_operation(capability, params),
            "expected_state": expected_state,
            "execution_policy": "confirm_before_act",
            "confirmation_url": clara_consent_url(
                proposal_id=str(proposal["proposal_id"])
            ),
            "confirmation_instruction": (
                "Apresente a operação exata ao usuário (quem, recurso, "
                "competência, versão, efeito, motivo) e direcione-o à "
                "confirmation_url no Portal Controladoria & Finanças "
                "para consentir. Responder 'sim' no chat NÃO autoriza "
                "a execução — o consentimento é gravado pela página do "
                "Portal com credencial fresca que esta conversa não "
                "consegue produzir. A confirmação não substitui a "
                "autorização efetiva — o backend revalida tudo no ACT."
            ),
            "expires_at": (
                expires_at.isoformat()
                if hasattr(expires_at, "isoformat")
                else expires_at
            ),
            "channel": MCP_CHANNEL,
        }

    # -- ACT ------------------------------------------------------------------

    def commit(
        self,
        *,
        handle: str,
        actor_sub: str,
        user_groups: Any = (),
        correlation_id: str | None = None,
        resume: bool = False,
    ) -> dict:
        sealed = self._proposals.load_any_for_actor(
            handle=handle, actor_sub=actor_sub
        )
        if sealed.get("batch_operation_id") is not None:
            raise ChecklistDomainError(
                "Proposta pertence a um lote — execute pelo "
                "execute_batch com o consentimento consolidado."
            )
        expires_at = sealed["expires_at"]
        if (
            getattr(expires_at, "tzinfo", None) is None
            and hasattr(expires_at, "replace")
        ):
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise ProposalExpired("Proposta expirada.")
        # Reconciliação de CLAIMED/UNKNOWN: retomada nunca repete
        # efeito — lê a pós-condição real antes de decidir.
        if resume:
            recovered = self._reconcile_claimed_proposal(
                proposal=sealed, actor_sub=actor_sub
            )
            if recovered is not None:
                return recovered
        # Claim atômico ANTES de qualquer efeito: duas ACTs simultâneas
        # sobre a mesma proposta têm exatamente um vencedor; a
        # concorrente recebe `proposal_stale`. Posse do handle não
        # autoriza — claim só liga ator+proposta; autorização efetiva é
        # reaplicada pelos repositórios canônicos na execução.
        #
        # Consentimento verificável (Doc 106 §3.1/§3.2): a tool
        # chamada pelo assistente não é prova de consentimento —
        # é exigido consent_record gravado pela superfície BFF de
        # step-up (token Keycloak emitido após o PREPARE). Boolean
        # ou texto do modelo nunca bastam.
        # Revalida o gate no ACT antes do claim — a permission pode
        # ter sido revogada entre PREPARE e execução.
        self._check_gate(sealed["capability"])
        self._require_consent(sealed)
        proposal = self._proposals.claim(
            handle=handle, actor_sub=actor_sub
        )
        capability = proposal["capability"]
        spec = self._capability_table().get(capability)
        if spec is None:
            self._proposals.record_result(
                handle=handle,
                result={"outcome": "failed",
                        "error_code": "unknown_capability"},
            )
            raise UnknownCapability(
                f"Capability desconhecida: {capability}."
            )
        payload = proposal["payload"]

        def _audit(event_type: str, detail: dict) -> None:
            _audit_mcp(
                entity_type=spec["resource_type"],
                entity_id=proposal["resource_key"],
                competence_id=None,
                event_type=event_type,
                actor=actor_sub,
                detail={
                    "capability": capability,
                    "resource_key": proposal["resource_key"],
                    "proposal_id": str(proposal["proposal_id"]),
                    "correlation_id": correlation_id,
                    **detail,
                },
            )

        _audit("CLARA_ACT_ATTEMPT", {})
        # Staleness: o estado vigente deve ser o selado no PREPARE;
        # snapshot indisponível bloqueia (nunca {} aceitável).
        try:
            current = self._snapshot(capability, payload)
        except ChecklistDomainError as exc:
            self._proposals.record_result(
                handle=handle,
                result={"outcome": "failed",
                        "error_code": getattr(exc, "code", "error")},
            )
            _audit("CLARA_ACT_REJECTED",
                   {"error_code": getattr(exc, "code", "error")})
            raise
        if not current or current != proposal["expected_state"]:
            self._proposals.record_result(
                handle=handle,
                result={"outcome": "failed",
                        "error_code": "proposal_stale"},
            )
            _audit("CLARA_ACT_REJECTED",
                   {"error_code": "proposal_stale"})
            raise ProposalStale(
                "O recurso mudou desde o PREPARE — reprepare a "
                "operação a partir do estado atual."
            )
        try:
            result = spec["execute"](payload, actor_sub, user_groups)
        except ChecklistDomainError as exc:
            self._proposals.record_result(
                handle=handle,
                result={"outcome": "failed",
                        "error_code": getattr(exc, "code", "error")},
            )
            _audit("CLARA_ACT_REJECTED",
                   {"error_code": getattr(exc, "code", "error")})
            raise
        if not spec["verify"](payload, result or {}) or not (
            self._readback(spec, payload, result or {}, actor_sub)
        ):
            self._proposals.record_result(
                handle=handle,
                result={"outcome": "unverified"},
            )
            _audit("CLARA_ACT_REJECTED",
                   {"error_code": "outcome_verification_failed"})
            raise OutcomeVerificationFailed(
                "A pós-condição não pôde ser confirmada por leitura."
            )
        self._proposals.record_result(
            handle=handle,
            result={"outcome": "executed", "result": result or {}},
        )
        _audit("CLARA_GOVERNED_ACT", {"outcome": "executed"})
        return {
            "executed": True,
            "capability": capability,
            "resource_type": spec["resource_type"],
            "resource_key": proposal["resource_key"],
            "result": result,
            "channel": MCP_CHANNEL,
        }


    # -- execução direta (DIRECT_ALLOWED — doc 126, SEMANTIC-002) ---------

    _DIRECT_TTL_SECONDS = 120

    def execute_direct(
        self,
        *,
        capability: str,
        params: dict,
        actor_sub: str,
        user_groups: Any = (),
        correlation_id: str | None = None,
    ) -> dict:
        """Executa capability `DIRECT_ALLOWED` em uma única chamada.

        O caminho direto mantém o núcleo governado inteiro — selagem
        de estado, claim atômico, execução pelo caso de uso canônico
        da BFF, pós-condição por read-back independente, auditoria
        mcp/clara — suprimindo apenas o desafio de consentimento. A
        proteção de repetição deixa de ser semântica e vira constraint
        física (V019): mesma (actor, capability, idempotency_key)
        nunca aplica efeito duplicado — retry idêntico devolve o
        resultado verificado já gravado (`replayed`).

        Capabilities sem o marcador `direct` na allowlist tipada são
        rejeitadas com `ConsentRequired` — o caminho governado
        (PREPARE → consentimento Portal → ACT) permanece o único
        possível para elas.
        """
        spec = self._capability_table().get(capability)
        if spec is None:
            raise UnknownCapability(
                f"Capability desconhecida: {capability}."
            )
        if not spec.get("direct"):
            raise ConsentRequired(
                "A operação exige confirmação humana verificável no "
                "Portal — execute via phase=prepare e o ACT com "
                "consentimento registrado."
            )
        for name in spec["required_params"]:
            _require(params, name)
        # Gate de permission efetiva — revalidado na execução (a
        # permission pode ter sido revogada desde a leitura).
        self._check_gate(capability)
        # Idempotência: key explícita do caller ou derivada
        # deterministicamente do plano — chamadas repetidas com o
        # mesmo pedido replayam o resultado verificado sem reexecutar
        # o efeito; pedidos distintos recebem keys distintas.
        idempotency_key = params.get("idempotency_key") or (
            "clara-direct-"
            + proposal_plan_hash(capability, params, {})
        )
        replay = self._replay_result(
            capability=capability,
            spec=spec,
            prior=self._proposals.find_by_idempotency(
                actor_sub=actor_sub,
                capability=capability,
                idempotency_key=idempotency_key,
            ),
            idempotency_key=idempotency_key,
        )
        if replay is not None:
            return replay
        resource_key = spec["resource_key"](params)
        expected_state = self._snapshot(capability, params)
        if not expected_state or not _state_present(expected_state):
            raise SnapshotUnavailable(
                "Não foi possível ler o estado do recurso — "
                "execução bloqueada."
            )
        handle = uuid.uuid4().hex + uuid.uuid4().hex
        try:
            proposal = self._proposals.create(
                handle=handle,
                actor_sub=actor_sub,
                capability=capability,
                resource_type=spec["resource_type"],
                resource_key=resource_key,
                payload=dict(params),
                expected_state=expected_state,
                ttl_seconds=self._DIRECT_TTL_SECONDS,
                idempotency_key=idempotency_key,
            )
        except IdempotencyConflict:
            # Concorrente venceu a inserção — devolve o outcome dela
            # (ou bloqueia honesto se ainda em curso/UNKNOWN).
            replay = self._replay_result(
                capability=capability,
                spec=spec,
                prior=self._proposals.find_by_idempotency(
                    actor_sub=actor_sub,
                    capability=capability,
                    idempotency_key=idempotency_key,
                ),
                idempotency_key=idempotency_key,
            )
            if replay is not None:
                return replay
            raise

        def _audit(event_type: str, detail: dict) -> None:
            _audit_mcp(
                entity_type=spec["resource_type"],
                entity_id=resource_key,
                competence_id=None,
                event_type=event_type,
                actor=actor_sub,
                detail={
                    "capability": capability,
                    "resource_key": resource_key,
                    "proposal_id": str(proposal["proposal_id"]),
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                    **detail,
                },
            )

        _audit("CLARA_DIRECT_ATTEMPT", {})
        # Claim atômico durável — mesmo núcleo do ACT governado.
        self._proposals.claim(handle=handle, actor_sub=actor_sub)
        try:
            result = spec["execute"](params, actor_sub, user_groups)
        except ChecklistDomainError as exc:
            self._proposals.record_result(
                handle=handle,
                result={"outcome": "failed",
                        "error_code": getattr(exc, "code", "error")},
            )
            _audit("CLARA_DIRECT_REJECTED",
                   {"error_code": getattr(exc, "code", "error")})
            raise
        if not spec["verify"](params, result or {}) or not (
            self._readback(spec, params, result or {}, actor_sub)
        ):
            self._proposals.record_result(
                handle=handle,
                result={"outcome": "unverified"},
            )
            _audit("CLARA_DIRECT_REJECTED",
                   {"error_code": "outcome_verification_failed"})
            raise OutcomeVerificationFailed(
                "A pós-condição não pôde ser confirmada por leitura — "
                "o outcome é UNKNOWN; não repita a operação."
            )
        self._proposals.record_result(
            handle=handle,
            result={"outcome": "executed", "result": result or {}},
        )
        _audit("CLARA_DIRECT_ACT", {"outcome": "executed"})
        return {
            "executed": True,
            "capability": capability,
            "resource_type": spec["resource_type"],
            "resource_key": resource_key,
            "result": result,
            "consent": "not_required",
            "idempotency_key": idempotency_key,
            "channel": MCP_CHANNEL,
        }

    def _replay_result(
        self,
        *,
        capability: str,
        spec: dict,
        prior: dict | None,
        idempotency_key: str,
    ) -> dict | None:
        """Interpreta proposta prévia da mesma idempotency_key.

        VERIFIED/APPLIED ⇒ devolve o resultado gravado (efeito único
        já comprovado por read-back). FAILED com erro determinístico ⇒
        propaga o erro tipado — repetir o mesmo plano falharia igual.
        CLAIMED sem resultado ⇒ UNKNOWN honesto, nunca reexecuta.
        Proposta fresca ainda não executada ⇒ concorrência em curso.
        """
        if prior is None:
            return None
        stored = prior.get("result") or {}
        if isinstance(stored, str):
            stored = json.loads(stored)
        outcome = stored.get("outcome")
        if outcome in ("executed", "applied"):
            return {
                "executed": True,
                "replayed": True,
                "capability": capability,
                "resource_type": spec["resource_type"],
                "resource_key": prior.get("resource_key"),
                "result": stored.get("result"),
                "consent": "not_required",
                "idempotency_key": idempotency_key,
                "channel": MCP_CHANNEL,
            }
        if outcome == "failed":
            code = stored.get("error_code") or "error"
            raise ChecklistDomainError(
                f"Execução anterior com esta chave falhou ({code}) — "
                "corrija os parâmetros ou use uma nova chave."
            )
        # CLAIMED sem resultado, UNKNOWN gravado ou proposta ainda em
        # curso: outcome desconhecido é bloqueio honesto — repetir
        # poderia duplicar o efeito.
        raise IdempotencyConflict(
            "Já existe execução em curso ou com outcome não "
            "verificado para esta chave — aguarde ou consulte o "
            "estado antes de repetir."
        )

    # -- consent & reconcile ---------------------------------------------

    _TRUSTED_CONSENT_TYPES = {CONSENT_TYPE_PORTAL_STEP_UP}

    def _require_consent(self, proposal: dict) -> None:
        record = proposal.get("consent_record") or {}
        if isinstance(record, str):
            record = json.loads(record)
        rtype = record.get("type")
        if rtype in self._TRUSTED_CONSENT_TYPES and (
            record.get("confirmed_by") == proposal["actor_sub"]
        ):
            # R-CLARA-01: o consent_record só é prova quando o
            # desafio referenciado existe, foi APROVADO/CONSUMED por
            # superfície confiável e está vinculado a esta proposta,
            # a este ator e a este plano (capability+params+estado).
            payload = proposal["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            plan_hash = record.get("plan_hash") or proposal_plan_hash(
                proposal["capability"],
                payload,
                proposal["expected_state"],
            )
            if self._challenges.verify_proposal_binding(
                challenge_id=record.get("challenge_id"),
                proposal_id=str(proposal["proposal_id"]),
                actor_sub=proposal["actor_sub"],
                plan_hash=plan_hash,
            ):
                return
        raise ConsentRequired(
            "Consentimento humano não registrado por superfície "
            "confiável. Abra a página de consentimento no Portal: "
            + clara_consent_url(
                proposal_id=str(proposal["proposal_id"])
            )
        )

    def _reconcile_claimed_proposal(
        self,
        *,
        proposal: dict,
        actor_sub: str,
    ) -> dict | None:
        """Recuperação pós-falha: CLAIMED pode ter aplicado efeito.

        Se a pós-condição já vale ⇒ VERIFIED (efeito aplicou,
        resultado não gravou); senão ⇒ UNKNOWN terminal e honesto —
        nunca repete efeito nem registra FAILED sem evidência.
        """
        state = proposal.get("execution_state")
        if state != "CLAIMED":
            if state in ("VERIFIED", "APPLIED"):
                return {
                    "executed": True,
                    "capability": proposal["capability"],
                    "resource_type": proposal["resource_type"],
                    "resource_key": proposal["resource_key"],
                    "result": proposal.get("result"),
                    "already_terminal": state,
                    "channel": MCP_CHANNEL,
                }
            # PREPARED/FAILED/UNKNOWN: segue o fluxo normal
            # (claim/erro tipado decide) ou reporta estado.
            if state in ("FAILED", "UNKNOWN"):
                return {
                    "executed": False,
                    "capability": proposal["capability"],
                    "resource_key": proposal["resource_key"],
                    "state": state,
                    "result": proposal.get("result"),
                    "already_terminal": state,
                    "channel": MCP_CHANNEL,
                }
            return None
        spec = self._capability_table().get(proposal["capability"])
        post_ok = False
        if spec is not None and spec.get("postcondition"):
            payload = proposal["payload"]
            last = proposal.get("result") or {}
            if isinstance(last, str):
                last = json.loads(last)
            try:
                post_ok = self._readback(
                    spec, payload, last.get("result") or last, actor_sub
                )
            except Exception:  # noqa: BLE001
                post_ok = False
        outcome = (
            {"outcome": "executed",
             "result": {"reconciled": True}}
            if post_ok
            else {"outcome": "unverified"}
        )
        self._proposals.record_result_by_id(
            proposal_id=str(proposal["proposal_id"]), result=outcome
        )
        _audit_mcp(
            entity_type=proposal["resource_type"],
            entity_id=proposal["resource_key"],
            competence_id=None,
            event_type="CLARA_ACT_RECONCILED",
            actor=actor_sub,
            detail={
                "capability": proposal["capability"],
                "proposal_id": str(proposal["proposal_id"]),
                "postcondition_met": post_ok,
            },
        )
        return {
            "executed": post_ok,
            "capability": proposal["capability"],
            "resource_type": proposal["resource_type"],
            "resource_key": proposal["resource_key"],
            "state": "VERIFIED" if post_ok else "UNKNOWN",
            "reconciled": True,
            "channel": MCP_CHANNEL,
        }
