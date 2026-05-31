#!/usr/bin/env python3
"""Gera PDF anonimizado de teste a partir de sample_carimbo.txt (Onda 12.2.4)."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

_ROOT = Path(__file__).resolve().parents[1]
_TEXT_FIXTURE = _ROOT / "tests" / "fixtures" / "drawings" / "sample_carimbo.txt"
_PDF_FIXTURE = _ROOT / "tests" / "fixtures" / "drawings" / "sample_carimbo_minimal.pdf"


def build_pdf(*, text_path: Path = _TEXT_FIXTURE, output_path: Path = _PDF_FIXTURE) -> Path:
    lines = text_path.read_text(encoding="utf-8").splitlines()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    pdf.cell(0, 8, "DESENHO TECNICO DELPI (fixture anonimizada)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    for line in lines:
        pdf.cell(0, 7, line[:120], new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))

    return output_path


if __name__ == "__main__":
    path = build_pdf()
    print(f"Fixture PDF gerada: {path}")
