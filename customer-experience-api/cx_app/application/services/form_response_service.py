from __future__ import annotations

from typing import Any

from cx_app.application.services.form_service import FormNotFoundError
from cx_app.domain.form import AnswerInput, QuestionType, ResponseInput
from cx_app.infrastructure.persistence.form_repository import FormRepository
from cx_app.infrastructure.persistence.form_response_repository import (
    FormResponseRepository,
)

RATING_MIN = 1
RATING_MAX = 5
MAX_TEXT_LEN = 2000
TEXT_SAMPLE_LIMIT = 100
YES_NO_OPTIONS = ["Sim", "Não"]


class FormResponseValidationError(ValueError):
    """Resposta de formulário inválida."""


class FormResponseService:
    def __init__(
        self,
        form_repository: FormRepository | None = None,
        response_repository: FormResponseRepository | None = None,
    ) -> None:
        self.forms = form_repository or FormRepository()
        self.responses = response_repository or FormResponseRepository()

    # ----- submissão (público) --------------------------------------------

    def submit(self, token: str, data: ResponseInput) -> dict[str, Any]:
        form = self.forms.get_by_token(token)
        if not form or not form.get("is_active"):
            raise FormNotFoundError(token)

        name = _clean(data.respondent_name)
        if not name:
            raise FormResponseValidationError("Informe seu nome.")

        questions = self.forms.list_questions(form["id"], active_only=True)
        by_id = {str(q["id"]): q for q in questions}
        provided = {str(a.question_id): a for a in data.answers}

        answer_rows: list[dict[str, Any]] = []
        for qid, question in by_id.items():
            answer = provided.get(qid)
            row = self._build_answer(question, answer)
            if row is not None:
                answer_rows.append(row)

        created = self.responses.create(
            {
                "form_id": form["id"],
                "respondent_name": name,
                "respondent_company": _clean(data.respondent_company),
            },
            answer_rows,
        )
        self.forms.increment_response_count(form["id"])
        return {"responseId": created.get("id")}

    def _build_answer(
        self, question: dict[str, Any], answer: AnswerInput | None
    ) -> dict[str, Any] | None:
        qid = str(question["id"])
        qtype = question["question_type"]
        required = bool(question.get("is_required"))
        label = question.get("label")
        options = question.get("options") or []

        def missing() -> None:
            if required:
                raise FormResponseValidationError(f"Responda: {label}")

        if answer is None:
            missing()
            return None

        if qtype == QuestionType.RATING:
            if answer.rating is None:
                missing()
                return None
            if not (RATING_MIN <= int(answer.rating) <= RATING_MAX):
                raise FormResponseValidationError(f"Nota inválida em: {label}")
            return {"question_id": qid, "answer_rating": int(answer.rating)}

        if qtype in (QuestionType.SHORT_TEXT, QuestionType.LONG_TEXT):
            text = _clean(answer.text)
            if not text:
                missing()
                return None
            return {"question_id": qid, "answer_text": text}

        if qtype in (QuestionType.SINGLE_CHOICE, QuestionType.YES_NO):
            valid = YES_NO_OPTIONS if qtype == QuestionType.YES_NO else options
            text = _clean(answer.text)
            if not text:
                missing()
                return None
            if text not in valid:
                raise FormResponseValidationError(f"Opção inválida em: {label}")
            return {"question_id": qid, "answer_text": text}

        if qtype == QuestionType.MULTI_CHOICE:
            chosen = [c for c in (_clean(x) or "" for x in answer.choices) if c]
            invalid = [c for c in chosen if c not in options]
            if invalid:
                raise FormResponseValidationError(f"Opção inválida em: {label}")
            if not chosen:
                missing()
                return None
            return {"question_id": qid, "answer_choices": chosen}

        return None

    # ----- consultas (admin) ----------------------------------------------

    def list_responses(
        self, form_id: str, *, limit: int, offset: int
    ) -> dict[str, Any]:
        form = self._require_form(form_id)
        questions = self.forms.list_questions(form_id, active_only=False)
        q_by_id = {str(q["id"]): q for q in questions}

        responses = self.responses.list_by_form(form_id, limit=limit, offset=offset)
        ids = [str(r["id"]) for r in responses]
        answers = self.responses.answers_by_response_ids(ids)

        items = []
        for r in responses:
            rid = str(r["id"])
            rendered = []
            for a in answers.get(rid, []):
                q = q_by_id.get(str(a["question_id"]))
                rendered.append(
                    {
                        "questionId": str(a["question_id"]),
                        "label": q.get("label") if q else None,
                        "type": q.get("question_type") if q else None,
                        "value": _answer_value(a),
                    }
                )
            items.append(
                {
                    "id": rid,
                    "respondentName": r.get("respondent_name"),
                    "respondentCompany": r.get("respondent_company"),
                    "createdAt": r.get("created_at"),
                    "answers": rendered,
                }
            )
        return {
            "items": items,
            "total": self.responses.count_by_form(form_id),
            "limit": limit,
            "offset": offset,
        }

    def dashboard(self, form_id: str) -> dict[str, Any]:
        form = self._require_form(form_id)
        questions = self.forms.list_questions(form_id, active_only=False)
        answers = self.responses.answers_by_form(form_id)

        by_question: dict[str, list[dict[str, Any]]] = {}
        for a in answers:
            by_question.setdefault(str(a["question_id"]), []).append(a)

        summary = [
            self._aggregate_question(q, by_question.get(str(q["id"]), []))
            for q in questions
        ]
        return {
            "formId": form_id,
            "title": form.get("title"),
            "totalResponses": self.responses.count_by_form(form_id),
            "questions": summary,
        }

    def _aggregate_question(
        self, question: dict[str, Any], answers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        qtype = question["question_type"]
        base = {
            "id": str(question["id"]),
            "label": question.get("label"),
            "type": qtype,
            "active": question.get("is_active"),
            "answered": len(answers),
        }

        if qtype == QuestionType.RATING:
            ratings = [int(a["answer_rating"]) for a in answers if a.get("answer_rating") is not None]
            distribution = {str(n): 0 for n in range(RATING_MIN, RATING_MAX + 1)}
            for r in ratings:
                distribution[str(r)] = distribution.get(str(r), 0) + 1
            base["average"] = round(sum(ratings) / len(ratings), 2) if ratings else None
            base["distribution"] = distribution
            return base

        if qtype in (
            QuestionType.SINGLE_CHOICE,
            QuestionType.YES_NO,
            QuestionType.MULTI_CHOICE,
        ):
            counts: dict[str, int] = {}
            options = (
                YES_NO_OPTIONS
                if qtype == QuestionType.YES_NO
                else (question.get("options") or [])
            )
            for opt in options:
                counts[opt] = 0
            for a in answers:
                if qtype == QuestionType.MULTI_CHOICE:
                    for c in a.get("answer_choices") or []:
                        counts[c] = counts.get(c, 0) + 1
                else:
                    text = a.get("answer_text")
                    if text is not None:
                        counts[text] = counts.get(text, 0) + 1
            base["optionCounts"] = counts
            return base

        # texto curto/longo: amostra dos textos
        base["samples"] = [
            a["answer_text"] for a in answers if a.get("answer_text")
        ][:TEXT_SAMPLE_LIMIT]
        return base

    def _require_form(self, form_id: str) -> dict[str, Any]:
        form = self.forms.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id)
        return form


def _answer_value(a: dict[str, Any]) -> Any:
    if a.get("answer_rating") is not None:
        return a["answer_rating"]
    if a.get("answer_choices"):
        return a["answer_choices"]
    return a.get("answer_text")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped[:MAX_TEXT_LEN] if stripped else None
