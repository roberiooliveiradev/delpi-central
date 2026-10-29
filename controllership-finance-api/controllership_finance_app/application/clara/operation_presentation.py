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


def _clip(text: Any, limit: int = 4000) -> str:
    """Clip defensivo de payload — nunca corta texto material do
    usuário (motivo, pergunta, resposta) em tamanho que esconda
    escopo da aprovação (R-CLARA-02)."""
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


def pendency_title(period: Any, pendency_id: Any) -> str | None:
    return _scalar(
        f"""
        SELECT p.title
          FROM {_SCHEMA}.closing_pendency p
          JOIN {_SCHEMA}.monthly_competence mc
            ON mc.competence_id = p.competence_id
         WHERE p.pendency_id = %s AND mc.period = %s
        """,
        (str(pendency_id), str(period)),
    )


def _pendency_label(period: Any, pendency_id: Any) -> str:
    title = pendency_title(period, pendency_id)
    return (
        f"a pendência «{title}»"
        if title
        else f"a pendência {_short(pendency_id)}"
    )


def _simple(
    action: str,
    target: str,
    *,
    effect: str | None = None,
    motivation: Any = None,
    summary: str | None = None,
) -> dict:
    return {
        "action": action,
        "target": target,
        "effect": effect,
        "motivation": _clip(motivation) if motivation else None,
        "summary": summary or f"{action} {target}.",
    }


def _period_of(params: dict) -> str:
    return period_label(params.get("period"))


def _doc_target(params: dict) -> str:
    title = document_title(params.get("period"), params.get("document_id"))
    return (
        f"o documento «{title}»"
        if title
        else f"o documento {_short(params.get('document_id'))}"
    )


def _item_target(params: dict) -> str:
    name = item_name(params.get("period"), params.get("item_key"))
    return (
        f"o item «{name}»"
        if name
        else f"o item {params.get('item_key')}"
    )


def _pkg_target(params: dict) -> str:
    return _package_label(
        params.get("period"), params.get("package_version_id")
    )


# -- apresentadores genéricos (classe A/B/C/D mantêm consentimento) ----------


def _present_competence_open(p: dict) -> dict:
    return _simple(
        "Abrir",
        f"a competência {_period_of(p)}",
        effect=(
            "a competência é aberta e o checklist vigente é clonado "
            "para a execução do mês"
        ),
    )


def _present_pendency_create(p: dict) -> dict:
    return _simple(
        "Criar",
        (
            f"a pendência «{p.get('title')}» do tipo "
            f"{p.get('kind')} na competência {_period_of(p)}"
        ),
        effect="a pendência entra na fila de trabalho da competência",
        motivation=p.get("description"),
    )


def _present_pendency_claim(p: dict) -> dict:
    return _simple(
        "Assumir",
        f"{_pendency_label(p.get('period'), p.get('pendency_id'))} "
        f"da competência {_period_of(p)}",
        effect="a pendência fica atribuída a você",
    )


def _present_pendency_reassign(p: dict) -> dict:
    return _simple(
        "Reatribuir",
        f"{_pendency_label(p.get('period'), p.get('pendency_id'))} "
        f"para {p.get('new_responsible')} na competência "
        f"{_period_of(p)}",
        effect="o responsável registrado da pendência muda",
    )


def _present_pendency_transition(p: dict) -> dict:
    return _simple(
        "Mover",
        f"{_pendency_label(p.get('period'), p.get('pendency_id'))} "
        f"para o estado {p.get('to_state')} na competência "
        f"{_period_of(p)}",
        effect="o estado de trabalho da pendência é atualizado",
        motivation=p.get("justification") or p.get("notes"),
    )


def _present_pendency_classification(p: dict) -> dict:
    return _simple(
        "Confirmar a classificação",
        (
            f"{p.get('classification')} em "
            f"{_pendency_label(p.get('period'), p.get('pendency_id'))} "
            f"da competência {_period_of(p)}"
        ),
        effect=(
            "a classificação sugerida vira classificação confirmada "
            "(decisão humana registrada)"
        ),
        motivation=p.get("reason"),
    )


def _present_p3_cutoff(p: dict) -> dict:
    return _simple(
        "Confirmar o cutoff P3 de",
        f"{_period_of(p)}",
        effect="o ponto de corte da conciliação fica registrado",
        motivation=p.get("notes"),
    )


