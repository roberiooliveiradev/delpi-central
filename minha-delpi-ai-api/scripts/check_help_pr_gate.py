#!/usr/bin/env python3
"""CI/local — exige atualização de ajuda quando actions/skills mudam (autoajuda Fase 3)."""

from __future__ import annotations

import os
import subprocess
import sys

_TRIGGER_PREFIXES = (
    "minha-delpi-ai-api/app/infrastructure/persistence/postgres_external_action",
    "minha-delpi-ai-api/app/application/services/external_actions/",
    "minha-delpi-ai-api/app/content/pt-BR/skills/",
    "minha-delpi-ai-api/app/interfaces/http/routes/chat_routes.py",
    "plugins/minha-delpi-chat/src/data/api/chatApi.ts",
)

_HELP_MARKERS = (
    "features_catalog.json",
    "assistant_release_notes.json",
    "capabilities.json",
    "personality_playbook.json",
    "chat_help",
    "assistant_capabilities",
    "playbook_autoajuda",
    "generate_assistant_capabilities_catalog",
    "check_assistant_capabilities_catalog",
    "check_help_pr_gate",
)


def _git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


def _changed_files(base_ref: str) -> list[str]:
    merge_base = _git_output("merge-base", "HEAD", base_ref)

    if merge_base:
        diff_range = f"{merge_base}...HEAD"
    else:
        diff_range = f"{base_ref}...HEAD"

    raw = _git_output("diff", "--name-only", diff_range)

    if not raw:
        raw = _git_output("diff", "--name-only", "HEAD")

    return [line.strip() for line in raw.splitlines() if line.strip()]


def main() -> int:
    if os.environ.get("SKIP_HELP_PR_GATE", "").lower() in {"1", "true", "yes"}:
        print("SKIP help PR gate (SKIP_HELP_PR_GATE).")
        return 0

    base_ref = os.environ.get("PR_BASE_REF", os.environ.get("GITHUB_BASE_REF", "main")).strip()

    if not _git_output("rev-parse", "--is-inside-work-tree"):
        print("SKIP help PR gate: não é repositório git.")
        return 0

    changed = _changed_files(base_ref)

    if not changed:
        print("OK help PR gate: sem arquivos alterados.")
        return 0

    triggered = [
        path
        for path in changed
        if any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in _TRIGGER_PREFIXES)
    ]

    if not triggered:
        print("OK help PR gate: alterações fora do escopo de actions/skills.")
        return 0

    help_touched = any(
        any(marker in path for marker in _HELP_MARKERS) for path in changed
    )

    if not help_touched:
        print(
            "FAIL help PR gate: mudanças em actions/skills exigem atualizar ajuda/catálogo.",
            file=sys.stderr,
        )

        for path in triggered[:12]:
            print(f"  - {path}", file=sys.stderr)

        print(
            "Atualize features_catalog.json, capabilities.json (featureAnswers), "
            "release notes ou rode generate_assistant_capabilities_catalog.py --write",
            file=sys.stderr,
        )

        return 1

    from scripts.check_assistant_capabilities_catalog import main as catalog_check

    return catalog_check()


if __name__ == "__main__":
    raise SystemExit(main())
