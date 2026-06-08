from pathlib import Path

from app.infrastructure.content.hardcoded_pt_string_scanner import (
    diff_against_baseline,
    load_baseline,
    scan_protected_paths,
)

BASELINE_PATH = Path("tests/fixtures/hardcoded_pt_strings_baseline.json")


def test_no_new_hardcoded_pt_strings_in_protected_paths():
    findings = scan_protected_paths()
    baseline = load_baseline(BASELINE_PATH)
    new_items, removed = diff_against_baseline(findings, baseline)

    messages: list[str] = []

    if new_items:
        messages.append("Novas strings PT hardcoded (mover para app/content/pt-BR/assistant/*.json):")
        for item in new_items[:20]:
            messages.append(f"  - {item.file}:{item.line} → {item.text[:100]}")

        if len(new_items) > 20:
            messages.append(f"  … e mais {len(new_items) - 20} ocorrência(s).")

    if removed:
        messages.append(
            "Baseline desatualizada — remova entradas resolvidas de "
            f"{BASELINE_PATH} ({len(removed)} fingerprint(s))."
        )

    assert not messages, "\n".join(messages)