def _present_p3_upsert(p: dict) -> dict:
    return _simple(
        "Registrar a fonte",
        (
            f"{p.get('domain')} como {p.get('source_state')} na "
            f"competência {_period_of(p)}"
        ),
        effect=(
            "a conciliação governada P3 registra o estado declarado "
            "da fonte oficial"
        ),
        motivation=p.get("rule_version"),
    )


def _present_p3_revalidate(p: dict) -> dict:
    return _simple(
        "Revalidar a conciliação P3 de",
        f"{_period_of(p)}",
        effect="uma nova rodada de revalidação é registrada",
        motivation=p.get("notes"),
    )


def _present_package_finalize(p: dict) -> dict:
    return _simple(
        "Finalizar o pacote",
        f"{p.get('recipient_area')} da competência {_period_of(p)}",
        effect="o pacote sai de rascunho e gera a versão finalizada",
        motivation=p.get("notes"),
    )


def _present_package_reopen(p: dict) -> dict:
    return _simple(
        "Reabrir",
        f"{_pkg_target(p)} da competência {_period_of(p)}",
        effect="a versão volta a editável para ajustes",
        motivation=p.get("reason"),
    )


def _present_package_complement(p: dict) -> dict:
    return _simple(
        "Criar complemento de",
        f"{_pkg_target(p)} da competência {_period_of(p)}",
        effect="uma nova versão complementar é criada",
        motivation=p.get("reason"),
    )


def _present_package_submit(p: dict) -> dict:
    return _simple(
        "Submeter à revisão",
        f"{_pkg_target(p)} da competência {_period_of(p)}",
        effect=(
            "a versão fica SUBMITTED e visível aos destinatários "
            "designados"
        ),
    )


def _present_assignment_create(p: dict) -> dict:
    scope = (
        f" (pacote {p['recipient_area']})"
        if p.get("recipient_area")
        else ""
    )
    return _simple(
        "Atribuir",
        (
            f"o papel {p.get('role')} a {p.get('subject')} na "
            f"competência {_period_of(p)}{scope}"
        ),
        effect="a atribuição de revisão fica ativa",
    )


def _present_assignment_deactivate(p: dict) -> dict:
    return _simple(
        "Desativar",
        f"a atribuição {_short(p.get('assignment_id'))} da "
        f"competência {_period_of(p)}",
        effect="o papel deixa de valer para novas revisões",
        motivation=p.get("reason"),
    )


def _present_start_review(p: dict) -> dict:
    return _simple(
        "Iniciar a revisão de",
        f"{_pkg_target(p)} da competência {_period_of(p)}",
        effect="a revisão da sua área fica em andamento",
    )


def _present_terminal_confirm(p: dict) -> dict:
    return _simple(
        "Confirmar a rejeição terminal da competência",
        _period_of(p),
        effect=(
            "DESTRUTIVO: congela as revisões do fechamento até "
            "reversão autorizada por coordenador"
        ),
        motivation=p.get("reason"),
    )


def _present_terminal_revert(p: dict) -> dict:
    return _simple(
        "Reverter a rejeição terminal da competência",
        _period_of(p),
        effect="as revisões voltam ao fluxo normal",
        motivation=p.get("reason"),
    )


def _present_item_reverse(p: dict) -> dict:
    return _simple(
        "Reverter a decisão",
        (
            f"{_short(p.get('decision_id'))} para "
            f"{p.get('result_state')} na competência {_period_of(p)}"
        ),
        effect="a decisão anterior é revertida com justificativa",
        motivation=p.get("justification"),
    )


def _present_item_na(p: dict) -> dict:
    return _simple(
        "Marcar como não aplicável",
        f"{_item_target(p)} da competência {_period_of(p)}",
        effect="o item deixa de exigir evidência no fechamento",
        motivation=p.get("justification"),
    )


def _present_item_revert_na(p: dict) -> dict:
    return _simple(
        "Reverter o não-aplicável de",
        f"{_item_target(p)} da competência {_period_of(p)}",
        effect="o item volta a exigir evidência",
        motivation=p.get("justification"),
    )


def _present_item_cancel(p: dict) -> dict:
    return _simple(
        "Cancelar",
        f"{_item_target(p)} da competência {_period_of(p)}",
        effect=(
            "DESTRUTIVO: o item é cancelado e não participa mais do "
            "fechamento"
        ),
        motivation=p.get("justification"),
    )


