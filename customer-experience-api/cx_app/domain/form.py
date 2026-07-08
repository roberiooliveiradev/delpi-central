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


class BackgroundFit:
    """Como a imagem de fundo do formulário preenche a viewport."""

    FIXED = "fixed"  # tamanho natural (px)
    SCALE = "scale"  # escalável — preenche a tela (cover)
    TILE = "tile"  # várias imagens repetidas


ALL_BACKGROUND_FITS: frozenset[str] = frozenset(
    {BackgroundFit.FIXED, BackgroundFit.SCALE, BackgroundFit.TILE}
)

DEFAULT_BACKGROUND_FIT = BackgroundFit.SCALE


@dataclass(frozen=True)
class FormInput:
    title: str
    description: str | None = None
    one_question_per_page: bool = False
    background_fit: str = DEFAULT_BACKGROUND_FIT


@dataclass(frozen=True)
class FormUpdate:
    title: str | None = None
    description: str | None = None
    one_question_per_page: bool | None = None
    background_fit: str | None = None


@dataclass(frozen=True)
class PageInput:
    title: str | None = None
    id: str | None = None
    background_image_filename: str | None = None
    point_image_filename: str | None = None
    point_image_fit: str | None = None
    point_icon: str | None = None


@dataclass(frozen=True)
class QuestionInput:
    label: str
    question_type: str
    id: str | None = None
    help_text: str | None = None
    is_required: bool = False
    options: list[str] = field(default_factory=list)
    page_id: str | None = None
    page_index: int | None = None
    point_image_filename: str | None = None
    point_image_fit: str | None = None
    point_icon: str | None = None


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
