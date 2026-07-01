from __future__ import annotations

import uuid

import pytest

from cx_app.application.services.form_response_service import (
    FormResponseService,
    FormResponseValidationError,
)
from cx_app.application.services.form_service import FormNotFoundError
from cx_app.domain.form import AnswerInput, QuestionType, ResponseInput

_FORM_ID = "f1"
_TOKEN = "tok"


def _q(qid, qtype, *, required=False, options=None):
    return {
        "id": qid,
        "question_type": qtype,
        "label": f"Pergunta {qid}",
        "is_required": required,
        "options": options or [],
        "is_active": True,
    }


class FakeFormRepo:
    def __init__(self, active=True, questions=None):
        self.form = {"id": _FORM_ID, "public_token": _TOKEN, "is_active": active, "title": "F"}
        self.questions = questions or []
        self.increment = 0

    def get_by_token(self, token):
        return dict(self.form) if token == _TOKEN and self.form else None

    def get_by_id(self, form_id):
        return dict(self.form) if form_id == _FORM_ID else None

    def list_questions(self, form_id, *, active_only=False):
        return [dict(q) for q in self.questions]

    def increment_response_count(self, form_id):
        self.increment += 1


class FakeResponseRepo:
    def __init__(self):
        self.responses: list[dict] = []
        self.answers: list[dict] = []

    def create(self, response, answers):
        rid = str(uuid.uuid4())
        self.responses.append({"id": rid, **response})
        for a in answers:
            self.answers.append({"response_id": rid, **a})
        return {"id": rid}

    def count_by_form(self, form_id):
        return len(self.responses)

    def list_by_form(self, form_id, *, limit, offset):
        return list(reversed(self.responses))[offset:offset + limit]

    def answers_by_response_ids(self, ids):
        grouped: dict[str, list] = {}
        for a in self.answers:
            if a["response_id"] in ids:
                grouped.setdefault(a["response_id"], []).append(a)
        return grouped

    def answers_by_form(self, form_id):
        return list(self.answers)


def _service(active=True, questions=None):
    forms = FakeFormRepo(active=active, questions=questions)
    responses = FakeResponseRepo()
    return FormResponseService(form_repository=forms, response_repository=responses), forms, responses


def test_submit_builds_all_answer_types():
    questions = [
        _q("q1", QuestionType.RATING, required=True),
        _q("q2", QuestionType.SHORT_TEXT),
        _q("q3", QuestionType.SINGLE_CHOICE, options=["A", "B"]),
        _q("q4", QuestionType.MULTI_CHOICE, options=["X", "Y", "Z"]),
        _q("q5", QuestionType.YES_NO),
    ]
    service, forms, responses = _service(questions=questions)
    result = service.submit(
        _TOKEN,
        ResponseInput(
            respondent_name="Ana",
            respondent_company="ACME",
            answers=[
                AnswerInput(question_id="q1", rating=5),
                AnswerInput(question_id="q2", text="Muito bom"),
                AnswerInput(question_id="q3", text="A"),
                AnswerInput(question_id="q4", choices=["X", "Z"]),
                AnswerInput(question_id="q5", text="Sim"),
            ],
        ),
    )
    assert result["responseId"]
    assert forms.increment == 1
    assert len(responses.answers) == 5


def test_submit_required_missing_raises():
    service, _, _ = _service(questions=[_q("q1", QuestionType.RATING, required=True)])
    with pytest.raises(FormResponseValidationError):
        service.submit(_TOKEN, ResponseInput(respondent_name="Ana", respondent_company=None, answers=[]))


def test_submit_no_name_raises():
    service, _, _ = _service(questions=[])
    with pytest.raises(FormResponseValidationError):
        service.submit(_TOKEN, ResponseInput(respondent_name="  ", respondent_company=None, answers=[]))


def test_submit_invalid_rating_raises():
    service, _, _ = _service(questions=[_q("q1", QuestionType.RATING)])
    with pytest.raises(FormResponseValidationError):
        service.submit(
            _TOKEN,
            ResponseInput(respondent_name="Ana", respondent_company=None,
                          answers=[AnswerInput(question_id="q1", rating=9)]),
        )


def test_submit_invalid_option_raises():
    service, _, _ = _service(questions=[_q("q1", QuestionType.SINGLE_CHOICE, options=["A", "B"])])
    with pytest.raises(FormResponseValidationError):
        service.submit(
            _TOKEN,
            ResponseInput(respondent_name="Ana", respondent_company=None,
                          answers=[AnswerInput(question_id="q1", text="Z")]),
        )


def test_submit_inactive_form_raises_not_found():
    service, _, _ = _service(active=False, questions=[])
    with pytest.raises(FormNotFoundError):
        service.submit(_TOKEN, ResponseInput(respondent_name="Ana", respondent_company=None, answers=[]))


def test_dashboard_aggregates_rating_and_choices():
    questions = [
        _q("q1", QuestionType.RATING),
        _q("q2", QuestionType.SINGLE_CHOICE, options=["A", "B"]),
    ]
    service, _, _ = _service(questions=questions)
    for rating, choice in [(5, "A"), (3, "A"), (4, "B")]:
        service.submit(
            _TOKEN,
            ResponseInput(respondent_name="X", respondent_company=None, answers=[
                AnswerInput(question_id="q1", rating=rating),
                AnswerInput(question_id="q2", text=choice),
            ]),
        )
    dash = service.dashboard(_FORM_ID)
    assert dash["totalResponses"] == 3
    rating_q = next(q for q in dash["questions"] if q["id"] == "q1")
    assert rating_q["average"] == 4.0
    assert rating_q["distribution"]["5"] == 1
    choice_q = next(q for q in dash["questions"] if q["id"] == "q2")
    assert choice_q["optionCounts"] == {"A": 2, "B": 1}


def test_list_responses_returns_items_with_answers():
    service, _, _ = _service(questions=[_q("q1", QuestionType.SHORT_TEXT)])
    service.submit(
        _TOKEN,
        ResponseInput(respondent_name="Ana", respondent_company="ACME",
                      answers=[AnswerInput(question_id="q1", text="Top")]),
    )
    listing = service.list_responses(_FORM_ID, limit=10, offset=0)
    assert listing["total"] == 1
    assert listing["items"][0]["respondentName"] == "Ana"
    assert listing["items"][0]["answers"][0]["value"] == "Top"
