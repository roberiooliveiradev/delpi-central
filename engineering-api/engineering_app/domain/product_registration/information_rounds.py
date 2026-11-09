"""PRC-REF-019 — rodadas de esclarecimento com o solicitante.

Comunicação formal analista ↔ solicitante: perguntas tipadas por alvo
técnico, respostas rastreáveis, avaliação e complemento. Independente
das bandeiras D16 (anotações internas). Não escreve SB1/SA5/TOTVS.
"""

from __future__ import annotations

from typing import Any

from engineering_app.domain.product_registration import catalog
from engineering_app.domain.product_registration.errors import (
    PrcValidationError,
)

ROUND_STATUSES = (
    "awaiting_requester",
    "awaiting_review",
    "resolved",
)
QUESTION_STATUSES = (
    "pending",
    "drafted",
    "submitted",
    "accepted",
    "follow_up_requested",
)
QUESTION_TARGETS = ("FIELD", "SUPPLIER_LINK", "GENERAL")
SUPPLIER_QUESTION_ATTRIBUTES = ("partNumber", "catalogNumber")

QUESTION_TEXT_MAX = 1000
ANSWER_TEXT_MAX = 4000
MESSAGE_MAX = 1000
MAX_QUESTIONS_PER_ROUND = 20

_FIELD_PATHS = frozenset(
    spec.path
    for spec in catalog.FIELD_SPECS
    if spec.path != "officialProductCode" and spec.kind != "suppliers"
)

# Transições de status da rodada (ator → pós-condição).
_ROUND_TRANSITIONS: dict[str, tuple[frozenset[str], str]] = {
    "submit_answers": (
        frozenset({"awaiting_requester"}),
        "awaiting_review",
    ),
    "resolve": (
        frozenset({"awaiting_review"}),
        "resolved",
    ),
    "reopen_for_follow_up": (
        frozenset({"awaiting_review"}),
        "resolved",  # rodada atual encerra; nova rodada nasce separada
    ),
}


def questionable_field_paths() -> tuple[str, ...]:
    """Paths SB1 elegíveis como alvo FIELD (ordem do catálogo)."""
    return tuple(
        spec.path
        for spec in catalog.FIELD_SPECS
        if spec.path in _FIELD_PATHS
    )


# Rótulos PT somente para texto de pergunta legado / targetLabel —
# catálogo técnico não carrega locale; UI também possui PRC_FIELD_LABELS.
_FIELD_LABELS_PT: dict[str, str] = {
    "description": "Descrição",
    "group": "Grupo",
    "type": "Tipo",
    "unit": "Unidade",
    "ncm": "NCM",
    "origin": "Origem",
    "secondUnit": "2ª unidade",
    "conversionFactor": "Fator de conversão",
    "account": "Conta contábil",
    "warehouse": "Armazém",
    "traceability": "Rastreabilidade",
}


def field_label(path: str) -> str:
    return _FIELD_LABELS_PT.get(path, path)


def normalize_question_target(
    *,
    target_type: str,
    target_path: str | None = None,
    supplier_key: dict | None = None,
    target_attribute: str | None = None,
) -> dict[str, Any]:
    """Valida e normaliza o alvo tipado de uma pergunta."""
    kind = str(target_type or "").strip().upper()
    if kind not in QUESTION_TARGETS:
        raise PrcValidationError(
            "targetType inválido.",
            fields={"targetType": "enum"},
        )
    if kind == "FIELD":
        path = str(target_path or "").strip()
        if not path:
            raise PrcValidationError(
                "targetPath é obrigatório para FIELD.",
                fields={"targetPath": "required"},
            )
        if path not in _FIELD_PATHS:
            raise PrcValidationError(
                "Campo técnico inexistente ou não questionável.",
                fields={"targetPath": "unknown"},
            )
        return {
            "target_type": "FIELD",
            "target_path": path,
            "target_attribute": None,
            "supplier_key": None,
            "target_key": f"FIELD:{path}",
            "target_label": field_label(path),
        }
    if kind == "SUPPLIER_LINK":
        if not isinstance(supplier_key, dict):
            raise PrcValidationError(
                "supplierKey é obrigatório para SUPPLIER_LINK.",
                fields={"supplierKey": "required"},
            )
        code = str(supplier_key.get("supplierCode") or "").strip()
        store = str(supplier_key.get("store") or "").strip()
        attr = str(target_attribute or "").strip()
        if not code or not store:
            raise PrcValidationError(
                "supplierKey exige supplierCode e store.",
                fields={"supplierKey": "required"},
            )
        if attr not in SUPPLIER_QUESTION_ATTRIBUTES:
            raise PrcValidationError(
                "targetAttribute inválido para SUPPLIER_LINK.",
                fields={"targetAttribute": "enum"},
            )
        label = f"Fornecedor {code}/{store} · {attr}"
        return {
            "target_type": "SUPPLIER_LINK",
            "target_path": None,
            "target_attribute": attr,
            "supplier_key": {"supplierCode": code, "store": store},
            "target_key": f"SUPPLIER:{code}|{store}|{attr}",
            "target_label": label,
        }
    # GENERAL
    return {
        "target_type": "GENERAL",
        "target_path": None,
        "target_attribute": None,
        "supplier_key": None,
        "target_key": "GENERAL",
        "target_label": "Esclarecimento geral",
    }


