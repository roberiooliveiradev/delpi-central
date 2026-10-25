"""CLARA — apresentação funcional do plano (R-CLARA-02, Doc 106 §4).

A página de consentimento só pode pedir autorização do que o usuário
consegue compreender. Este módulo traduz cada operação selada
(capability + params) em uma descrição funcional em português,
resolvendo rótulos de domínio (título do documento, nome do item,
área/versão do pacote, pergunta do esclarecimento) por leitura
best-effort — falha de rótulo degrada para o identificador curto,
nunca para silêncio.

É a fonte única de apresentação consumida pelo plano (PREPARE) e
pela superfície de consentimento: o que aparece na página é o que o
``plan_hash`` sela — nada é reconstruído no frontend.
"""

from __future__ import annotations

from typing import Any, Callable

from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
)

_SCHEMA = SCHEMA_NAME

_MONTHS_PT = {
    "01": "janeiro", "02": "fevereiro", "03": "março",
    "04": "abril", "05": "maio", "06": "junho",
    "07": "julho", "08": "agosto", "09": "setembro",
    "10": "outubro", "11": "novembro", "12": "dezembro",
}

_DECISION_PT = {
    "ACCEPTED": "Aceitar",
    "REJECTED": "Rejeitar",
    "REVERSED": "Reverter a decisão sobre",
}

_OUTCOME_PT = {
    "ACCEPTED": "Aprovar",
    "CHANGES_REQUESTED": "Solicitar ajustes em",
    "REJECTED": "Rejeitar",
}


def period_label(period: Any) -> str:
    """``2026-09`` → ``setembro de 2026`` (fallback: o próprio valor)."""
    text = str(period or "")
    try:
        year, month = text.split("-", 1)
        return f"{_MONTHS_PT[month[:2]]} de {year}"
    except (ValueError, KeyError):
        return text or "competência não informada"


def _short(value: Any) -> str:
    text = str(value or "")
    return f"{text[:8]}…" if len(text) > 10 else text or "—"


# -- rótulos de domínio (best-effort) --------------------------------------


def _scalar(sql: str, args: tuple) -> Any:
    try:
        with plugins_db_connect() as conn:
            row = conn.execute(sql, args).fetchone()
        return row[0] if row else None
    except Exception:  # noqa: BLE001 — rótulo é best-effort
        return None


def document_title(period: Any, document_id: Any) -> str | None:
    return _scalar(
        f"""
        SELECT d.title
          FROM {_SCHEMA}.closing_document d
          JOIN {_SCHEMA}.monthly_competence mc
            ON mc.competence_id = d.competence_id
         WHERE d.document_id = %s AND mc.period = %s
        """,
        (str(document_id), str(period)),
    )


def item_name(period: Any, item_key: Any) -> str | None:
    return _scalar(
        f"""
        SELECT i.name
          FROM {_SCHEMA}.competence_checklist_item i
          JOIN {_SCHEMA}.monthly_competence mc
            ON mc.competence_id = i.competence_id
         WHERE mc.period = %s AND i.item_key = %s
        """,
        (str(period), str(item_key)),
    )


def _row(sql: str, args: tuple) -> Any:
    try:
        with plugins_db_connect() as conn:
            return conn.execute(sql, args).fetchone()
    except Exception:  # noqa: BLE001 — rótulo é best-effort
        return None


def package_version_label(period: Any, package_version_id: Any) -> str | None:
    """``pacote CONTÁBIL v2`` do pacote dono da versão."""
    row = _row(
        f"""
        SELECT p.recipient_area, v.version_no
          FROM {_SCHEMA}.closing_package_version v
          JOIN {_SCHEMA}.closing_package p
            ON p.package_id = v.package_id
          JOIN {_SCHEMA}.monthly_competence mc
            ON mc.competence_id = p.competence_id
         WHERE v.package_version_id = %s AND mc.period = %s
        """,
        (str(package_version_id), str(period)),
    )
    if row is None:
        return None
    return f"pacote {row[0]} v{row[1]}"


def _package_label(period: Any, package_version_id: Any) -> str:
    return package_version_label(period, package_version_id) or (
        f"versão {_short(package_version_id)} do pacote"
    )


def clarification_label(period: Any, clarification_id: Any) -> dict | None:
    row = _row(
        f"""
        SELECT c.area, c.question
          FROM {_SCHEMA}.closing_clarification c
          JOIN {_SCHEMA}.closing_package_version v
            ON v.package_version_id = c.package_version_id
          JOIN {_SCHEMA}.closing_package p
            ON p.package_id = v.package_id
          JOIN {_SCHEMA}.monthly_competence mc
            ON mc.competence_id = p.competence_id
         WHERE c.clarification_id = %s AND mc.period = %s
        """,
        (str(clarification_id), str(period)),
    )
    if row is None:
        return None
    return {"area": row[0], "question": row[1]}


# -- apresentadores por capability ------------------------------------------


def _clip(text: Any, limit: int = 140) -> str:
    value = str(text or "").strip()
    if len(value) > limit:
        return value[: limit - 1].rstrip() + "…"
    return value


