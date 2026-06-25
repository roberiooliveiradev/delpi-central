#!/usr/bin/env python3
"""Gera template Excel mínimo para CI/export 8D (Onda 1.2)."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tests" / "fixtures" / "quality" / "rnc_8d_template_minimal.xlsx"


def main() -> int:
    TARGET.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "RNC 8D"
    ws["I4"] = ""
    ws["C8"] = ""
    ws["C9"] = ""

    annex = wb.create_sheet("Anexos(Evidencias)")
    annex["A1"] = "Evidências"

    wb.save(TARGET)
    print(f"[OK] Template mínimo gerado: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