def validate_questions_payload(
    questions: Any,
    *,
    require_at_least_one: bool = True,
) -> list[dict[str, Any]]:
    """Normaliza lista de perguntas do analista."""
    if questions is None:
        questions = []
    if not isinstance(questions, list):
        raise PrcValidationError(
            "questions deve ser uma lista.",
            fields={"questions": "type"},
        )
    if require_at_least_one and len(questions) < 1:
        raise PrcValidationError(
            "Informe ao menos uma pergunta.",
            fields={"questions": "required"},
        )
    if len(questions) > MAX_QUESTIONS_PER_ROUND:
        raise PrcValidationError(
            f"Máximo de {MAX_QUESTIONS_PER_ROUND} perguntas por rodada.",
            fields={"questions": "max_items"},
        )
    out: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for idx, raw in enumerate(questions):
        if not isinstance(raw, dict):
            raise PrcValidationError(
                f"Pergunta {idx + 1} inválida.",
                fields={f"questions[{idx}]": "type"},
            )
        text = str(raw.get("questionText") or raw.get("question_text") or "").strip()
        if not text:
            raise PrcValidationError(
                "Texto da pergunta é obrigatório.",
                fields={f"questions[{idx}].questionText": "required"},
            )
        if len(text) > QUESTION_TEXT_MAX:
            raise PrcValidationError(
                f"Pergunta excede {QUESTION_TEXT_MAX} caracteres.",
                fields={f"questions[{idx}].questionText": "max_length"},
            )
        target = normalize_question_target(
            target_type=str(
                raw.get("targetType") or raw.get("target_type") or "GENERAL"
            ),
            target_path=raw.get("targetPath") or raw.get("target_path"),
            supplier_key=raw.get("supplierKey") or raw.get("supplier_key"),
            target_attribute=(
                raw.get("targetAttribute") or raw.get("target_attribute")
            ),
        )
        # GENERAL pode repetir; FIELD/SUPPLIER únicos por rodada.
        if target["target_type"] != "GENERAL":
            if target["target_key"] in seen_keys:
                raise PrcValidationError(
                    "Alvo duplicado na mesma rodada.",
                    fields={f"questions[{idx}].target": "duplicate"},
                )
            seen_keys.add(target["target_key"])
        out.append(
            {
                "ordinal": idx + 1,
                "question_text": text,
                "status": "pending",
                **target,
            }
        )
    return out


def validate_answer_text(text: Any, *, field_key: str = "text") -> str:
    value = str(text or "").strip()
    if not value:
        raise PrcValidationError(
            "Texto da resposta é obrigatório.",
            fields={field_key: "required"},
        )
    if len(value) > ANSWER_TEXT_MAX:
        raise PrcValidationError(
            f"Resposta excede {ANSWER_TEXT_MAX} caracteres.",
            fields={field_key: "max_length"},
        )
    return value


def validate_message(message: Any) -> str | None:
    if message is None:
        return None
    text = str(message).strip()
    if not text:
        return None
    if len(text) > MESSAGE_MAX:
        raise PrcValidationError(
            f"Mensagem excede {MESSAGE_MAX} caracteres.",
            fields={"message": "max_length"},
        )
    return text


