from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cipa_app.application.security import cipa_permissions as perms
from cipa_app.application.services.sipat_excel_export_service import (
    build_sipat_results_xlsx,
    group_response_answers,
)
from cipa_app.application.services.sipat_qr_service import (
    SipatQrService,
    build_sipat_public_url,
)
from cipa_app.application.services.token_service import generate_public_token
from cipa_app.infrastructure.persistence.repositories.sipat_survey_repository import (
    SipatSurveyRepository,
)

QUESTION_TYPES = frozenset(
    {
        "single_choice",
        "multi_choice",
        "likert_5",
        "yes_no",
        "text_short",
        "text_long",
    }
)
CHOICE_TYPES = frozenset({"single_choice", "multi_choice"})
LIKERT_LABELS = ["1", "2", "3", "4", "5"]
YES_NO_OPTIONS = ["Sim", "Não"]

SIPAT_TEMPLATES: dict[str, dict[str, Any]] = {
    "clima_basico": {
        "title": "Pesquisa de clima — SIPAT",
        "description": (
            "Avaliação anônima sobre segurança, bem-estar e participação "
            "durante a SIPAT."
        ),
        "questions": [
            {
                "question_type": "likert_5",
                "label": "Como você avalia a organização geral da SIPAT?",
                "is_required": True,
                "help_text": "1 = muito ruim · 5 = excelente",
            },
            {
                "question_type": "likert_5",
                "label": "As palestras e atividades foram úteis para o seu dia a dia?",
                "is_required": True,
            },
            {
                "question_type": "yes_no",
                "label": "Você se sente mais preparado(a) para prevenir acidentes após a SIPAT?",
                "is_required": True,
            },
            {
                "question_type": "single_choice",
                "label": "Qual formato de atividade você mais valoriza?",
                "is_required": True,
                "options": [
                    "Palestras",
                    "Dinâmicas práticas",
                    "Blitze / inspeções",
                    "Concurso / gamificação",
                    "Outros",
                ],
            },
            {
                "question_type": "multi_choice",
                "label": "Quais temas gostaria de ver na próxima SIPAT?",
                "is_required": False,
                "options": [
                    "Ergonomia",
                    "EPI",
                    "Saúde mental",
                    "Primeiros socorros",
                    "Meio ambiente",
                    "Qualidade de vida",
                ],
            },
            {
                "question_type": "text_long",
                "label": "Sugestões ou comentários (opcional)",
                "is_required": False,
            },
        ],
    },
    "seguranca_rapida": {
        "title": "Checklist rápido — SIPAT",
        "description": "Pesquisa curta e anônima sobre percepção de segurança.",
        "questions": [
            {
                "question_type": "yes_no",
                "label": "Você conhece os canais para reportar riscos na empresa?",
                "is_required": True,
            },
            {
                "question_type": "likert_5",
                "label": "Quão seguro(a) você se sente no seu posto de trabalho?",
                "is_required": True,
            },
            {
                "question_type": "text_short",
                "label": "Cite um ponto de melhoria em segurança (opcional)",
                "is_required": False,
            },
        ],
    },
}


