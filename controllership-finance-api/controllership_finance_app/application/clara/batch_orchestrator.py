"""CLARA — orquestração de múltiplas ações (Documento 106).

Fluxo governado:

    USER REQUEST → DISCOVERY → PLAN → PREPARE_BATCH
        → VERIFIED CONSENT → EXECUTE → VERIFY → REPORT

- ``plan_batch`` classifica cada operação pedida como ``viable`` ou
  ``blocked`` (capability desconhecida, params ausentes, snapshot
  indisponível) e resolve o grafo de dependências — dependências
  explícitas + serialização automática de operações sobre o mesmo
  recurso (intenção ordenada do usuário);
- ``prepare_batch`` sela o plano inteiro (hash canônico), cria uma
  proposta governed por operação viável e devolve um resumo único
  para confirmação consolidada — nunca uma confirmação por item;
- ``confirm_batch`` registra o consentimento verificado
  (CONSOLIDATED ou HOST_ATTESTED) vinculado ao ``plan_hash`` exato —
  mudança material do plano exige reprepare;
- ``execute_batch`` reivindica o lote atomicamente, executa em
  ordem topológica, bloqueia dependentes de falhas, continua
  independentes, reconcilia operações CLAIMED em retomada e
  nunca repete efeito UNKNOWN;
- cada operação reusa claim staleness + execução canônica + read-back
  do single-ACT — autorização efetiva segue nos repositórios BFF.

Não existe transação global: cada operação é governada por seu
próprio bounded resource. O lote é um artefato de orquestração,
auditoria e consentimento — não uma promessa de atomicidade.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from typing import Any

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
    MCP_CHANNEL,
    _audit_mcp,
    _state_present,
)
from controllership_finance_app.application.clara.step_up_consent import (
    CONSENT_TYPE_PORTAL_STEP_UP,
    ConsentRequired,
    clara_consent_url,
)
from controllership_finance_app.infrastructure.persistence.clara_batch_repository import (
    BatchActorMismatch,
    BatchTerminal,
    ClaraBatchRepository,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    ClaraProposalRepository,
)

logger = logging.getLogger(__name__)

BATCH_TTL_SECONDS = 1800


class PlanExpansionRejected(ChecklistDomainError):
    code = "plan_expansion_rejected"
    status = 409


class HostAttestationUnavailable(ChecklistDomainError):
    code = "host_attestation_unavailable"
    status = 503


class HostAttestationInvalid(ChecklistDomainError):
    code = "host_attestation_invalid"
    status = 403


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      default=str)


def _plan_hash(operations: list[dict]) -> str:
    canon = [
        {
            "capability": op["capability"],
            "params": op["params"],
            "depends_on": op.get("depends_on", []),
        }
        for op in operations
    ]
    return hashlib.sha256(_canonical(canon).encode()).hexdigest()


class ClaraBatchOrchestrator:
    """Orquestra lotes sobre o executor governed single-op."""

    def __init__(
        self,
        *,
        writes: ClaraGovernedWrites | None = None,
        batches: ClaraBatchRepository | None = None,
        proposals: ClaraProposalRepository | None = None,
    ) -> None:
        self._writes = writes or ClaraGovernedWrites()
        self._proposals = proposals or self._writes._proposals
        self._batches = batches or ClaraBatchRepository()

    # -- PLAN -----------------------------------------------------------

    def plan_batch(
        self, *, operations: list[dict], actor_sub: str
    ) -> dict:
        """Classifica operações e resolve dependências — sem efeitos."""
        table = self._writes._capability_table()
        classified: list[dict] = []
        seen_resources: dict[tuple[str, str], int] = {}
        for idx, raw in enumerate(operations):
            op = {
                "index": idx,
                "capability": str(raw.get("capability") or ""),
                "params": dict(raw.get("params") or {}),
                "depends_on": list(raw.get("depends_on") or []),
            }
            spec = table.get(op["capability"])
            if spec is None:
                op["status"] = "blocked"
                op["block_reason"] = "unknown_capability"
                classified.append(op)
                continue
            missing = [
                n for n in spec["required_params"]
                if op["params"].get(n) in (None, "")
            ]
            if missing:
                op["status"] = "blocked"
                op["block_reason"] = "missing_params"
                op["missing_params"] = missing
                classified.append(op)
                continue
            try:
                resource_key = spec["resource_key"](op["params"])
            except ChecklistDomainError as exc:
                op["status"] = "blocked"
                op["block_reason"] = getattr(exc, "code", "error")
                classified.append(op)
                continue
            op["resource_type"] = spec["resource_type"]
            op["resource_key"] = resource_key
            op["description"] = spec["describe"](op["params"])
            # Snapshot fail-closed por operação: indisponível ⇒ blocked.
            try:
                expected_state = self._writes._snapshot(
                    op["capability"], op["params"]
                )
            except ChecklistDomainError as exc:
                op["status"] = "blocked"
                op["block_reason"] = getattr(
                    exc, "code", "snapshot_unavailable"
                )
                classified.append(op)
                continue
            if not expected_state or not _state_present(
                expected_state
            ):
                op["status"] = "blocked"
                op["block_reason"] = "snapshot_unavailable"
                classified.append(op)
                continue
            op["expected_state"] = expected_state
            # Dependência implícita: mesma resource ⇒ serializa na
            # ordem pedida pelo usuário.
            rkey = (op["resource_type"], resource_key)
            if rkey in seen_resources:
                dep = seen_resources[rkey]
                if dep not in op["depends_on"]:
                    op["depends_on"].append(dep)
            seen_resources[rkey] = idx
            op["status"] = "viable"
            classified.append(op)
        # Ciclo de dependência = plano inválido, fail-closed.
        self._assert_acyclic(classified)
        viable = [op for op in classified if op["status"] == "viable"]
        return {
            "operations": classified,
            "viable_count": len(viable),
            "blocked_count": len(classified) - len(viable),
            "plan_hash": _plan_hash(classified),
        }

    @staticmethod
    def _assert_acyclic(operations: list[dict]) -> None:
        deps = {
            op["index"]: set(op.get("depends_on") or [])
            for op in operations
        }
        state: dict[int, int] = {}

        def visit(i: int, path: list[int]) -> None:
            s = state.get(i, 0)
            if s == 2:
                return
            if s == 1:
                raise ChecklistDomainError(
                    "Plano com ciclo de dependências "
                    f"({'->'.join(map(str, path + [i]))})."
                )
            state[i] = 1
            for d in deps.get(i, ()):
                if d in deps:
                    visit(d, path + [i])
            state[i] = 2

        for i in deps:
            visit(i, [])

    # -- PREPARE_BATCH ---------------------------------------------------

    def prepare_batch(
        self,
        *,
        operations: list[dict],
        actor_sub: str,
        correlation_id: str | None = None,
    ) -> dict:
        plan = self.plan_batch(
            operations=operations, actor_sub=actor_sub
        )
        if plan["viable_count"] == 0:
            raise ChecklistDomainError(
                "Nenhuma operação viável no pedido — revise os "
                "motivos de bloqueio."
            )
        handle = uuid.uuid4().hex + uuid.uuid4().hex
        persisted_ops: list[dict] = []
        op_handles: dict[int, str] = {}
        seq = 0
        for op in plan["operations"]:
            if op["status"] != "viable":
                seq += 1
                continue
            op_handle = uuid.uuid4().hex + uuid.uuid4().hex
            self._proposals.create(
                handle=op_handle,
                actor_sub=actor_sub,
                capability=op["capability"],
                resource_type=op["resource_type"],
                resource_key=op["resource_key"],
                payload=dict(op["params"]),
                expected_state=op["expected_state"],
                ttl_seconds=BATCH_TTL_SECONDS,
            )
            op_handles[op["index"]] = op_handle
            persisted_ops.append(
                {
                    "seq": seq,
                    "idempotency_key": hashlib.sha256(
                        _canonical(
                            {
                                "capability": op["capability"],
                                "params": op["params"],
                                "seq": seq,
                            }
                        ).encode()
                    ).hexdigest()[:32],
                    "capability": op["capability"],
                    "resource_type": op["resource_type"],
                    "resource_key": op["resource_key"],
                    "params": op["params"],
                    "depends_on": op["depends_on"],
                    "proposal_handle": op_handle,
                }
            )
            seq += 1
        batch = self._batches.create_batch(
            handle=handle,
            actor_sub=actor_sub,
            plan=plan,
            plan_hash=plan["plan_hash"],
            operations=persisted_ops,
            ttl_seconds=BATCH_TTL_SECONDS,
            correlation_id=correlation_id,
        )
        _audit_mcp(
            entity_type="clara_batch",
            entity_id=str(batch["batch_id"]),
            competence_id=None,
            event_type="CLARA_BATCH_PREPARED",
            actor=actor_sub,
            detail={
                "plan_hash": plan["plan_hash"],
                "viable": plan["viable_count"],
                "blocked": plan["blocked_count"],
                "correlation_id": correlation_id,
            },
        )
        return {
            "batch_handle": handle,
            "batch_id": str(batch["batch_id"]),
            "plan_hash": plan["plan_hash"],
            "actor": actor_sub,
            "operations": [
                {
                    "index": op["index"],
                    "status": op["status"],
                    "capability": op["capability"],
                    "resource_type": op.get("resource_type"),
                    "resource_key": op.get("resource_key"),
                    "description": op.get("description"),
                    "depends_on": op.get("depends_on", []),
                    "block_reason": op.get("block_reason"),
                }
                for op in plan["operations"]
            ],
            "confirmation_url": clara_consent_url(
                batch_id=str(batch["batch_id"])
            ),
            "consent_instruction": (
                "Apresente UMA confirmação consolidada ao usuário "
                "listando ator, competência, objetos, operações, "
                "motivos, efeitos e dependências — nunca uma "
                "confirmação por operação. Direcione o usuário à "
                "confirmation_url no Portal Controladoria & Finanças "
                "para consentir o plano inteiro: responder 'sim' no "
                "chat NÃO autoriza a execução — o consentimento é "
                "gravado pela página do Portal com credencial fresca "
                "que esta conversa não consegue produzir. O plano "
                "selado não pode ser ampliado."
            ),
            "expires_at": (
                batch["expires_at"].isoformat()
                if hasattr(batch["expires_at"], "isoformat")
                else batch["expires_at"]
            ),
            "channel": MCP_CHANNEL,
        }

    # -- VERIFIED CONSENT --------------------------------------------------

    def confirm_batch(
        self,
        *,
        handle: str,
        actor_sub: str,
        plan_hash: str,
        attestation: dict | None = None,
    ) -> dict:
        """Uma confirmação consolidada, vinculada ao plan_hash exato.

        A chamada MCP NUNCA é, por si, prova de consentimento
        (Doc 106 §3.1). São aceitas duas evidências verificáveis:

        - Modo A (HOST_ATTESTED): assinatura HMAC do host sobre
          ``plan_hash|actor_sub|expires_at`` — texto de modelo ou
          ``confirmed=true`` nunca bastam;
        - Modo B (CONSOLIDATED): ``consent_record`` do tipo
          ``portal_step_up`` já gravado pela superfície BFF de
          consentimento — token Keycloak emitido após o PREPARE,
          credencial que o canal MCP não consegue fabricar.

        Sem evidência válida ⇒ ``consent_required`` com a URL da
        página de consentimento do Portal.
        """
        if attestation is not None:
            consent_record = self._verify_attestation(
                attestation, plan_hash=plan_hash, actor_sub=actor_sub
            )
            updated = self._batches.record_consent(
                handle=handle,
                actor_sub=actor_sub,
                plan_hash=plan_hash,
                mode="HOST_ATTESTED",
                consent_record=consent_record,
            )
            mode = "HOST_ATTESTED"
        else:
            batch = self._batches.load_by_handle(handle=handle)
            if batch["actor_sub"] != actor_sub:
                raise BatchActorMismatch(
                    "Lote pertence a outro ator."
                )
            record = batch.get("consent_record") or {}
            if isinstance(record, str):
                record = json.loads(record)
            trusted = (
                record.get("type") == CONSENT_TYPE_PORTAL_STEP_UP
                and record.get("confirmed_by") == actor_sub
                and record.get("plan_hash") == plan_hash
            )
            if batch["status"] == "CONFIRMED" and trusted:
                updated = {
                    "batch_id": batch["batch_id"],
                    "status": batch["status"],
                    "confirmed_at": batch["confirmed_at"],
                }
                mode = "CONSOLIDATED"
            elif batch["status"] == "CONFIRMED":
                raise ChecklistDomainError(
                    "plan_hash divergente do plano consentido — o "
                    "consentimento consolidado não cobre alterações "
                    "posteriores do plano."
                )
            elif batch["status"] == "PREPARED":
                raise ConsentRequired(
                    "Consentimento humano não registrado por "
                    "superfície confiável. Abra a página de "
                    "consentimento no Portal: "
                    + clara_consent_url(
                        batch_id=str(batch["batch_id"])
                    )
                )
            else:
                raise BatchTerminal(
                    f"Lote em estado {batch['status']} — não "
                    "aceita consentimento."
                )
        _audit_mcp(
            entity_type="clara_batch",
            entity_id=str(updated["batch_id"]),
            competence_id=None,
            event_type="CLARA_BATCH_CONFIRMED",
            actor=actor_sub,
            detail={"consent_mode": mode,
                    "plan_hash": plan_hash},
        )
        return {
            "batch_id": str(updated["batch_id"]),
            "status": updated["status"],
            "consent_mode": mode,
            "confirmed_at": (
                updated["confirmed_at"].isoformat()
                if hasattr(updated["confirmed_at"], "isoformat")
                else updated["confirmed_at"]
            ),
            "channel": MCP_CHANNEL,
        }

    @staticmethod
    def _verify_attestation(
        attestation: dict, *, plan_hash: str, actor_sub: str
    ) -> dict:
        """Contrato físico Modo A — HMAC host→servidor.

        Payload: {plan_hash, actor_sub, expires_at, signature} onde
        ``signature = HMAC(CLARA_HOST_ATTESTATION_SECRET,
        "plan_hash|actor_sub|expires_at")``. Sem segredo configurado
        a atestação não é verificável ⇒ fail-closed 503. O mecanismo
        físico exige aprovação de Segurança/Plataforma (Doc 106 §4).
        """
        secret = os.environ.get("CLARA_HOST_ATTESTATION_SECRET")
        if not secret:
            raise HostAttestationUnavailable(
                "Atestação de host não configurada neste ambiente — "
                "use confirmação consolidada."
            )
        from datetime import datetime as _dt, timezone as _tz

        expires_at = attestation.get("expires_at")
        try:
            exp = _dt.fromisoformat(str(expires_at))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=_tz.utc)
        except (TypeError, ValueError) as exc:
            raise HostAttestationInvalid(
                "Atestação sem expires_at válido."
            ) from exc
        if exp < _dt.now(_tz.utc):
            raise HostAttestationInvalid("Atestação expirada.")
        if attestation.get("plan_hash") != plan_hash:
            raise HostAttestationInvalid(
                "Atestação não corresponde ao plano selado."
            )
        if attestation.get("actor_sub") != actor_sub:
            raise HostAttestationInvalid(
                "Atestação não corresponde ao ator autenticado."
            )
        payload = (
            f"{plan_hash}|{actor_sub}|{expires_at}"
        ).encode()
        expected = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(
            expected, str(attestation.get("signature") or "")
        ):
            raise HostAttestationInvalid(
                "Assinatura de atestação inválida."
            )
        return {
            "type": "host_attested_intent",
            "plan_hash": plan_hash,
            "actor_sub": actor_sub,
            "expires_at": expires_at,
        }

    # -- EXECUTE -----------------------------------------------------------

    def execute_batch(
        self,
        *,
        handle: str,
        actor_sub: str,
        user_groups: Any = (),
        correlation_id: str | None = None,
        resume: bool = False,
    ) -> dict:
        # Sem resume=True, só a transição CONFIRMED→EXECUTING vence;
        # uma segunda execução concorrente é rejeitada (único
        # corredor). Com resume, reentra para reconciliar CLAIMED/
        # UNKNOWN e continuar PREPARED — operações nunca repetem
        # efeito desconhecido.
        batch = self._batches.claim_batch_for_execution(
            handle=handle, actor_sub=actor_sub, resume=resume
        )
        batch_id = str(batch["batch_id"])
        ops = self._batches.list_operations(batch_id=batch_id)
        plan = batch["plan"]
        # Bloqueadas no PLANO ficam BLOCKED (linhas persistidas? não —
        # só viáveis viraram linha; bloqueadas reportamos do plano).
        op_state: dict[int, str] = {}
        index_by_seq: dict[int, int] = {}
        plan_ops = {
            op["index"]: op
            for op in (plan or {}).get("operations", [])
        }
        for row in ops:
            index_by_seq[row["seq"]] = row["seq"]

        results: list[dict] = []
        table = self._writes._capability_table()

        def dep_ok(row: dict) -> bool:
            # depends_on guarda índices do plano; seq == índice
            # (contador percorre a lista inteira, viáveis e
            # bloqueadas, em ordem).
            deps = row.get("depends_on") or []
            if isinstance(deps, str):
                deps = json.loads(deps)
            return all(
                op_state.get(int(d)) == "VERIFIED" for d in deps
            )

        for row in ops:
            seq = row["seq"]
            if not dep_ok(row):
                self._batches.set_operation_state(
                    operation_id=str(row["operation_id"]),
                    state="BLOCKED",
                    error_code="dependency_failed",
                )
                op_state[seq] = "BLOCKED"
                results.append(
                    self._op_result(
                        row, "BLOCKED", "dependency_failed"
                    )
                )
                continue
            # Retomada: operação CLAIMED de execução anterior —
            # reconciliar por read-back, nunca repetir efeito cego.
            if row["state"] in ("CLAIMED",):
                resolved = self._reconcile_claimed(
                    row, table, actor_sub, user_groups
                )
                op_state[seq] = resolved["state"]
                results.append(resolved)
                continue
            if row["state"] != "PREPARED":
                op_state[seq] = row["state"]
                results.append(
                    self._op_result(row, row["state"], row.get(
                        "error_code"))
                )
                continue
            results.append(
                self._execute_operation(
                    row, table, actor_sub, user_groups,
                    batch_id=batch_id,
                )
            )
            op_state[seq] = results[-1]["state"]

        # Operações bloqueadas no plano (sem linha persistida)
        for op in plan_ops.values():
            if op.get("status") == "blocked":
                results.append(
                    {
                        "index": op["index"],
                        "capability": op["capability"],
                        "state": "BLOCKED",
                        "error_code": op.get("block_reason"),
                        "description": op.get("description"),
                    }
                )
        summary = {
            "executed": sum(
                1 for r in results if r["state"] == "VERIFIED"
            ),
            "failed": sum(
                1 for r in results if r["state"] == "FAILED"
            ),
            "blocked": sum(
                1 for r in results if r["state"] == "BLOCKED"
            ),
            "unknown": sum(
                1 for r in results if r["state"] == "UNKNOWN"
            ),
            "total": len(results),
        }
        finished = self._batches.finish_batch(
            batch_id=batch_id,
            result={"summary": summary, "operations": results},
        )
        _audit_mcp(
            entity_type="clara_batch",
            entity_id=batch_id,
            competence_id=None,
            event_type="CLARA_BATCH_EXECUTED",
            actor=actor_sub,
            detail={
                "plan_hash": batch["plan_hash"],
                "summary": summary,
                "correlation_id": correlation_id,
            },
        )
        return {
            "batch_id": batch_id,
            "status": finished["status"],
            "summary": summary,
            "operations": results,
            "channel": MCP_CHANNEL,
        }

    def _execute_operation(
        self,
        row: dict,
        table: dict,
        actor_sub: str,
        user_groups: Any,
        *,
        batch_id: str,
    ) -> dict:
        op_id = str(row["operation_id"])
        try:
            self._batches.claim_operation(operation_id=op_id)
        except ChecklistDomainError:
            # Outro executor venceu a corrida — reportar o estado
            # observado, nunca sobrescrever o resultado dele.
            observed = self._observed_state(row)
            return self._op_result(
                row, observed or "UNKNOWN", "claim_lost"
            )
        capability = row["capability"]
        spec = table.get(capability)
        try:
            if spec is None:
                raise ChecklistDomainError("Capability desconhecida.")
            # Claim durável da proposta ANTES do efeito.
            proposal = self._proposals.claim_by_id(
                proposal_id=str(row["proposal_id"]),
                actor_sub=actor_sub,
            )
            payload = proposal["payload"]
            current = self._writes._snapshot(capability, payload)
            if not current or current != proposal["expected_state"]:
                self._finish_op_proposal(
                    row, {"outcome": "failed",
                          "error_code": "proposal_stale"}
                )
                self._batches.set_operation_state(
                    operation_id=op_id,
                    state="FAILED",
                    error_code="proposal_stale",
                )
                return self._op_result(row, "FAILED",
                                       "proposal_stale")
            result = spec["execute"](
                payload, actor_sub, user_groups
            )
            if not spec["verify"](payload, result or {}) or not (
                self._writes._readback(
                    spec, payload, result or {}, actor_sub
                )
            ):
                self._finish_op_proposal(
                    row, {"outcome": "unverified"}
                )
                self._batches.set_operation_state(
                    operation_id=op_id,
                    state="UNKNOWN",
                    error_code="outcome_verification_failed",
                    result={"result": result},
                )
                return self._op_result(
                    row, "UNKNOWN",
                    "outcome_verification_failed",
                )
            self._finish_op_proposal(
                row, {"outcome": "executed",
                      "result": result or {}}
            )
            self._batches.set_operation_state(
                operation_id=op_id,
                state="VERIFIED",
                result={"result": result},
            )
            _audit_mcp(
                entity_type=row["resource_type"],
                entity_id=row["resource_key"],
                competence_id=None,
                event_type="CLARA_BATCH_OP_EXECUTED",
                actor=actor_sub,
                detail={
                    "batch_id": batch_id,
                    "capability": capability,
                    "operation_id": op_id,
                    "outcome": "verified",
                },
            )
            return {
                "seq": row["seq"],
                "capability": capability,
                "resource_key": row["resource_key"],
                "state": "VERIFIED",
                "result": result,
            }
        except ChecklistDomainError as exc:
            code = getattr(exc, "code", "error")
            self._finish_op_proposal(
                row, {"outcome": "failed", "error_code": code}
            )
            self._batches.set_operation_state(
                operation_id=op_id,
                state="FAILED",
                error_code=code,
            )
            _audit_mcp(
                entity_type=row["resource_type"],
                entity_id=row["resource_key"],
                competence_id=None,
                event_type="CLARA_BATCH_OP_FAILED",
                actor=actor_sub,
                detail={
                    "batch_id": batch_id,
                    "capability": capability,
                    "operation_id": op_id,
                    "error_code": code,
                },
            )
            return self._op_result(row, "FAILED", code)
        except Exception as exc:  # noqa: BLE001 — falha de infra
            logger.exception(
                "clara_batch_op_infra_failed op=%s", op_id
            )
            self._finish_op_proposal(
                row, {"outcome": "failed",
                      "error_code": "internal_error"}
            )
            self._batches.set_operation_state(
                operation_id=op_id,
                state="FAILED",
                error_code="internal_error",
            )
            return self._op_result(row, "FAILED",
                                   "internal_error")

    def _observed_state(self, row: dict) -> str | None:
        try:
            ops = self._batches.list_operations(
                batch_id=str(row["batch_id"])
            )
            for op in ops:
                if str(op["operation_id"]) == str(
                    row["operation_id"]
                ):
                    return op["state"]
        except ChecklistDomainError:
            return None
        return None

    def _reconcile_claimed(
        self,
        row: dict,
        table: dict,
        actor_sub: str,
        user_groups: Any,
    ) -> dict:
        """Operação CLAIMED numa execução anterior: efeito desconhecido.

        Re-lê a pós-condição; se já satisfeita ⇒ VERIFIED (efeito
        aplicou, estado não gravou); senão ⇒ UNKNOWN e não repete —
        o relatório exige intervenção humana.
        """
        spec = table.get(row["capability"])
        op_id = str(row["operation_id"])
        if spec is not None:
            params = row["params"]
            if isinstance(params, str):
                params = json.loads(params)
            try:
                # Read-back direto: se a pós-condição esperada já
                # vale, o efeito aplicou antes da interrupção —
                # mesmo sem result gravado (falha antes do status).
                last = self._proposals_result(row)
                post_ok = self._writes._readback(
                    spec, params, last or {}, actor_sub
                )
                if post_ok:
                    self._batches.set_operation_state(
                        operation_id=op_id, state="VERIFIED",
                        result={"result": last},
                    )
                    return {
                        "seq": row["seq"],
                        "capability": row["capability"],
                        "resource_key": row["resource_key"],
                        "state": "VERIFIED",
                        "result": last,
                        "reconciled": True,
                    }
            except ChecklistDomainError:
                pass
        self._batches.set_operation_state(
            operation_id=op_id, state="UNKNOWN",
            error_code="outcome_unknown",
        )
        return self._op_result(row, "UNKNOWN", "outcome_unknown")

    def _proposals_result(self, row: dict) -> dict | None:
        """Último resultado conhecido do execute (para reconcile)."""
        result = row.get("result")
        if isinstance(result, str):
            result = json.loads(result)
        if isinstance(result, dict):
            return result.get("result")
        return None

    def _finish_op_proposal(self, row: dict, result: dict) -> None:
        try:
            self._proposals.record_result_by_id(
                proposal_id=str(row["proposal_id"]), result=result
            )
        except ChecklistDomainError:
            pass

    @staticmethod
    def _op_result(
        row: dict, state: str, error_code: str | None
    ) -> dict:
        return {
            "seq": row["seq"],
            "capability": row.get("capability"),
            "resource_key": row.get("resource_key"),
            "state": state,
            "error_code": error_code,
        }

    # -- status -------------------------------------------------------------

    def batch_status(self, *, batch_id: str, actor_sub: str) -> dict:
        batch = self._batches.get_batch(batch_id=batch_id)
        if batch["actor_sub"] != actor_sub:
            raise BatchActorMismatch(
                "Lote pertence a outro ator."
            )
        return {
            "batch_id": batch_id,
            "status": batch["status"],
            "plan_hash": batch["plan_hash"],
            "consent_mode": batch["consent_mode"],
            "result": batch.get("result"),
            "operations": [
                {
                    "seq": op["seq"],
                    "capability": op["capability"],
                    "state": op["state"],
                    "error_code": op.get("error_code"),
                }
                for op in batch["operations"]
            ],
            "channel": MCP_CHANNEL,
        }