def _present_item_exceptional(p: dict) -> dict:
    return _simple(
        "Criar o item excepcional",
        (
            f"«{p.get('name')}» ({p.get('sheet')}) na competência "
            f"{_period_of(p)}"
        ),
        effect="o item excepcional entra no checklist da competência",
        motivation=p.get("justification"),
    )


def _present_item_correction(p: dict) -> dict:
    return _simple(
        "Solicitar correção de",
        f"{_item_target(p)} da competência {_period_of(p)}",
        effect="a correção fica pendente de revisão administrativa",
        motivation=p.get("justification"),
    )


def _present_item_correction_review(p: dict) -> dict:
    verb = "Aprovar" if p.get("approve") else "Rejeitar"
    return _simple(
        verb,
        (
            f"a correção {_short(p.get('correction_id'))} do item "
            f"{p.get('item_key')} na competência {_period_of(p)}"
        ),
        effect="a correção é aplicada ao item" if p.get("approve")
        else "a correção é rejeitada",
        motivation=p.get("review_reason"),
    )


def _present_doc_message(p: dict) -> dict:
    return _simple(
        "Registrar mensagem em",
        f"{_doc_target(p)} da competência {_period_of(p)}",
        effect="a mensagem entra na conversa do documento",
        motivation=p.get("body"),
    )


def _present_doc_cancel(p: dict) -> dict:
    return _simple(
        "Cancelar",
        f"{_doc_target(p)} da competência {_period_of(p)}",
        effect=(
            "DESTRUTIVO: o documento fica CANCELLED e não compõe "
            "mais evidências"
        ),
    )


def _present_doc_answer(p: dict) -> dict:
    return _simple(
        "Responder a solicitação de ajuste",
        (
            f"{_short(p.get('request_id'))} de {_doc_target(p)} da "
            f"competência {_period_of(p)}"
        ),
        effect="a solicitação fica respondida aguardando confirmação",
        motivation=p.get("answer_body"),
    )


def _present_recv_message(p: dict) -> dict:
    return _simple(
        "Enviar mensagem em",
        f"{_doc_target(p)} da competência {_period_of(p)}",
        effect="a mensagem é visível à Controladoria",
        motivation=p.get("body"),
    )


def _present_recv_adjustment(p: dict) -> dict:
    return _simple(
        "Abrir solicitação de ajuste em",
        f"{_doc_target(p)} da competência {_period_of(p)}",
        effect=(
            "a Controladoria recebe o pedido e responde na fila de "
            "ajustes"
        ),
        motivation=p.get("body"),
    )


def _present_recv_confirm(p: dict) -> dict:
    return _simple(
        "Confirmar a solicitação",
        (
            f"{_short(p.get('request_id'))} do documento "
            f"{_short(p.get('document_id'))} da competência "
            f"{_period_of(p)}"
        ),
        effect="a solicitação respondida fica CONFIRMED",
    )


def _present_catalog_create(p: dict) -> dict:
    return _simple(
        "Criar a entrada",
        (
            f"{p.get('code')} «{p.get('label')}» no catálogo "
            f"{p.get('catalog_key')}"
        ),
        effect="a entrada fica ativa para uso nas telas governadas",
    )


def _present_catalog_update(p: dict) -> dict:
    return _simple(
        "Atualizar a entrada",
        f"{p.get('code')} do catálogo {p.get('catalog_key')}",
        effect="rótulo/atributos vigentes mudam (versão incrementada)",
        motivation=p.get("label"),
    )


def _present_catalog_deactivate(p: dict) -> dict:
    return _simple(
        "Desativar a entrada",
        f"{p.get('code')} do catálogo {p.get('catalog_key')}",
        effect="a entrada sai do uso até reativação",
    )


def _present_catalog_reactivate(p: dict) -> dict:
    return _simple(
        "Reativar a entrada",
        f"{p.get('code')} do catálogo {p.get('catalog_key')}",
        effect="a entrada volta ao uso",
    )


def _present_tpl_draft_create(p: dict) -> dict:
    return _simple(
        "Criar rascunho de versão do template",
        _short(p.get("template_id")),
        effect="um novo rascunho editável é criado",
    )


def _present_tpl_draft_update(p: dict) -> dict:
    return _simple(
        "Editar os itens do rascunho",
        (
            f"v{p.get('version')} do template "
            f"{_short(p.get('template_id'))}"
        ),
        effect="o conjunto de itens do rascunho é substituído",
    )


