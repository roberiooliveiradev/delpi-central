#!/usr/bin/env python3
"""Audita governança, escopo, hierarquia e referências das regras Cursor."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = REPO_ROOT / ".cursor" / "rules"
INDEX_PATH = RULES_DIR / "development-standards-index.mdc"

GLOBAL_ALLOWLIST = {
    "development-standards-index.mdc",
    "evidence-driven-execution.mdc",
    "centralized-rules-first.mdc",
    "clean-code-architecture-guardrails.mdc",
    "english-code-identifiers.mdc",
}
GLOBAL_BUDGET = len(GLOBAL_ALLOWLIST)

# Donos transversais da engenharia. Permanecem não globais para preservar contexto.
REQUIRED_TRANSVERSAL_RULES = {
    "platform-architecture-boundaries.mdc",
    "platform-security-identity-authorization.mdc",
    "platform-api-contracts-integration.mdc",
    "platform-data-persistence.mdc",
    "platform-frontend-mfe-experience.mdc",
    "platform-quality-testing.mdc",
    "platform-delivery-runtime-operations.mdc",
    "platform-reliability-observability.mdc",
}

REQUIRED_SPECIALIZED_RULES = {
    # Guardrails especializados críticos já existentes.
    "ai-external-tools-security.mdc",
    "ai-intelligence-evaluation.mdc",
    "ai-context-and-tool-budget.mdc",
    "http-integration-resilience.mdc",
    "observability-standards.mdc",
    "contract-evolution-backward-compatibility.mdc",
    # Enforcement executável.
    "architecture-ci-enforcement.mdc",
}

MAX_RULE_BYTES = 20_000
REFERENCE_RE = re.compile(r"(?:`|\b)([A-Za-z0-9_.-]+\.mdc)(?:`|\b)")
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str, list[str]]:
    """Parseia o subconjunto YAML usado nas regras, incluindo listas multilinha."""
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, text, ["frontmatter ausente"]

    try:
        _, raw_frontmatter, body = text.split("---", 2)
    except ValueError:
        return {}, text, ["frontmatter sem fechamento ---"]

    data: dict[str, str] = {}
    current_key: str | None = None
    list_values: dict[str, list[str]] = {}

    for raw_line in raw_frontmatter.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        if raw_line[:1].isspace():
            stripped = raw_line.strip()
            if stripped.startswith("-") and current_key:
                value = stripped[1:].strip().strip('"').strip("'")
                list_values.setdefault(current_key, []).append(value)
                continue
            errors.append(f"linha YAML indentada não suportada: {raw_line!r}")
            continue

        match = TOP_LEVEL_KEY_RE.match(raw_line)
        if not match:
            errors.append(f"linha de frontmatter inválida: {raw_line!r}")
            current_key = None
            continue

        key = match.group(1)
        value = (match.group(2) or "").strip().strip('"').strip("'")
        if key in data or key in list_values:
            errors.append(f"chave duplicada no frontmatter: {key}")
        data[key] = value
        current_key = key

    for key, values in list_values.items():
        if data.get(key):
            errors.append(f"{key}: não misturar valor inline e lista multilinha")
        data[key] = ",".join(values)

    return data, body, errors


def main() -> int:
    if not RULES_DIR.is_dir():
        print(f"ERRO: diretório não encontrado: {RULES_DIR}", file=sys.stderr)
        return 2

    rule_paths = sorted(RULES_DIR.glob("*.mdc"))
    rule_names = {path.name for path in rule_paths}
    errors: list[str] = []
    warnings: list[str] = []
    descriptions: list[tuple[str, str]] = []
    global_rules: set[str] = set()

    missing_transversal = REQUIRED_TRANSVERSAL_RULES - rule_names
    if missing_transversal:
        errors.append(
            "responsabilidades transversais canônicas ausentes: "
            + ", ".join(sorted(missing_transversal))
        )

    missing_specialized = REQUIRED_SPECIALIZED_RULES - rule_names
    if missing_specialized:
        errors.append(
            "guardrails especializados obrigatórios ausentes: "
            + ", ".join(sorted(missing_specialized))
        )

    index_text = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
    for required_name in sorted(REQUIRED_TRANSVERSAL_RULES):
        if required_name not in index_text:
            errors.append(
                f"{required_name}: responsabilidade transversal não referenciada em development-standards-index.mdc"
            )

    for required_name in sorted(REQUIRED_SPECIALIZED_RULES):
        if required_name not in index_text:
            errors.append(
                f"{required_name}: guardrail obrigatório não referenciado em development-standards-index.mdc"
            )

    for path in rule_paths:
        frontmatter, body, parse_errors = parse_frontmatter(path)
        for error in parse_errors:
            errors.append(f"{path.name}: {error}")

        description = frontmatter.get("description", "").strip()
        globs = frontmatter.get("globs", "").strip()
        always_apply_raw = frontmatter.get("alwaysApply")

        if description:
            descriptions.append((path.name, description.casefold()))
            if description.casefold().startswith("(legado)"):
                errors.append(
                    f"{path.name}: regra marcada como legado deve ser removida ou absorvida pela fonte canônica"
                )
        elif not globs:
            warnings.append(
                f"{path.name}: regra não global sem description/globs pode depender de invocação manual"
            )

        if always_apply_raw is None:
            errors.append(f"{path.name}: alwaysApply ausente")
            always_apply = False
        elif always_apply_raw not in {"true", "false"}:
            errors.append(
                f"{path.name}: alwaysApply deve ser true|false, recebido {always_apply_raw!r}"
            )
            always_apply = False
        else:
            always_apply = always_apply_raw == "true"

        if always_apply:
            global_rules.add(path.name)
            if globs:
                errors.append(
                    f"{path.name}: alwaysApply=true + globs é proibido; o glob é ignorado no modo global"
                )
            if path.name not in GLOBAL_ALLOWLIST:
                errors.append(f"{path.name}: regra global fora da allowlist canônica")

        if path.name in (REQUIRED_TRANSVERSAL_RULES | REQUIRED_SPECIALIZED_RULES) and always_apply:
            errors.append(
                f"{path.name}: responsabilidade/guardrail especializado deve permanecer alwaysApply=false"
            )

        if path.name in REQUIRED_TRANSVERSAL_RULES:
            if not description.startswith("Responsabilidade transversal canônica"):
                errors.append(
                    f"{path.name}: description deve identificar explicitamente a responsabilidade transversal canônica"
                )
            if globs:
                errors.append(
                    f"{path.name}: owner transversal não deve usar globs; seleção ocorre por responsabilidade/relevância"
                )

        size = path.stat().st_size
        if size > MAX_RULE_BYTES and "governanceSizeJustification" not in frontmatter:
            errors.append(
                f"{path.name}: {size} bytes excede {MAX_RULE_BYTES}; reduzir ou declarar governanceSizeJustification"
            )

        for referenced_name in sorted(set(REFERENCE_RE.findall(body))):
            if referenced_name not in rule_names:
                errors.append(
                    f"{path.name}: referência a regra inexistente: {referenced_name}"
                )

    if len(global_rules) > GLOBAL_BUDGET:
        errors.append(
            f"orçamento global excedido: {len(global_rules)} regras globais; máximo {GLOBAL_BUDGET}"
        )

    missing_global = GLOBAL_ALLOWLIST - global_rules
    if missing_global:
        errors.append(
            "constituição global incompleta: " + ", ".join(sorted(missing_global))
        )

    description_counts = Counter(description for _, description in descriptions)
    duplicated_descriptions = {
        description for description, count in description_counts.items() if count > 1
    }
    for description in sorted(duplicated_descriptions):
        owners = sorted(name for name, value in descriptions if value == description)
        errors.append("description duplicada em regras: " + ", ".join(owners))

    print("Cursor rules audit")
    print(f"- regras: {len(rule_paths)}")
    print(f"- globais: {len(global_rules)}/{GLOBAL_BUDGET}")
    print("- globais canônicas: " + ", ".join(sorted(global_rules)))
    print(
        "- responsabilidades transversais: "
        + ", ".join(sorted(REQUIRED_TRANSVERSAL_RULES & rule_names))
    )
    print(
        "- guardrails especializados obrigatórios: "
        + ", ".join(sorted(REQUIRED_SPECIALIZED_RULES & rule_names))
    )

    for warning in warnings:
        print(f"WARN: {warning}")

    if errors:
        print(f"\nFALHOU: {len(errors)} problema(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("OK: governança das regras Cursor válida")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
