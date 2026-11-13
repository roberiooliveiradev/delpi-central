"""CLARA governed capabilities — LNF (invoice_posting).

Delegam às rotas/use cases da BFF com o ContextVar do usuário final
(já estabelecido pelo transporte MCP). Não reimplementam AuthZ.
"""

from __future__ import annotations

import inspect
import json
from typing import Any, Callable
from uuid import UUID

from fastapi.params import Param
from pydantic_core import PydanticUndefined
from starlette.responses import Response

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.interface.http.routes.invoice_posting import (
    router as lnf_router,
)
from controllership_finance_app.interface.http.routes.invoice_posting.router import (
    BlockBody,
    CancelBody,
    CommentBody,
    CreateRequestBody,
    LinkPurchaseOrderBody,
    LinkPurchaseOrderGroupBody,
    PostManualBody,
    ReconciliationRunBody,
)

_APP_BASE = "/apps/lancamento-notas-fiscais"


class LnfRouteFailed(ChecklistDomainError):
    code = "lnf_route_failed"
    status = 400


def _call_route(fn, **params: Any) -> Any:
    """Chama rota LNF resolvendo defaults ``Query``/``Param``."""
    resolved = dict(params)
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        signature = None
    if signature is not None:
        for name, param in signature.parameters.items():
            if name in resolved:
                continue
            default = param.default
            if default is inspect.Parameter.empty:
                continue
            if isinstance(default, Param):
                value = default.default
                resolved[name] = None if value is PydanticUndefined else value
            else:
                resolved[name] = default
    return fn(**resolved)


def _unwrap_route(result: Any) -> dict:
    if isinstance(result, Response):
        try:
            body = json.loads(result.body)
        except Exception as exc:  # noqa: BLE001
            raise LnfRouteFailed("Resposta LNF não-JSON.") from exc
        if isinstance(body, dict) and body.get("success") is False:
            msg = body.get("message") or "Operação LNF rejeitada."
            err = LnfRouteFailed(msg)
            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            code = ((data.get("error") or {}).get("code")) if data else None
            if code:
                err.code = str(code)
            err.status = int(getattr(result, "status_code", 400) or 400)
            raise err
        if isinstance(body, dict) and "data" in body:
            data = body.get("data")
            return data if isinstance(data, dict) else {"value": data}
        return body if isinstance(body, dict) else {"value": body}
    if isinstance(result, dict):
        return result
    return {"value": result}


def _as_uuid(request_id: Any) -> UUID:
    return UUID(str(request_id))


def _request_snapshot(request_id: Any) -> dict:
    data = _unwrap_route(
        _call_route(lnf_router.get_request, request_id=_as_uuid(request_id))
    )
    req = data.get("request") if isinstance(data, dict) else None
    if not isinstance(req, dict):
        return {"request": {"status": None, "id": str(request_id)}}
    return {
        "request": {
            "status": req.get("status"),
            "id": str(req.get("id") or request_id),
            "revision": req.get("revision") or req.get("updated_at"),
        }
    }


def _create_fingerprint(params: dict) -> dict:
    return {
        "request": {
            "status": "absent",
            "fingerprint": "|".join(
                [
                    str(params.get("branch") or params.get("branch_code") or ""),
                    str(params.get("document") or params.get("document_number") or ""),
                    str(params.get("series") or ""),
                    str(params.get("fiscal_model") or ""),
                    str(params.get("supplier_code") or ""),
                    str(params.get("supplier_store") or ""),
                ]
            ),
        }
    }


def _reconciliation_snapshot() -> dict:
    return {"request": {"status": "reconciliation_ready"}}


def snapshot_for(capability: str, params: dict) -> dict | None:
    """Retorna snapshot LNF ou None se a capability não for LNF."""
    if capability == "invoice_posting.create":
        return _create_fingerprint(params)
    if capability == "reconciliation.run":
        return _reconciliation_snapshot()
    if capability.startswith("invoice_posting.") or capability == "reconciliation.refresh":
        rid = params.get("request_id")
        if capability == "reconciliation.refresh":
            return _reconciliation_snapshot()
        if rid is None:
            return {}
        try:
            return _request_snapshot(rid)
        except Exception:  # noqa: BLE001 — snapshot fail-closed
            return {}
    return None


def _exec_comment(p: dict, *_a) -> dict:
    body = CommentBody(
        body=str(p["body"]),
        mentioned_user_ids=list(p.get("mentioned_user_ids") or []),
    )
    return _unwrap_route(
        _call_route(
            lnf_router.add_comment,
            request_id=_as_uuid(p["request_id"]),
            body=body,
        )
    )


def _exec_refresh(_p: dict, *_a) -> dict:
    return _unwrap_route(_call_route(lnf_router.refresh_reconciliation))


def _exec_create(p: dict, *_a) -> dict:
    payload = {k: v for k, v in p.items() if k != "idempotency_key"}
    body = CreateRequestBody.model_validate(payload)
    return _unwrap_route(_call_route(lnf_router.create_request, body=body))


