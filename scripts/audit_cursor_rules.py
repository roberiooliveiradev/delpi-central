#!/usr/bin/env python3
"""Audita governança, escopo, hierarquia, ownership e referências das regras Cursor."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = REPO_ROOT / ".cursor" / "rules"
INDEX_PATH = RULES_DIR / "development-standards-index.mdc"
RESPONSIBILITY_MAP_PATH = RULES_DIR / "responsibility-map.json"
TRANSVERSAL_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "11-padroes-de-desenvolvimento"
    / "responsabilidades-transversais.md"
)
INVENTORY_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "11-padroes-de-desenvolvimento"
    / "inventario-regras-cursor.md"
)
TRANSVERSAL_DOCS_INDEX_PATH = (
    REPO_ROOT / "docs" / "11-padroes-de-desenvolvimento" / "README.md"
)

GLOBAL_ALLOWLIST = {
    "development-standards-index.mdc",
    "evidence-driven-execution.mdc",
    "centralized-rules-first.mdc",
    "clean-code-architecture-guardrails.mdc",
    "english-code-identifiers.mdc",
}
GLOBAL_BUDGET = len(GLOBAL_ALLOWLIST)

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
    "ai-external-tools-security.mdc",
    "ai-intelligence-evaluation.mdc",
    "ai-context-and-tool-budget.mdc",
    "http-integration-resilience.mdc",
    "observability-standards.mdc",
    "contract-evolution-backward-compatibility.mdc",
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


def audit_responsibility_map(rule_names: set[str], errors: list[str]) -> dict[str, list[str]]:
    """Garante ownership primário único para toda regra especializada."""
    if not RESPONSIBILITY_MAP_PATH.exists():
        errors.append(".cursor/rules/responsibility-map.json ausente")
        return {}

    try:
        payload = json.loads(RESPONSIBILITY_MAP_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"responsibility-map.json inválido: {exc}")
        return {}

    if payload.get("version") != 1:
        errors.append("responsibility-map.json: version deve ser 1")

    owners = payload.get("owners")
    if not isinstance(owners, dict):
        errors.append("responsibility-map.json: owners deve ser objeto")
        return {}

    owner_names = set(owners)
    missing_owners = REQUIRED_TRANSVERSAL_RULES - owner_names
    extra_owners = owner_names - REQUIRED_TRANSVERSAL_RULES
    if missing_owners:
        errors.append(
            "responsibility-map sem owners canônicos: "
            + ", ".join(sorted(missing_owners))
        )
    if extra_owners:
        errors.append(
            "responsibility-map contém owner não canônico: "
            + ", ".join(sorted(extra_owners))
        )

    assignments: Counter[str] = Counter()
    normalized: dict[str, list[str]] = {}
    for owner, children in owners.items():
        if not isinstance(children, list) or any(
            not isinstance(child, str) for child in children
        ):
            errors.append(f"responsibility-map: {owner} deve conter lista de nomes .mdc")
            continue
        if len(children) != len(set(children)):
            errors.append(f"responsibility-map: {owner} contém regra duplicada na própria lista")
        normalized[owner] = children
        assignments.update(children)

    expected_specialized = rule_names - GLOBAL_ALLOWLIST - REQUIRED_TRANSVERSAL_RULES
    mapped = set(assignments)

    orphan_rules = expected_specialized - mapped
    if orphan_rules:
        errors.append(
            "regras especializadas sem owner transversal: "
            + ", ".join(sorted(orphan_rules))
        )

    unknown_rules = mapped - expected_specialized
    if unknown_rules:
        errors.append(
            "responsibility-map referencia regra inexistente/global/owner: "
            + ", ".join(sorted(unknown_rules))
        )

    duplicate_owners = sorted(name for name, count in assignments.items() if count > 1)
    if duplicate_owners:
        errors.append(
            "regras com mais de um owner primário: " + ", ".join(duplicate_owners)
        )

    return normalized


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

    unexpected_platform_rules = {
        name for name in rule_names if name.startswith("platform-")
    } - REQUIRED_TRANSVERSAL_RULES
    if unexpected_platform_rules:
        errors.append(
            "regras platform-* fora das oito responsabilidades canônicas: "
            + ", ".join(sorted(unexpected_platform_rules))
        )

    missing_specialized = REQUIRED_SPECIALIZED_RULES - rule_names
    if missing_specialized:
        errors.append(
            "guardrails especializados obrigatórios ausentes: "
            + ", ".join(sorted(missing_specialized))
        )

    ownership = audit_responsibility_map(rule_names, errors)

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

    if "responsibility-map.json" not in index_text:
        errors.append(
            "development-standards-index.mdc não referencia responsibility-map.json"
        )

    if not TRANSVERSAL_DOC_PATH.exists():
        errors.append(
            "documentação canônica das responsabilidades ausente: "
            + str(TRANSVERSAL_DOC_PATH.relative_to(REPO_ROOT))
        )
        transversal_doc_text = ""
    else:
        transversal_doc_text = TRANSVERSAL_DOC_PATH.read_text(encoding="utf-8")

    for required_name in sorted(REQUIRED_TRANSVERSAL_RULES):
        if required_name not in transversal_doc_text:
            errors.append(
                f"{required_name}: responsabilidade transversal não documentada em responsabilidades-transversais.md"
            )

    if not INVENTORY_DOC_PATH.exists():
        errors.append("docs/11-padroes-de-desenvolvimento/inventario-regras-cursor.md ausente")
        inventory_text = ""
    else:
        inventory_text = INVENTORY_DOC_PATH.read_text(encoding="utf-8")

    for owner, children in ownership.items():
        if owner not in inventory_text:
            errors.append(f"{owner}: owner não documentado no inventário Cursor")
        for child in children:
            if child not in inventory_text:
                errors.append(f"{child}: regra não documentada no inventário Cursor")

    if not TRANSVERSAL_DOCS_INDEX_PATH.exists():
        errors.append("docs/11-padroes-de-desenvolvimento/README.md ausente")
    else:
        docs_index_text = TRANSVERSAL_DOCS_INDEX_PATH.read_text(encoding="utf-8")
        for required_doc in (
            "responsabilidades-transversais.md",
            "inventario-regras-cursor.md",
        ):
            if required_doc not in docs_index_text:
                errors.append(
                    f"docs/11-padroes-de-desenvolvimento/README.md não indexa {required_doc}"
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
    print(f"- regras .mdc: {len(rule_paths)}")
    print(f"- globais: {len(global_rules)}/{GLOBAL_BUDGET}")
    print("- globais canônicas: " + ", ".join(sorted(global_rules)))
    print(
        "- responsabilidades transversais: "
        + ", ".join(sorted(REQUIRED_TRANSVERSAL_RULES & rule_names))
    )
    print(
        "- regras especializadas classificadas: "
        + str(sum(len(children) for children in ownership.values()))
    )
    print(
        "- guardrails especializados obrigatórios: "
        + ", ".join(sorted(REQUIRED_SPECIALIZED_RULES & rule_names))
    )
    print(
        "- documentação transversal: "
        + ("OK" if TRANSVERSAL_DOC_PATH.exists() else "AUSENTE")
    )
    print(
        "- inventário Cursor: "
        + ("OK" if INVENTORY_DOC_PATH.exists() else "AUSENTE")
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
