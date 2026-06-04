#!/usr/bin/env python3
"""Smoke — apresentação humanizada do product analyser (roteiro + inspeção em tabelas).

Sem HTTP; valida ExternalActionResultPresenter com payload representativo.

Uso:
  PYTHONPATH=/app python scripts/smoke_product_analyser_presentation.py
"""

from __future__ import annotations

import sys

from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def main() -> int:
    presenter = ExternalActionResultPresenter()
    payload = _analyser_payload_with_guide_and_inspection()
    path = "/products/90260140/analyser"

    humanized = presenter.present(payload, path=path)
    body = "\n".join(humanized.get("linhas") or [])
    text = presenter.build_text_presentation(payload, path=path)
    markdown = (text or {}).get("markdown") or ""

    failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal failed

        if ok:
            print(f"OK {name}")
        else:
            print(f"FAIL {name}", file=sys.stderr)
            failed += 1

    check("sem dump Qp6/Qp7 no corpo", "Qp6=[" not in body and "Product=" not in body)
    guide_table = presenter.build_presentation(payload, path=path)
    check(
        "roteiro em tablePresentation",
        isinstance(guide_table, dict)
        and guide_table.get("type") == "table"
        and "Roteiro" in str(guide_table.get("title") or ""),
    )
    check(
        "roteiro fora do markdown narrativo",
        "| Produto | BOM | Op. |" not in body and "| Produto | BOM | Op. |" not in markdown,
    )
    inspection_table = presenter._build_product_analyser_inspection_table(
        presenter._normalize_analyser_root(payload),
    )
    check(
        "inspeção em tablePresentation",
        isinstance(inspection_table, dict) and inspection_table.get("type") == "table",
    )
    check(
        "inspeção fora do markdown narrativo",
        "Ensaios dimensionais" not in body and "Ensaios dimensionais" not in markdown,
    )
    check("estrutura só no painel visual", "**Estrutura do produto" not in body)
    check("árvore disponível", (humanized.get("apresentacao") or {}).get("type") == "tree")
    check("textPresentation sem dump", "Qp6=[" not in markdown)
    check("perfil em linhas narrativas", "90260140" in body and "CHICOTE" in body)

    if failed:
        print(f"\n{failed} verificação(ões) falharam", file=sys.stderr)
        return 1

    print("Smoke product analyser presentation: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