def _exec_update(p: dict, *_a) -> dict:
    rid = _as_uuid(p["request_id"])
    patch = {
        k: v
        for k, v in p.items()
        if k not in {"request_id", "idempotency_key"} and v is not None
    }
    return _unwrap_route(
        _call_route(lnf_router.update_request, request_id=rid, body=patch)
    )


def _exec_link(p: dict, *_a) -> dict:
    rid = _as_uuid(p["request_id"])
    if p.get("groups") is not None:
        groups = [
            LinkPurchaseOrderGroupBody.model_validate(g)
            for g in (p.get("groups") or [])
        ]
        body = LinkPurchaseOrderBody(groups=groups)
    else:
        body = LinkPurchaseOrderBody(
            order_number=p.get("order_number"),
            delivery_date=p.get("delivery_date"),
        )
    return _unwrap_route(
        _call_route(
            lnf_router.link_request_purchase_order,
            request_id=rid,
            body=body,
        )
    )


def _exec_start(p: dict, *_a) -> dict:
    return _unwrap_route(
        _call_route(
            lnf_router.start_request, request_id=_as_uuid(p["request_id"])
        )
    )


def _exec_block(p: dict, *_a) -> dict:
    body = BlockBody(
        block_reason=str(p["block_reason"]),
        block_description=str(p["block_description"]),
        assignee_user_id=str(p["assignee_user_id"]),
        assignee_name=str(p["assignee_name"]),
    )
    return _unwrap_route(
        _call_route(
            lnf_router.block_request,
            request_id=_as_uuid(p["request_id"]),
            body=body,
        )
    )


def _exec_resume(p: dict, *_a) -> dict:
    return _unwrap_route(
        _call_route(
            lnf_router.resume_request, request_id=_as_uuid(p["request_id"])
        )
    )


def _exec_post_manual(p: dict, *_a) -> dict:
    justification = p.get("justification")
    if not justification or not str(justification).strip():
        raise LnfRouteFailed("justification é obrigatória para post_manual na CLARA.")
    body = PostManualBody(justification=str(justification).strip())
    return _unwrap_route(
        _call_route(
            lnf_router.post_manual_request,
            request_id=_as_uuid(p["request_id"]),
            body=body,
        )
    )


def _exec_run(p: dict, *_a) -> dict:
    body = ReconciliationRunBody(limit=p.get("limit"))
    return _unwrap_route(_call_route(lnf_router.run_reconciliation, body=body))


def _exec_cancel(p: dict, *_a) -> dict:
    justification = p.get("justification")
    if not justification or not str(justification).strip():
        raise LnfRouteFailed("justification é obrigatória para cancel.")
    body = CancelBody(justification=str(justification).strip())
    return _unwrap_route(
        _call_route(
            lnf_router.cancel_request,
            request_id=_as_uuid(p["request_id"]),
            body=body,
        )
    )


def _status_of(result: dict | None) -> str | None:
    if not isinstance(result, dict):
        return None
    req = result.get("request")
    if isinstance(req, dict):
        return req.get("status")
    return result.get("status")


