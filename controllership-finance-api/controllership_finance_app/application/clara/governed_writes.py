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
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    MissingReason,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    ClaraProposalRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    ClosingPackageRepository,
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
    ) -> None:
        self._proposals = proposals or ClaraProposalRepository()
        self._packages = packages or ClosingPackageRepository()
        self._validations = validations or ClosingValidationRepository()

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
            ):
                version_id = params.get("package_version_id")
                if version_id is None:
                    return {}
                version = self._version_state(period, version_id)
                return {
                    "package_version_id": str(version_id),
                    "version": version,
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
        }

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
        return {
            "proposal_handle": handle,
            "capability": capability,
            "resource_type": spec["resource_type"],
            "resource_key": resource_key,
            "operation": spec["describe"](params),
            "expected_state": expected_state,
            "execution_policy": "confirm_before_act",
            "confirmation_instruction": (
                "Apresente a operação exata ao usuário (quem, recurso, "
                "competência, versão, efeito, motivo) e exija uma "
                "confirmação explícita desta operação antes de chamar "
                "commit_proposal. A confirmação não substitui a "
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
    ) -> dict:
        # Claim atômico ANTES de qualquer efeito: duas ACTs simultâneas
        # sobre a mesma proposta têm exatamente um vencedor; a
        # concorrente recebe `proposal_stale`. Posse do handle não
        # autoriza — claim só liga ator+proposta; autorização efetiva é
        # reaplicada pelos repositórios canônicos na execução.
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
