#!/usr/bin/env python3
"""Validate the canonical documentation layout for Minha DELPI."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATHS = (
    ROOT / "documentos",
    ROOT / "docs" / "12-roadmap-e-volucao",
)

REQUIRED_PATHS = (
    ROOT / "docs",
    ROOT / "docs" / "11-padroes-de-desenvolvimento" / "instrucoes-oficiais-gpt-arquiteto-delpi-central.md",
    ROOT / "docs" / "12-roadmap-e-evolucao",
    ROOT / "docs" / "12-roadmap-e-evolucao" / "customer-experience",
    ROOT / "docs" / "12-roadmap-e-evolucao" / "kaizometro",
    ROOT / "docs" / "14-documentacao-geral" / "README.md",
)


def main() -> int:
    errors: list[str] = []

    for path in FORBIDDEN_PATHS:
        if path.exists():
            errors.append(f"caminho proibido reapareceu: {path.relative_to(ROOT)}")

    for path in REQUIRED_PATHS:
        if not path.exists():
            errors.append(f"caminho canonico ausente: {path.relative_to(ROOT)}")

    docs_readme = ROOT / "docs" / "README.md"
    if docs_readme.exists():
        text = docs_readme.read_text(encoding="utf-8")
        if "12-roadmap-e-evolucao" not in text:
            errors.append("docs/README.md nao aponta para o roadmap canonico")
        if "11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md" not in text:
            errors.append("docs/README.md nao aponta para as instrucoes oficiais")

    if errors:
        print("Documentation structure audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Documentation structure audit: OK")
    print("- raiz documental unica: docs/")
    print("- roadmap/evolucao canonico: docs/12-roadmap-e-evolucao/")
    print("- instrucoes oficiais: docs/11-padroes-de-desenvolvimento/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