def build_lnf_capability_table(
    *,
    require: Callable[[dict, str], Any],
) -> dict[str, dict]:
    """Tabela de capabilities LNF para merge em ClaraGovernedWrites."""

    def _rid(p: dict) -> str:
        return str(require(p, "request_id"))

    return {
        "invoice_posting.comment": {
            "gate": "lnf_write",
            "direct": True,
            "resource_type": "invoice_posting_request",
            "resource_key": _rid,
            "required_params": ("request_id", "body"),
            "describe": lambda p: (
                f"comentar na solicitação LNF {p.get('request_id')}"
            ),
            "execute": _exec_comment,
            "verify": lambda p, result: bool(result),
            "postcondition": lambda p, result, actor: (
                _status_of(_request_snapshot(p["request_id"])) is not None
            ),
        },
        "reconciliation.refresh": {
            "gate": "lnf_read",
            "direct": True,
            "resource_type": "invoice_posting_reconciliation",
            "resource_key": lambda p: "reconciliation",
            "required_params": (),
            "describe": lambda p: "atualizar fila de conciliação LNF",
            "execute": _exec_refresh,
            "verify": lambda p, result: True,
            "postcondition": lambda p, result, actor: True,
        },
        "invoice_posting.create": {
            "gate": "lnf_create",
            "direct": False,
            "resource_type": "invoice_posting_request",
            "resource_key": lambda p: (
                f"{p.get('branch') or p.get('branch_code')}:"
                f"{p.get('document') or p.get('document_number')}"
            ),
            "required_params": (
                "branch",
                "document",
                "fiscal_model",
                "supplier_code",
                "supplier_store",
                "issue_date",
                "amount",
                "received_at",
            ),
            "describe": lambda p: (
                f"criar solicitação LNF {p.get('document')} "
                f"filial {p.get('branch')}"
            ),
            "execute": _exec_create,
            "verify": lambda p, result: bool(
                (result or {}).get("request", {}).get("id")
                or (result or {}).get("id")
            ),
            "postcondition": lambda p, result, actor: (
                _status_of(result) in {"pending", "in_progress", "blocked"}
                or bool((result or {}).get("request", {}).get("id"))
            ),
        },
        "invoice_posting.update": {
            "gate": "lnf_write",
            "direct": False,
            "resource_type": "invoice_posting_request",
            "resource_key": _rid,
            "required_params": ("request_id",),
            "describe": lambda p: (
                f"atualizar solicitação LNF {p.get('request_id')}"
            ),
            "execute": _exec_update,
            "verify": lambda p, result: bool(result),
            "postcondition": lambda p, result, actor: (
                _status_of(_request_snapshot(p["request_id"])) is not None
            ),
        },
        "invoice_posting.link_purchase_order": {
            "gate": "lnf_process",
            "direct": False,
            "resource_type": "invoice_posting_request",
            "resource_key": _rid,
            "required_params": ("request_id",),
            "describe": lambda p: (
                f"amarrar PC à solicitação LNF {p.get('request_id')}"
            ),
            "execute": _exec_link,
            "verify": lambda p, result: bool(result),
            "postcondition": lambda p, result, actor: True,
        },
        "invoice_posting.start": {
            "gate": "lnf_process",
            "direct": False,
            "resource_type": "invoice_posting_request",
            "resource_key": _rid,
            "required_params": ("request_id",),
            "describe": lambda p: (
                f"iniciar atendimento LNF {p.get('request_id')}"
            ),
            "execute": _exec_start,
            "verify": lambda p, result: _status_of(result) == "in_progress"
            or bool(result),
            "postcondition": lambda p, result, actor: (
                _status_of(_request_snapshot(p["request_id"])) == "in_progress"
            ),
        },
        "invoice_posting.block": {
            "gate": "lnf_process",
            "direct": False,
            "resource_type": "invoice_posting_request",
            "resource_key": _rid,
            "required_params": (
                "request_id",
                "block_reason",
                "block_description",
                "assignee_user_id",
                "assignee_name",
            ),
            "describe": lambda p: (
                f"bloquear solicitação LNF {p.get('request_id')}"
            ),
            "execute": _exec_block,
            "verify": lambda p, result: _status_of(result) == "blocked"
            or bool(result),
            "postcondition": lambda p, result, actor: (
                _status_of(_request_snapshot(p["request_id"])) == "blocked"
            ),
        },
        "invoice_posting.resume": {
            "gate": "lnf_process",
            "direct": False,
            "resource_type": "invoice_posting_request",
            "resource_key": _rid,
            "required_params": ("request_id",),
            "describe": lambda p: (
                f"retomar solicitação LNF {p.get('request_id')}"
            ),
            "execute": _exec_resume,
            "verify": lambda p, result: _status_of(result) == "in_progress"
            or bool(result),
            "postcondition": lambda p, result, actor: (
                _status_of(_request_snapshot(p["request_id"])) == "in_progress"
            ),
        },
        "invoice_posting.post_manual": {
            "gate": "lnf_process",
            "direct": False,
            "resource_type": "invoice_posting_request",
            "resource_key": _rid,
            "required_params": ("request_id", "justification"),
            "describe": lambda p: (
                f"marcar como lançada (manual) LNF {p.get('request_id')}"
            ),
            "execute": _exec_post_manual,
            "verify": lambda p, result: _status_of(result) == "posted"
            or bool(result),
            "postcondition": lambda p, result, actor: (
                _status_of(_request_snapshot(p["request_id"])) == "posted"
            ),
        },
        "reconciliation.run": {
            "gate": "lnf_manage",
            "direct": False,
            "resource_type": "invoice_posting_reconciliation",
            "resource_key": lambda p: "reconciliation",
            "required_params": (),
            "describe": lambda p: "executar conciliação LNF",
            "execute": _exec_run,
            "verify": lambda p, result: True,
            "postcondition": lambda p, result, actor: True,
        },
        "invoice_posting.cancel": {
            "gate": "lnf_write",
            "destructive": True,
            "direct": False,
            "resource_type": "invoice_posting_request",
            "resource_key": _rid,
            "required_params": ("request_id", "justification"),
            "describe": lambda p: (
                f"cancelar solicitação LNF {p.get('request_id')}"
            ),
            "execute": _exec_cancel,
            "verify": lambda p, result: _status_of(result) == "cancelled"
            or bool(result),
            "postcondition": lambda p, result, actor: (
                _status_of(_request_snapshot(p["request_id"])) == "cancelled"
            ),
        },
    }


def app_deep_link(request_id: str | None = None) -> dict[str, str]:
    out = {"app_url": _APP_BASE}
    if request_id:
        out["request_url"] = f"{_APP_BASE}?requestId={request_id}"
    return out
