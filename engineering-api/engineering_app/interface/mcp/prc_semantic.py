"""Handlers semânticos EVA — Product Registration (PRC-C4).

Módulo isolado: os handlers despacham ``(entity, action)`` ao MESMO
``ProductRegistrationService`` das rotas REST — sem lógica duplicada,
sem URL/SQL/função arbitrária do modelo. A integração em
``semantic_bridge.py`` é apenas o registro nos dispatch maps.

Ator: sempre o humano autenticado (``context.user``) — nunca o modelo,
nunca identidade fornecida em payload. ``channel="eva"`` é auditado.

Terminais (reject, verify_and_complete): PREPARE sela proposta
(ator/alvo/versão/efeito) → ACT exige ``proposal_ref`` + confirmação
humana verificável via elicitation; verify executa a leitura oficial
TOTVS no ACT — confirmar não substitui a prova oficial.
"""

from __future__ import annotations

from typing import Any

from engineering_app.application.eva.proposal_store import (
    fingerprint,
    get_proposal_store,
    load_valid_proposal,
    seal_proposal,
)
from engineering_app.application.use_cases.product_registration.actor import (
    prc_actor_from_principal,
)
from engineering_app.composition.prc_composer import build_prc_service


def _actor(context):
    return prc_actor_from_principal(context.user, channel="eva")


def _err(message: str, *, code: str = "validation", status: int = 400,
         data: dict | None = None):
    from engineering_app.interface.mcp.semantic_bridge import _err as _e

    return _e(message, status_code=status, code=code, data=data or {})


def _ok(data: dict, message: str):
    from engineering_app.interface.mcp.semantic_bridge import _ok as _o

    return _o(data, message)


_MAP_DOMAIN = {
    "PrcNotFoundError": ("not_found", 404),
    "PrcValidationError": ("validation", 422),
    "PrcUnverifiableFieldError": ("unverifiable_field", 422),
    "PrcConcurrencyError": ("stale_version", 409),
    "PrcStaleRevisionError": ("stale_version", 409),
    "PrcStateConflictError": ("state_conflict", 409),
    "PrcForbiddenError": ("forbidden", 403),
    "PrcDuplicateError": ("duplicate_external_reference", 409),
    "PrcRepositoryError": ("unavailable", 503),
    "PrcOfficialError": ("official_error", 409),
    "EvaProposalError": ("proposal_error", 400),
}


def _domain_err(exc: Exception):
    kind = type(exc).__name__
    code, status = _MAP_DOMAIN.get(kind, ("internal", 500))
    data: dict[str, Any] = {}
    if kind == "PrcOfficialError":
        data["official_kind"] = getattr(exc, "kind", None)
        data["verification"] = getattr(exc, "verification", None)
        data["field_results"] = getattr(exc, "field_results", None)
        status = {
            "not_found": 409, "mismatch": 409, "unverifiable": 422,
            "forbidden": 403, "unavailable": 503, "timeout": 504,
        }.get(getattr(exc, "kind", ""), 502)
    return _err(str(exc), code=code, status=status, data=data)


# --- READ ------------------------------------------------------------------


async def read_action(context, entry, args: dict):
    """READ dispatch → mesmo use case da REST (escopo+AuthZ no service)."""
    svc = build_prc_service()
    actor = _actor(context)
    try:
        if entry.action == "list":
            return _ok(
                svc.list_requests(actor=actor, filters=args),
                "Fila de solicitações carregada.",
            )
        ref = args.get("request_id") or args.get("record_id") or ""
        if entry.action == "detail":
            return _ok(
                svc.get_request_detail(ref, actor=actor),
                "Solicitação carregada.",
            )
        if entry.action == "timeline":
            return _ok(
                svc.get_timeline(
                    ref, actor=actor,
                    page=int(args.get("page", 1)),
                    page_size=int(args.get("page_size", 50)),
                ),
                "Timeline carregada.",
            )
        if entry.action == "verifications":
            return _ok(
                svc.list_verifications(ref, actor=actor),
                "Verificações carregadas.",
            )
        if entry.action == "record":
            return _ok(
                svc.get_record(ref, actor=actor),
                "Ficha técnica carregada.",
            )
        if entry.action == "revisions":
            return _ok(
                svc.list_revisions(ref, actor=actor),
                "Revisões carregadas.",
            )
        if entry.action == "revision":
            return _ok(
                svc.get_revision(
                    ref,
                    int(args.get("revision_number") or 0),
                    actor=actor,
                ),
                "Revisão carregada.",
            )
        if entry.action == "reference_data":
            return _ok(
                svc.reference_data(actor=actor),
                "Dados de referência carregados.",
            )
        if entry.action == "outbound_result":
            return _ok(
                svc.outbound_request(ref, actor=actor),
                "Resultado carregado.",
            )
    except Exception as exc:
        return _domain_err(exc)
    return _err(f"Ação '{entry.capability}' sem handler.",
                code="not_implemented", status=501)