def pending_fields_from_questions(questions: list[dict[str, Any]]) -> list[str]:
    """Deriva pendingFields legados a partir dos alvos tipados."""
    fields: list[str] = []
    for q in questions:
        if q.get("target_type") == "FIELD" and q.get("target_path"):
            path = str(q["target_path"])
            if path not in fields:
                fields.append(path)
        elif q.get("target_type") == "SUPPLIER_LINK":
            key = str(q.get("target_key") or "")
            if key and key not in fields:
                fields.append(key)
    return fields


def legacy_questions_from_reason(
    *,
    reason: str,
    pending_fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Compatibilidade: motivo + pendingFields → perguntas GENERAL/FIELD."""
    questions: list[dict[str, Any]] = []
    for path in pending_fields or []:
        p = str(path or "").strip()
        if not p:
            continue
        if p in _FIELD_PATHS:
            questions.append(
                {
                    "targetType": "FIELD",
                    "targetPath": p,
                    "questionText": (
                        f"Esclareça o campo «{field_label(p)}»: {reason}"
                    )[:QUESTION_TEXT_MAX],
                }
            )
        else:
            questions.append(
                {
                    "targetType": "GENERAL",
                    "questionText": (
                        f"Esclareça «{p}»: {reason}"
                    )[:QUESTION_TEXT_MAX],
                }
            )
    if not questions:
        questions.append(
            {
                "targetType": "GENERAL",
                "questionText": reason[:QUESTION_TEXT_MAX],
            }
        )
    return validate_questions_payload(questions)


def round_allows_requester_write(status: str) -> bool:
    return status == "awaiting_requester"


def round_allows_analyst_review(status: str) -> bool:
    return status == "awaiting_review"


def all_questions_accepted(questions: list[dict[str, Any]]) -> bool:
    if not questions:
        return False
    return all(q.get("status") == "accepted" for q in questions)


def has_open_information_blocker(
    rounds: list[dict[str, Any]],
) -> bool:
    """True quando existe rodada ativa impedindo resume."""
    for rnd in rounds:
        status = rnd.get("status")
        if status in ("awaiting_requester", "awaiting_review"):
            return True
    return False


def public_question_view(question: dict[str, Any]) -> dict[str, Any]:
    answer = question.get("answer")
    answer_view = None
    if isinstance(answer, dict):
        answer_view = {
            "id": answer.get("id"),
            "text": answer.get("text"),
            "status": answer.get("status"),
            "version": answer.get("row_version") or answer.get("version"),
            "submittedAt": answer.get("submitted_at"),
            "updatedAt": answer.get("updated_at"),
            "authorSubject": answer.get("author_subject"),
        }
    return {
        "id": question["id"],
        "ordinal": question.get("ordinal"),
        "targetType": question.get("target_type"),
        "targetPath": question.get("target_path"),
        "targetAttribute": question.get("target_attribute"),
        "supplierKey": question.get("supplier_key"),
        "targetKey": question.get("target_key"),
        "targetLabel": question.get("target_label"),
        "questionText": question.get("question_text"),
        "status": question.get("status"),
        "answer": answer_view,
    }


def public_round_view(
    round_row: dict[str, Any],
    *,
    include_internal: bool = False,
) -> dict[str, Any]:
    questions = [
        public_question_view(q) for q in (round_row.get("questions") or [])
    ]
    view = {
        "id": round_row["id"],
        "requestId": round_row["request_id"],
        "sequence": round_row.get("sequence"),
        "originStatus": round_row.get("origin_status"),
        "status": round_row.get("status"),
        "requestedBy": {
            "subject": round_row.get("requested_by_subject"),
            "displayName": round_row.get("requested_by_display_name"),
        },
        "requesterSubject": round_row.get("requester_subject"),
        "message": round_row.get("message"),
        "version": round_row.get("row_version"),
        "createdAt": round_row.get("created_at"),
        "updatedAt": round_row.get("updated_at"),
        "resolvedAt": round_row.get("resolved_at"),
        "questions": questions,
    }
    if include_internal:
        view["parentRoundId"] = round_row.get("parent_round_id")
    return view