def _evidence_version(params: dict) -> dict:
    period = period_label(params.get("period"))
    title = document_title(
        params.get("period"), params.get("document_id")
    )
    target = (
        f"o documento «{title}»" if title
        else f"o documento {_short(params.get('document_id'))}"
    )
    decision = str(params.get("decision") or "").upper()
    verb = _DECISION_PT.get(decision, f"Registrar {decision or 'decisão'} em")
    reason = params.get("comment") or params.get("reason_code")
    effect = (
        "o item do checklist é reavaliado com a evidência aceita"
        if decision == "ACCEPTED"
        else "a evidência fica marcada como rejeitada"
        if decision == "REJECTED"
        else "a decisão anterior sobre a evidência é revertida"
    )
    return {
        "action": verb,
        "target": f"{target} da competência {period}",
        "effect": effect,
        "motivation": _clip(reason) if reason else None,
        "summary": f"{verb} {target} da competência {period}.",
    }


def _evidence_item_set(params: dict) -> dict:
    period = period_label(params.get("period"))
    name = item_name(params.get("period"), params.get("item_key"))
    target = (
        f"o conjunto de evidências do item «{name}»" if name
        else f"o item {params.get('item_key')}"
    )
    decision = str(params.get("decision") or "").upper()
    verb = _DECISION_PT.get(decision, f"Registrar {decision or 'decisão'} em")
    reason = params.get("comment") or params.get("reason_code")
    return {
        "action": verb,
        "target": f"{target} da competência {period}",
        "effect": "todas as evidências do item recebem a decisão",
        "motivation": _clip(reason) if reason else None,
        "summary": f"{verb} {target} da competência {period}.",
    }


def _review_decision(params: dict) -> dict:
    period = period_label(params.get("period"))
    target_pkg = _package_label(
        params.get("period"), params.get("package_version_id")
    )
    outcome = str(params.get("outcome") or "").upper()
    verb = _OUTCOME_PT.get(outcome, f"Registrar {outcome or 'decisão'} em")
    area = params.get("area") or "área revisora"
    note = params.get("note")
    return {
        "action": verb,
        "target": (
            f"o {target_pkg} da competência {period} na revisão "
            f"da área {area}"
        ),
        "effect": "a decisão da área fica registrada na revisão",
        "motivation": _clip(note) if note else None,
        "summary": (
            f"{verb} o {target_pkg} da competência {period} "
            f"(revisão da área {area})."
        ),
    }


def _clarification_open(params: dict) -> dict:
    period = period_label(params.get("period"))
    target_pkg = _package_label(
        params.get("period"), params.get("package_version_id")
    )
    area = params.get("area") or "a área responsável"
    question = _clip(params.get("question"))
    return {
        "action": "Abrir esclarecimento",
        "target": (
            f"para {area} sobre o {target_pkg} da competência {period}"
        ),
        "effect": (
            "o pacote fica com um esclarecimento aberto aguardando "
            "resposta"
        ),
        "motivation": f"«{question}»" if question else None,
        "summary": (
            f"Abrir esclarecimento para {area} sobre o {target_pkg} "
            f"da competência {period}."
        ),
    }


def _clarification_resolve(params: dict) -> dict:
    period = period_label(params.get("period"))
    label = clarification_label(
        params.get("period"), params.get("clarification_id")
    )
    if label:
        area = label.get("area") or "área responsável"
        question = _clip(label.get("question"))
        target = (
            f"o esclarecimento de {area} («{question}») da "
            f"competência {period}"
        )
    else:
        target = (
            f"o esclarecimento {_short(params.get('clarification_id'))} "
            f"da competência {period}"
        )
    response = _clip(params.get("response"))
    return {
        "action": "Responder",
        "target": target,
        "effect": "o esclarecimento fica respondido e resolvido",
        "motivation": f"«{response}»" if response else None,
        "summary": f"Responder {target} com a resposta informada.",
    }


_PRESENTERS: dict[str, Callable[[dict], dict]] = {
    "evidence.decide_version": _evidence_version,
    "evidence.decide_item_set": _evidence_item_set,
    "review.record_decision": _review_decision,
    "clarification.open": _clarification_open,
    "clarification.resolve": _clarification_resolve,
}


def present_operation(capability: str, params: dict) -> dict:
    """Apresentação funcional selada da operação.

    ``displayable=False`` quando a capability não tem apresentador
    ou um parâmetro obrigatório à descrição está ausente — a
    superfície de consentimento deve impedir a autorização de
    operações não representáveis.
    """
    presenter = _PRESENTERS.get(capability)
    if presenter is None:
        return {
            "displayable": False,
            "action": capability or "operação desconhecida",
            "target": "—",
            "effect": None,
            "motivation": None,
            "summary": (
                "Operação sem representação funcional — não "
                "autorizável."
            ),
        }
    try:
        presentation = presenter(dict(params or {}))
    except Exception:  # noqa: BLE001 — apresentação nunca quebra o plano
        return {
            "displayable": False,
            "action": capability,
            "target": "—",
            "effect": None,
            "motivation": None,
            "summary": (
                "Operação sem representação funcional — não "
                "autorizável."
            ),
        }
    presentation["displayable"] = True
    return presentation