def _present_tpl_submit(p: dict) -> dict:
    return _simple(
        "Submeter à revisão a versão",
        (
            f"v{p.get('version')} do template "
            f"{_short(p.get('template_id'))}"
        ),
        effect="a versão sai de rascunho para revisão",
    )


def _present_tpl_return(p: dict) -> dict:
    return _simple(
        "Devolver a rascunho a versão",
        (
            f"v{p.get('version')} do template "
            f"{_short(p.get('template_id'))}"
        ),
        effect="a versão volta a editável",
        motivation=p.get("reason"),
    )


def _present_tpl_discard(p: dict) -> dict:
    return _simple(
        "Descartar a versão",
        (
            f"v{p.get('version')} do template "
            f"{_short(p.get('template_id'))}"
        ),
        effect="DESTRUTIVO: a versão é descartada",
    )


def _present_tpl_publish(p: dict) -> dict:
    return _simple(
        "Publicar a versão",
        (
            f"v{p.get('version')} do template "
            f"{_short(p.get('template_id'))} a partir de "
            f"{period_label(p.get('effective_from_period'))}"
        ),
        effect="a versão vira o checklist vigente das próximas aberturas",
    )


def _present_tpl_inactivate(p: dict) -> dict:
    return _simple(
        "Inativar a versão",
        (
            f"v{p.get('version')} do template "
            f"{_short(p.get('template_id'))}"
        ),
        effect="a versão deixa de ser elegível a novas competências",
    )


def _present_tpl_doc_requirement(p: dict) -> dict:
    return _simple(
        "Atualizar o requisito documental do item",
        (
            f"{p.get('item_key')} do template "
            f"{_short(p.get('template_id'))}"
        ),
        effect=(
            "o documento exigido pelo item muda a partir da "
            "vigência informada"
        ),
    )


_PRESENTERS: dict[str, Callable[[dict], dict]] = {
    "evidence.decide_version": _evidence_version,
    "evidence.decide_item_set": _evidence_item_set,
    "review.record_decision": _review_decision,
    "clarification.open": _clarification_open,
    "clarification.resolve": _clarification_resolve,
    "competence.open": _present_competence_open,
    "pendency.create": _present_pendency_create,
    "pendency.claim": _present_pendency_claim,
    "pendency.reassign": _present_pendency_reassign,
    "pendency.transition": _present_pendency_transition,
    "pendency.confirm_classification": (
        _present_pendency_classification
    ),
    "p3.confirm_cutoff": _present_p3_cutoff,
    "p3.upsert_reconciliation": _present_p3_upsert,
    "p3.revalidate": _present_p3_revalidate,
    "package.finalize": _present_package_finalize,
    "package.reopen": _present_package_reopen,
    "package.complement": _present_package_complement,
    "package.submit_review": _present_package_submit,
    "package.assignment_create": _present_assignment_create,
    "package.assignment_deactivate": _present_assignment_deactivate,
    "package.start_review": _present_start_review,
    "package.confirm_terminal_rejection": _present_terminal_confirm,
    "package.revert_terminal_rejection": _present_terminal_revert,
    "item.reverse_decision": _present_item_reverse,
    "item.mark_not_applicable": _present_item_na,
    "item.revert_not_applicable": _present_item_revert_na,
    "item.cancel": _present_item_cancel,
    "item.create_exceptional": _present_item_exceptional,
    "item.request_correction": _present_item_correction,
    "item.review_correction": _present_item_correction_review,
    "document.post_message": _present_doc_message,
    "document.cancel": _present_doc_cancel,
    "document.answer_adjustment": _present_doc_answer,
    "received.post_message": _present_recv_message,
    "received.create_adjustment": _present_recv_adjustment,
    "received.confirm_adjustment": _present_recv_confirm,
    "catalog.entry_create": _present_catalog_create,
    "catalog.entry_update": _present_catalog_update,
    "catalog.entry_deactivate": _present_catalog_deactivate,
    "catalog.entry_reactivate": _present_catalog_reactivate,
    "checklist.draft_create": _present_tpl_draft_create,
    "checklist.draft_update": _present_tpl_draft_update,
    "checklist.version_submit": _present_tpl_submit,
    "checklist.version_return": _present_tpl_return,
    "checklist.version_discard": _present_tpl_discard,
    "checklist.version_publish": _present_tpl_publish,
    "checklist.version_inactivate": _present_tpl_inactivate,
    "checklist.doc_requirement": _present_tpl_doc_requirement,
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