class SipatSurveyService:
    def __init__(
        self,
        repository: SipatSurveyRepository | None = None,
        qr_service: SipatQrService | None = None,
    ) -> None:
        self.repo = repository or SipatSurveyRepository()
        self.qr = qr_service or SipatQrService()

    def _user_id(self, user) -> str:
        return str(getattr(user, "id", None) or getattr(user, "sub", None) or "")

    def list_templates(self) -> list[dict[str, Any]]:
        return [
            {
                "id": key,
                "title": value["title"],
                "description": value["description"],
                "question_count": len(value["questions"]),
            }
            for key, value in SIPAT_TEMPLATES.items()
        ]

    def list_surveys(self, user, *, unit_code: str) -> dict[str, Any]:
        code = perms.normalize_unit_code(unit_code)
        if not code:
            raise ValueError("Unidade inválida.")
        perms.assert_unit_action(user, "sipat_view", code)
        items = self.repo.list_surveys(unit_code=code)
        return {
            "unit_code": code,
            "items": [self._survey_summary(item) for item in items],
            "templates": self.list_templates(),
        }

    def get_survey(self, user, survey_id: str) -> dict[str, Any]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_view", survey["unit_code"])
        questions = self.repo.list_questions(survey_id)
        return self._survey_detail(survey, questions)

    def create_survey(self, user, payload: dict[str, Any]) -> dict[str, Any]:
        code = perms.normalize_unit_code(str(payload.get("unit_code") or ""))
        if not code:
            raise ValueError("Unidade inválida.")
        perms.assert_unit_action(user, "sipat_manage", code)
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("Informe o título da pesquisa.")
        template_id = str(payload.get("template_id") or "").strip()
        questions_payload = payload.get("questions")
        if template_id:
            template = SIPAT_TEMPLATES.get(template_id)
            if not template:
                raise ValueError("Template SIPAT inválido.")
            if not title:
                title = template["title"]
            if not payload.get("description"):
                payload = {**payload, "description": template["description"]}
            if not questions_payload:
                questions_payload = template["questions"]

        survey = self.repo.create_survey(
            {
                "unit_code": code,
                "title": title[:200],
                "description": (str(payload.get("description") or "").strip() or None),
                "opens_at": payload.get("opens_at"),
                "closes_at": payload.get("closes_at"),
                "created_by_user_id": self._user_id(user),
            }
        )
        questions = self._normalize_questions(questions_payload or [])
        stored = self.repo.replace_questions(str(survey["id"]), questions)
        return self._survey_detail(survey, stored)

    def update_survey(self, user, survey_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_manage", survey["unit_code"])
        if survey["status"] != "draft" and "questions" in payload:
            raise ValueError("Só é possível editar perguntas em rascunho.")

        fields: dict[str, Any] = {"updated_by_user_id": self._user_id(user)}
        if "title" in payload:
            title = str(payload.get("title") or "").strip()
            if not title:
                raise ValueError("Informe o título da pesquisa.")
            fields["title"] = title[:200]
        if "description" in payload:
            fields["description"] = str(payload.get("description") or "").strip() or None
        if "opens_at" in payload:
            fields["opens_at"] = payload.get("opens_at")
        if "closes_at" in payload:
            fields["closes_at"] = payload.get("closes_at")

        updated = self.repo.update_survey(survey_id, fields) or survey
        questions = self.repo.list_questions(survey_id)
        if survey["status"] == "draft" and "questions" in payload:
            normalized = self._normalize_questions(payload.get("questions") or [])
            questions = self.repo.replace_questions(survey_id, normalized)
        return self._survey_detail(updated, questions)

    def apply_template(self, user, survey_id: str, template_id: str) -> dict[str, Any]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_manage", survey["unit_code"])
        if survey["status"] != "draft":
            raise ValueError("Template só pode ser aplicado em rascunho.")
        template = SIPAT_TEMPLATES.get(template_id)
        if not template:
            raise ValueError("Template SIPAT inválido.")
        updated = self.repo.update_survey(
            survey_id,
            {
                "title": template["title"][:200],
                "description": template["description"],
                "updated_by_user_id": self._user_id(user),
            },
        )
        questions = self.repo.replace_questions(
            survey_id, self._normalize_questions(template["questions"])
        )
        return self._survey_detail(updated or survey, questions)

    def clone_survey(self, user, survey_id: str) -> dict[str, Any]:
        """Cria rascunho com as mesmas perguntas; sem token/QR/respostas."""
        source = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_manage", source["unit_code"])
        questions = self.repo.list_questions(survey_id)
        base_title = str(source.get("title") or "Pesquisa SIPAT").strip()
        clone_title = f"Cópia de {base_title}"[:200]
        created = self.repo.create_survey(
            {
                "unit_code": source["unit_code"],
                "title": clone_title,
                "description": source.get("description"),
                "opens_at": None,
                "closes_at": None,
                "created_by_user_id": self._user_id(user),
            }
        )
        payload = [
            {
                "question_type": q["question_type"],
                "label": q["label"],
                "help_text": q.get("help_text"),
                "is_required": q.get("is_required", True),
                "options": q.get("options"),
            }
            for q in questions
        ]
        stored = self.repo.replace_questions(
            str(created["id"]), self._normalize_questions(payload)
        )
        return self._survey_detail(created, stored)

    def publish(self, user, survey_id: str) -> dict[str, Any]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_manage", survey["unit_code"])
        if survey["status"] == "closed":
            raise ValueError("Pesquisa encerrada não pode ser republicada.")
        questions = self.repo.list_questions(survey_id)
        if not questions:
            raise ValueError("Adicione ao menos uma pergunta antes de publicar.")

        token = survey.get("public_token") or generate_public_token()
        if survey.get("qr_filename"):
            self.qr.delete(str(survey["qr_filename"]))
        qr_filename = self.qr.generate(token=str(token))
        updated = self.repo.update_survey(
            survey_id,
            {
                "status": "published",
                "public_token": token,
                "qr_filename": qr_filename,
                "updated_by_user_id": self._user_id(user),
            },
        )
        return self._survey_detail(updated or survey, questions)

    def close(self, user, survey_id: str) -> dict[str, Any]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_manage", survey["unit_code"])
        if survey["status"] != "published":
            raise ValueError("Somente pesquisas publicadas podem ser encerradas.")
        updated = self.repo.update_survey(
            survey_id,
            {
                "status": "closed",
                "updated_by_user_id": self._user_id(user),
            },
        )
        questions = self.repo.list_questions(survey_id)
        return self._survey_detail(updated or survey, questions)

    def delete_survey(self, user, survey_id: str) -> dict[str, Any]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_manage", survey["unit_code"])
        if survey.get("qr_filename"):
            self.qr.delete(str(survey["qr_filename"]))
        deleted = self.repo.soft_delete(survey_id, actor_user_id=self._user_id(user))
        return {"survey": self._survey_summary(deleted or survey)}

    def qr_bytes(self, user, survey_id: str) -> tuple[bytes, str]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_view", survey["unit_code"])
        filename = survey.get("qr_filename")
        if not filename:
            raise LookupError("QR ainda não gerado. Publique a pesquisa.")
        raw = self.qr.read(str(filename))
        if not raw:
            raise LookupError("Arquivo do QR não encontrado.")
        return raw, str(filename)

    def summary(self, user, survey_id: str) -> dict[str, Any]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_view", survey["unit_code"])
        questions = self.repo.list_questions(survey_id)
        answers = self.repo.list_answers_for_survey(survey_id)
        return {
            "survey": self._survey_summary(survey),
            "response_count": int(survey.get("response_count") or 0),
            "questions": self._build_question_summaries(
                questions, answers, text_limit=50
            ),
        }

    def export_excel(self, user, survey_id: str) -> tuple[bytes, str]:
        survey = self._require_survey(survey_id)
        perms.assert_unit_action(user, "sipat_view", survey["unit_code"])
        questions = self.repo.list_questions(survey_id)
        answers = self.repo.list_answers_for_survey(survey_id)
        flat_rows = self.repo.list_response_answer_rows(survey_id)
        responses = group_response_answers(flat_rows)
        return build_sipat_results_xlsx(
            survey=self._survey_summary(survey),
            questions=questions,
            summary_questions=self._build_question_summaries(
                questions, answers, text_limit=None
            ),
            responses=responses,
        )

    def _build_question_summaries(
        self,
        questions: list[dict[str, Any]],
        answers: list[dict[str, Any]],
        *,
        text_limit: int | None = 50,
    ) -> list[dict[str, Any]]:
        by_question: dict[str, list[dict[str, Any]]] = {}
        for answer in answers:
            qid = str(answer["question_id"])
            by_question.setdefault(qid, []).append(answer)

        question_summaries = []
        for question in questions:
            qid = str(question["id"])
            q_answers = by_question.get(qid, [])
            qtype = str(question["question_type"])
            entry: dict[str, Any] = {
                "question_id": qid,
                "label": question["label"],
                "question_type": qtype,
                "answer_count": len(q_answers),
            }
            if qtype in CHOICE_TYPES or qtype in {"likert_5", "yes_no"}:
                counts: dict[str, int] = {}
                for item in q_answers:
                    values: list[str] = []
                    if item.get("value_json") is not None:
                        raw = item["value_json"]
                        if isinstance(raw, list):
                            values = [str(v) for v in raw]
                        else:
                            values = [str(raw)]
                    elif item.get("value_text"):
                        values = [str(item["value_text"])]
                    for value in values:
                        counts[value] = counts.get(value, 0) + 1
                entry["counts"] = counts
            else:
                texts = [
                    str(item.get("value_text") or "").strip()
                    for item in q_answers
                    if str(item.get("value_text") or "").strip()
                ]
                entry["sample_texts"] = (
                    texts if text_limit is None else texts[:text_limit]
                )
            question_summaries.append(entry)
        return question_summaries

    def get_public(self, token: str) -> dict[str, Any]:
        survey = self.repo.get_by_token(token)
        if not survey:
            raise LookupError("Pesquisa não encontrada.")
        self._assert_accepting_responses(survey)
        questions = self.repo.list_questions(str(survey["id"]))
        return {
            "id": str(survey["id"]),
            "title": survey["title"],
            "description": survey.get("description"),
            "unit_code": survey["unit_code"],
            "questions": [self._public_question(q) for q in questions],
        }

    def submit_public(self, token: str, payload: dict[str, Any]) -> dict[str, Any]:
        survey = self.repo.get_by_token(token)
        if not survey:
            raise LookupError("Pesquisa não encontrada.")
        self._assert_accepting_responses(survey)
        questions = self.repo.list_questions(str(survey["id"]))
        by_id = {str(q["id"]): q for q in questions}
        raw_answers = payload.get("answers")
        if not isinstance(raw_answers, list):
            raise ValueError("answers deve ser uma lista.")

        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in raw_answers:
            if not isinstance(item, dict):
                raise ValueError("Resposta inválida.")
            qid = str(item.get("question_id") or "").strip()
            if not qid or qid not in by_id:
                raise ValueError("Pergunta inválida na resposta.")
            if qid in seen:
                raise ValueError("Pergunta duplicada na resposta.")
            seen.add(qid)
            question = by_id[qid]
            normalized.append(self._normalize_answer(question, item))

        for question in questions:
            qid = str(question["id"])
            if question.get("is_required") and qid not in seen:
                raise ValueError(f"Resposta obrigatória ausente: {question['label']}")

        response = self.repo.create_response_with_answers(
            survey_id=str(survey["id"]),
            answers=normalized,
        )
        return {"response_id": str(response["id"]), "ok": True}

    def _require_survey(self, survey_id: str) -> dict[str, Any]:
        survey = self.repo.get_survey(survey_id)
        if not survey:
            raise LookupError("Pesquisa não encontrada.")
        return survey

    def _assert_accepting_responses(self, survey: dict[str, Any]) -> None:
        if survey["status"] != "published":
            raise ValueError("Esta pesquisa não está aberta para respostas.")
        now = datetime.now(timezone.utc)
        opens_at = survey.get("opens_at")
        closes_at = survey.get("closes_at")
        if opens_at is not None and opens_at.tzinfo is None:
            opens_at = opens_at.replace(tzinfo=timezone.utc)
        if closes_at is not None and closes_at.tzinfo is None:
            closes_at = closes_at.replace(tzinfo=timezone.utc)
        if opens_at and now < opens_at:
            raise ValueError("Esta pesquisa ainda não está aberta.")
        if closes_at and now > closes_at:
            raise ValueError("O prazo desta pesquisa encerrou.")

    def _normalize_questions(self, questions: list[Any]) -> list[dict[str, Any]]:
        if not isinstance(questions, list):
            raise ValueError("questions deve ser uma lista.")
        result: list[dict[str, Any]] = []
        for index, raw in enumerate(questions):
            if not isinstance(raw, dict):
                raise ValueError("Pergunta inválida.")
            qtype = str(raw.get("question_type") or "").strip()
            if qtype not in QUESTION_TYPES:
                raise ValueError(f"Tipo de pergunta inválido: {qtype}")
            label = str(raw.get("label") or "").strip()
            if not label:
                raise ValueError("Toda pergunta precisa de enunciado.")
            options = raw.get("options")
            if qtype in CHOICE_TYPES:
                if not isinstance(options, list) or len(options) < 2:
                    raise ValueError(
                        f"Pergunta de escolha precisa de ao menos 2 opções: {label}"
                    )
                options = [str(item).strip() for item in options if str(item).strip()]
                if len(options) < 2:
                    raise ValueError(f"Opções inválidas: {label}")
            elif qtype == "likert_5":
                options = LIKERT_LABELS
            elif qtype == "yes_no":
                options = YES_NO_OPTIONS
            else:
                options = None
            result.append(
                {
                    "position": index,
                    "question_type": qtype,
                    "label": label,
                    "help_text": str(raw.get("help_text") or "").strip() or None,
                    "is_required": bool(raw.get("is_required", True)),
                    "options": options,
                }
            )
        return result

    def _normalize_answer(
        self, question: dict[str, Any], item: dict[str, Any]
    ) -> dict[str, Any]:
        qtype = str(question["question_type"])
        qid = str(question["id"])
        if qtype in CHOICE_TYPES or qtype in {"likert_5", "yes_no"}:
            if qtype == "multi_choice":
                choices = item.get("choices") or item.get("value_json") or []
                if not isinstance(choices, list):
                    raise ValueError(f"Escolhas inválidas: {question['label']}")
                values = [str(v).strip() for v in choices if str(v).strip()]
                if question.get("is_required") and not values:
                    raise ValueError(f"Resposta obrigatória: {question['label']}")
                allowed = {str(o) for o in (question.get("options") or [])}
                if any(v not in allowed for v in values):
                    raise ValueError(f"Opção inválida: {question['label']}")
                return {"question_id": qid, "value_json": values, "value_text": None}
            value = str(
                item.get("value")
                or item.get("value_text")
                or item.get("choice")
                or ""
            ).strip()
            if question.get("is_required") and not value:
                raise ValueError(f"Resposta obrigatória: {question['label']}")
            allowed = {str(o) for o in (question.get("options") or [])}
            if value and value not in allowed:
                raise ValueError(f"Opção inválida: {question['label']}")
            return {"question_id": qid, "value_text": value or None, "value_json": None}

        text = str(item.get("value") or item.get("value_text") or "").strip()
        if question.get("is_required") and not text:
            raise ValueError(f"Resposta obrigatória: {question['label']}")
        if qtype == "text_short" and len(text) > 500:
            raise ValueError(f"Texto muito longo: {question['label']}")
        if qtype == "text_long" and len(text) > 4000:
            raise ValueError(f"Texto muito longo: {question['label']}")
        return {"question_id": qid, "value_text": text or None, "value_json": None}

    def _survey_summary(self, survey: dict[str, Any]) -> dict[str, Any]:
        token = survey.get("public_token")
        return {
            "id": str(survey["id"]),
            "unit_code": survey["unit_code"],
            "title": survey["title"],
            "description": survey.get("description"),
            "status": survey["status"],
            "public_token": token,
            "public_url": build_sipat_public_url(str(token)) if token else None,
            "qr_filename": survey.get("qr_filename"),
            "opens_at": survey.get("opens_at"),
            "closes_at": survey.get("closes_at"),
            "response_count": int(survey.get("response_count") or 0),
            "created_at": survey.get("created_at"),
            "updated_at": survey.get("updated_at"),
        }

    def _survey_detail(
        self, survey: dict[str, Any], questions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return {
            "survey": self._survey_summary(survey),
            "questions": [self._admin_question(q) for q in questions],
        }

    def _admin_question(self, question: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(question["id"]),
            "position": question.get("position"),
            "question_type": question["question_type"],
            "label": question["label"],
            "help_text": question.get("help_text"),
            "is_required": bool(question.get("is_required")),
            "options": question.get("options"),
        }

    def _public_question(self, question: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(question["id"]),
            "position": question.get("position"),
            "type": question["question_type"],
            "label": question["label"],
            "helpText": question.get("help_text"),
            "required": bool(question.get("is_required")),
            "options": question.get("options"),
        }