# --- EXECUTE -----------------------------------------------------------------


def _require_version(kw: dict) -> int:
    raw = kw.get("expected_version")
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        raise ValueError("expected_version inválido.")


def _payload_changes(payload: dict | None, changes: dict | None) -> list:
    if isinstance(changes, dict) and "changes" in changes:
        changes = changes["changes"]
    if changes is None and isinstance(payload, dict):
        changes = payload.get("changes")
    return changes if isinstance(changes, list) else []


async def execute_action(
    context, entry, phase, *,
    target_ref=None, payload=None, changes=None,
    idempotency_key=None, expected_version=None,
    proposal_ref=None, ctx=None,
):
    """EXECUTE dispatch — moderate direto; terminais via proposta selada."""
    svc = build_prc_service()
    actor = _actor(context)
    action = entry.action
    ref = (target_ref or "").strip()
    try:
        if action == "submit":
            body = payload or {}
            if phase == "prepare":
                return _ok(
                    {"phase": "prepare", "validated": True,
                     "request_type": body.get("requestType"),
                     "note": "ACT grava a solicitação com o ator real."},
                    "Payload aceito para submissão.",
                )
            data = svc.submit_request(
                actor=actor,
                source="eva",
                external_request_id=body.get("externalRequestId"),
                external_item_id=body.get("externalItemId"),
                request_type=body.get("requestType", ""),
                product_type=body.get("productType", "raw_material"),
                schema_version=int(body.get("schemaVersion") or 1),
                payload={
                    "requestedData": body.get("requestedData"),
                    "officialProductCode": body.get("officialProductCode"),
                    "baseRevision": body.get("baseRevision"),
                    "changes": body.get("changes"),
                },
                idempotency_key=idempotency_key,
            )
            return _ok({"entity": entry.entity, "action": action, **data},
                       "Solicitação registrada.")

        terminal = action in ("reject", "verify_and_complete")
        if terminal:
            return await _terminal(
                context, entry, phase, ref,
                payload=payload, reason=(payload or {}).get("reason"),
                official_code=(payload or {}).get("official_code"),
                expected_version=expected_version,
                proposal_ref=proposal_ref, ctx=ctx,
                idempotency_key=idempotency_key,
            )

        if not ref:
            return _err("target_ref (request_id) é obrigatório.",
                        code="validation")
        version = _require_version({"expected_version": expected_version})
        reason = (payload or {}).get("reason")

        if phase == "prepare":
            return _ok(
                {"phase": "prepare", "request_id": ref,
                 "action": action, "expected_version": version},
                "Pré-validação concluída — ACT aplica a ação.",
            )

        fn = {
            "start": svc.start_request,
            "resume": svc.resume_request,
            "submit_review": svc.submit_review,
        }.get(action)
        if fn is not None:
            data = fn(
                ref, actor=actor, expected_version=version,
                reason=reason, idempotency_key=idempotency_key,
            )
        elif action == "request_information":
            data = svc.request_information(
                ref, actor=actor, expected_version=version,
                reason=reason or "",
                pending_fields=(payload or {}).get("pending_fields") or [],
                idempotency_key=idempotency_key,
            )
        elif action == "update_draft":
            data = svc.update_draft(
                ref, actor=actor, expected_version=version,
                changes=_payload_changes(payload, changes),
                idempotency_key=idempotency_key,
            )
        else:
            return _err(f"Ação '{entry.capability}' sem handler.",
                        code="not_implemented", status=501)
        return _ok({"entity": entry.entity, "action": action, **data},
                   "Ação aplicada.")
    except ValueError as exc:
        return _err(str(exc), code="validation")
    except Exception as exc:
        return _domain_err(exc)


