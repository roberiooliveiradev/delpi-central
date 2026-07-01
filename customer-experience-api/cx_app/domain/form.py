from __future__ import annotations

from dataclasses import dataclass, field


class QuestionType:
    RATING = "rating"
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    YES_NO = "yes_no"


ALL_QUESTION_TYPES: frozenset[str] = frozenset(
    {
        QuestionType.RATING,
        QuestionType.SHORT_TEXT,
        QuestionType.LONG_TEXT,
        QuestionType.SINGLE_CHOICE,
        QuestionType.MULTI_CHOICE,
        QuestionType.YES_NO,
    }
)

# Tipos que exigem lista de opções configurada no editor.
CHOICE_QUESTION_TYPES: frozenset[str] = frozenset(
    {QuestionType.SINGLE_CHOICE, QuestionType.MULTI_CHOICE}
)


@dataclass(frozen=True)
class QuestionInput:
    label: str
    question_type: str
    id: str | None = None
    help_text: str | None = None
    is_required: bool = False
    options: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FormInput:
    title: str
    description: str | None = None


@dataclass(frozen=True)
class FormUpdate:
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class AnswerInput:
    question_id: str
    text: str | None = None
    rating: int | None = None
    choices: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResponseInput:
    respondent_name: str
    respondent_company: str | None
    answers: list[AnswerInput] = field(default_factory=list)
