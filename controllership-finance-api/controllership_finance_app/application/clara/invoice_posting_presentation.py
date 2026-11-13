"""Apresentação selada das operações LNF (CLARA PREPARE/consent).

Mesmo contrato de ``operation_presentation._simple``: action, target,
effect, motivation, summary — com alvo legível (filial, NF, fornecedor,
valor) e efeito de→para status quando aplicável.
"""

from __future__ import annotations

from typing import Any, Callable

from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_connect,
)

_LNF_SCHEMA = "lancamento_notas_fiscais"

_STATUS_PT = {
    "pending": "Pendente",
    "in_progress": "Em atendimento",
    "blocked": "Bloqueada",
    "posted": "Lançada",
    "cancelled": "Cancelada",
}


def _clip(text: Any, limit: int = 4000) -> str | None:
    if text is None:
        return None
    cleaned = " ".join(str(text).split())
    if not cleaned:
        return None
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"


def _money(value: Any) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(value or "—")


def _status_pt(raw: Any) -> str:
    key = str(raw or "").strip().lower()
    return _STATUS_PT.get(key, str(raw or "—"))


def _request_row(request_id: Any) -> dict[str, Any] | None:
    if not request_id:
        return None
    try:
        with plugins_db_connect() as conn:
            row = conn.execute(
                f"""
                SELECT id::text AS id,
                       branch_code,
                       document_number,
                       series,
                       supplier_code,
                       supplier_store,
                       amount,
                       status,
                       fiscal_model
                  FROM {_LNF_SCHEMA}.invoice_posting_requests
                 WHERE id = %s::uuid
                """,
                (str(request_id),),
            ).fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        cols = (
            "id",
            "branch_code",
            "document_number",
            "series",
            "supplier_code",
            "supplier_store",
            "amount",
            "status",
            "fiscal_model",
        )
        return dict(zip(cols, row))
    except Exception:  # noqa: BLE001 — rótulo best-effort
        return None


def _nf_label(row: dict[str, Any] | None, params: dict) -> str:
    if row:
        branch = row.get("branch_code") or "?"
        doc = row.get("document_number") or "?"
        series = row.get("series") or "—"
        supplier = row.get("supplier_code") or "—"
        store = row.get("supplier_store") or ""
        supplier_txt = f"{supplier}/{store}" if store else str(supplier)
        amount = _money(row.get("amount"))
        status = _status_pt(row.get("status"))
        return (
            f"NF {doc} série {series} · filial {branch} · "
            f"fornecedor {supplier_txt} · {amount} · status {status}"
        )
    branch = params.get("branch") or params.get("branch_code") or "?"
    doc = params.get("document") or params.get("document_number") or "?"
    series = params.get("series") or "—"
    supplier = params.get("supplier_code") or "—"
    store = params.get("supplier_store") or ""
    supplier_txt = f"{supplier}/{store}" if store else str(supplier)
    amount = _money(params.get("amount"))
    return (
        f"NF {doc} série {series} · filial {branch} · "
        f"fornecedor {supplier_txt} · {amount}"
    )


def _simple(
    action: str,
    target: str,
    *,
    effect: str | None = None,
    motivation: Any = None,
    summary: str | None = None,
    risks: str | None = None,
    reversible: bool | None = None,
) -> dict:
    out = {
        "action": action,
        "target": target,
        "effect": effect,
        "motivation": _clip(motivation),
        "summary": summary or f"{action} {target}.",
    }
    if risks:
        out["risks"] = risks
    if reversible is not None:
        out["reversible"] = reversible
    return out


def _present_create(p: dict) -> dict:
    target = _nf_label(None, p)
    return _simple(
        "Criar solicitação de lançamento",
        target,
        effect="a solicitação nasce como Pendente no app LNF",
        motivation=p.get("observation"),
        summary=f"Criar solicitação de lançamento: {target}.",
        risks="Não lança no Protheus; só registra a solicitação no app.",
        reversible=True,
    )


def _present_update(p: dict) -> dict:
    row = _request_row(p.get("request_id"))
    target = _nf_label(row, p)
    return _simple(
        "Atualizar solicitação",
        target,
        effect="os campos informados substituem os valores atuais",
        summary=f"Atualizar a solicitação {target}.",
        reversible=True,
    )


def _present_link(p: dict) -> dict:
    row = _request_row(p.get("request_id"))
    target = _nf_label(row, p)
    orders = p.get("order_number") or (
        ", ".join(
            str(g.get("order_number"))
            for g in (p.get("groups") or [])
            if isinstance(g, dict) and g.get("order_number")
        )
        or "pedido(s) informado(s)"
    )
    return _simple(
        "Amarrar pedido de compra",
        target,
        effect=f"a solicitação fica vinculada a {orders}",
        summary=f"Amarrar {orders} à solicitação {target}.",
        reversible=True,
    )


