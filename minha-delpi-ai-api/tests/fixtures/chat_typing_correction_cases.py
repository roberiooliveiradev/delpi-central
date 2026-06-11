"""Casos de regressão T1–T7 — Playbook 14 corretor de digitação."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TypingCorrectionCase:
    id: str
    text: str
    expect_suggestions: bool
    expect_in_corrected: tuple[str, ...] = ()
    expect_not_in_corrected: tuple[str, ...] = ()
    expect_unchanged: bool = False
    max_changes: int | None = None


TYPING_CORRECTION_CASES: tuple[TypingCorrectionCase, ...] = (
    TypingCorrectionCase(
        id="T1",
        text="estouque do produto 90262404",
        expect_suggestions=True,
        expect_in_corrected=("estoque", "90262404"),
    ),
    TypingCorrectionCase(
        id="T2",
        text="qual o status fabril filial 01",
        expect_suggestions=False,
        expect_in_corrected=("01",),
    ),
    TypingCorrectionCase(
        id="T3",
        text="corrija: estouque baixo",
        expect_suggestions=False,
        expect_unchanged=True,
    ),
    TypingCorrectionCase(
        id="T4",
        text="@Agente estouque",
        expect_suggestions=True,
        expect_in_corrected=("@Agente", "estoque"),
    ),
    TypingCorrectionCase(
        id="T7",
        text="SELECT * FROM SB1",
        expect_suggestions=False,
    ),
    TypingCorrectionCase(
        id="T8",
        text="status fabrril filial 01",
        expect_suggestions=True,
        expect_in_corrected=("fabril", "01"),
    ),
    TypingCorrectionCase(
        id="T9",
        text="como para que sim",
        expect_suggestions=False,
    ),
    TypingCorrectionCase(
        id="T10",
        text="producai na filial 01",
        expect_suggestions=True,
        expect_in_corrected=("producao", "01"),
    ),
)