async def _terminal(
    context, entry, phase, ref, *,
    payload, reason, official_code,
    expected_version, proposal_ref, ctx, idempotency_key,
):
    from engineering_app.interface.mcp.semantic_bridge import (
        _require_human_confirmation,
    )
    from engineering_app.application.eva.proposal_store import (
        EvaProposalError,
    )

    svc = build_prc_service()
    actor = _actor(context)
    if not ref:
        return _err("target_ref (request_id) é obrigatório.",
                    code="validation")
    version = _require_version({"expected_version": expected_version})

    if phase == "prepare":
        detail = svc.get_request_detail(ref, actor=actor)
        proposal, handle = seal_proposal(
            capability=entry.capability,
            actor_id=str(getattr(context.user, "id", "") or ""),
            target_ref=ref,
            change={
                "action": entry.action,
                "reason": reason,
                "official_code": official_code,
                "expected_version": version,
            },
            impact={
                "operation": entry.action,
                "terminal": True,
                "status": detail.get("status"),
                "official_code": official_code
                or detail.get("officialCode"),
                "effect": (
                    "Rejeição terminal — sem alterar a ficha vigente."
                    if entry.action == "reject"
                    else "Conclusão só ocorre se a leitura oficial TOTVS "
                    "comprovar a ficha — mismatch nunca conclui."
                ),
            },
            expected_postcondition={
                "check": "read_back_status",
                "expected": "rejected"
                if entry.action == "reject" else "completed",
            },
        )
        return _ok(
            {"entity": entry.entity, "action": entry.action,
             "phase": "prepare", "proposal_ref": handle,
             "proposal": proposal.to_public_dict()},
            "Proposta selada — apresente o resumo ao usuário e execute "
            "phase=commit somente após autorização explícita.",
        )

    # commit — proposta selada + confirmação humana verificável.
    handle = (proposal_ref or "").strip()
    if not handle:
        raise EvaProposalError(
            "proposal_ref é obrigatório para phase=commit.",
            code="proposal_required", status_code=400,
        )
    proposal = load_valid_proposal(
        proposal_handle=handle,
        actor_id=str(getattr(context.user, "id", "") or ""),
        expected_capability=entry.capability,
        expected_target_ref=ref,
    )
    # A proposta selada armazena apenas o fingerprint da mudança — os
    # parâmetros do ACT são revalidados contra ele abaixo.
    if fingerprint(
        {"action": entry.action, "reason": reason,
         "official_code": official_code,
         "expected_version": version}
    ) != proposal.change_fingerprint:
        raise EvaProposalError(
            "Parâmetros divergem da proposta selada — prepare novamente.",
            code="proposal_mismatch", status_code=409,
        )
    summary = (
        f"{entry.action} na solicitação {ref}"
        + (f" (código oficial {official_code})" if official_code else "")
        + " — operação terminal/verificação oficial."
    )
    confirmation = await _require_human_confirmation(
        ctx,
        expected_echo=ref,
        summary=summary,
        proposal_id=proposal.proposal_id,
    )
    if confirmation is not None:
        return confirmation
    get_proposal_store().consume(proposal.proposal_id)
    if entry.action == "reject":
        data = svc.reject_request(
            ref, actor=actor, expected_version=version,
            reason=reason or "",
            idempotency_key=idempotency_key,
        )
    else:
        token = str(getattr(context.user, "access_token", "") or "")
        data = await svc.verify_and_complete(
            ref, actor=actor, expected_version=version,
            official_code=official_code,
            reason=reason,
            access_token=token,
            correlation_id=proposal.proposal_id,
            idempotency_key=idempotency_key,
        )
    return _ok(
        {"entity": entry.entity, "action": entry.action,
         "phase": "commit", "proposal_id": proposal.proposal_id, **data},
        "Operação terminal aplicada.",
    )