def _present_start(p: dict) -> dict:
    row = _request_row(p.get("request_id"))
    target = _nf_label(row, p)
    current = _status_pt((row or {}).get("status") or "pending")
    return _simple(
        "Iniciar atendimento",
        target,
        effect=f"status de {current} → Em atendimento",
        summary=f"Iniciar atendimento da solicitação {target}.",
        reversible=False,
    )


def _present_block(p: dict) -> dict:
    row = _request_row(p.get("request_id"))
    target = _nf_label(row, p)
    current = _status_pt((row or {}).get("status") or "—")
    assignee = p.get("assignee_name") or p.get("assignee_user_id") or "—"
    reason = p.get("block_reason")
    desc = p.get("block_description")
    motivation = " · ".join(
        part for part in (str(reason or ""), str(desc or "")) if part
    )
    return _simple(
        "Bloquear solicitação",
        target,
        effect=(
            f"status de {current} → Bloqueada; responsável {assignee}"
        ),
        motivation=motivation or None,
        summary=(
            f"Bloquear a solicitação {target} "
            f"(responsável {assignee})."
        ),
        reversible=True,
    )


def _present_resume(p: dict) -> dict:
    row = _request_row(p.get("request_id"))
    target = _nf_label(row, p)
    return _simple(
        "Retomar solicitação",
        target,
        effect="status de Bloqueada → Em atendimento",
        summary=f"Retomar a solicitação {target}.",
        reversible=False,
    )


def _present_post_manual(p: dict) -> dict:
    row = _request_row(p.get("request_id"))
    target = _nf_label(row, p)
    current = _status_pt((row or {}).get("status") or "—")
    return _simple(
        "Marcar como lançada (manual)",
        target,
        effect=f"status de {current} → Lançada (sem escrita no Protheus)",
        motivation=p.get("justification"),
        summary=(
            f"Marcar como lançada (manual) a solicitação {target}. "
            f"Justificativa: {_clip(p.get('justification')) or '—'}."
        ),
        risks=(
            "Não grava lançamento no ERP; apenas conclui o fluxo no app."
        ),
        reversible=False,
    )


def _present_recon_run(p: dict) -> dict:
    limit = p.get("limit")
    target = (
        f"fila de conciliação LNF (limite {limit})"
        if limit is not None
        else "fila de conciliação LNF"
    )
    return _simple(
        "Executar conciliação",
        target,
        effect="a fila é processada conforme a regra canônica da BFF",
        summary=f"Executar conciliação na {target}.",
        risks="Pode alterar estados de solicitações elegíveis.",
        reversible=False,
    )


def _present_cancel(p: dict) -> dict:
    row = _request_row(p.get("request_id"))
    target = _nf_label(row, p)
    current = _status_pt((row or {}).get("status") or "—")
    return _simple(
        "Cancelar solicitação",
        target,
        effect=f"status de {current} → Cancelada (terminal)",
        motivation=p.get("justification"),
        summary=(
            f"Cancelar a solicitação {target}. "
            f"Justificativa: {_clip(p.get('justification')) or '—'}."
        ),
        risks="Operação destrutiva no fluxo LNF; não desfaz sozinha.",
        reversible=False,
    )


def _present_comment(p: dict) -> dict:
    row = _request_row(p.get("request_id"))
    target = _nf_label(row, p)
    return _simple(
        "Comentar",
        target,
        effect="o comentário fica visível no histórico da solicitação",
        motivation=p.get("body"),
        summary=f"Comentar na solicitação {target}.",
        reversible=False,
    )


def _present_recon_refresh(_p: dict) -> dict:
    return _simple(
        "Atualizar fila de conciliação",
        "lançamento de notas fiscais",
        effect="a fila é recarregada sem aplicar lançamentos",
        summary="Atualizar a fila de conciliação do LNF.",
        reversible=True,
    )


LNF_PRESENTERS: dict[str, Callable[[dict], dict]] = {
    "invoice_posting.create": _present_create,
    "invoice_posting.update": _present_update,
    "invoice_posting.link_purchase_order": _present_link,
    "invoice_posting.start": _present_start,
    "invoice_posting.block": _present_block,
    "invoice_posting.resume": _present_resume,
    "invoice_posting.post_manual": _present_post_manual,
    "reconciliation.run": _present_recon_run,
    "invoice_posting.cancel": _present_cancel,
    "invoice_posting.comment": _present_comment,
    "reconciliation.refresh": _present_recon_refresh,
}
