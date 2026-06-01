#!/usr/bin/env python3
"""Gera plugins/minha-delpi-chat/src/ui/chatFeedbackReasons.ts a partir do playbook."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK_PATH = (
    REPO_ROOT
    / "minha-delpi-ai-api/app/content/pt-BR/assistant/personality_playbook.json"
)
OUTPUT_PATH = REPO_ROOT / "plugins/minha-delpi-chat/src/ui/chatFeedbackReasons.ts"


def _load_playbook() -> dict:
    return json.loads(PLAYBOOK_PATH.read_text(encoding="utf-8"))


def _render_ts(playbook: dict) -> str:
    reasons = playbook.get("feedbackReasons") or []
    primary_ids = playbook.get("feedbackPrimaryReasonIds") or []

    lines = [
        "// AUTO-GENERATED — não editar manualmente.",
        "// Fonte: minha-delpi-ai-api/app/content/pt-BR/assistant/personality_playbook.json",
        "// Comando: python minha-delpi-ai-api/scripts/generate_chat_feedback_reasons_ts.py --write",
        "",
        "export type ChatFeedbackReason = {",
        "  id: string;",
        "  label: string;",
        "};",
        "",
        "export const CHAT_FEEDBACK_REASONS: ChatFeedbackReason[] = [",
    ]

    for item in reasons:
        if not isinstance(item, dict):
            continue

        reason_id = str(item.get("id") or "").strip()
        label = str(item.get("label") or "").strip()

        if not reason_id or not label:
            continue

        safe_label = label.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'  {{ id: "{reason_id}", label: "{safe_label}" }},')

    lines.extend(
        [
            "];",
            "",
            "export const CHAT_FEEDBACK_PRIMARY_REASON_IDS: string[] = [",
        ]
    )

    for reason_id in primary_ids:
        token = str(reason_id).strip()

        if token:
            lines.append(f'  "{token}",')

    lines.extend(["];", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Grava o arquivo TS.")
    parser.add_argument("--check", action="store_true", help="Falha se houver drift.")
    args = parser.parse_args()

    if not args.write and not args.check:
        parser.print_help()
        return 2

    if not PLAYBOOK_PATH.is_file():
        print(f"Playbook não encontrado: {PLAYBOOK_PATH}", file=sys.stderr)
        return 1

    generated = _render_ts(_load_playbook())

    if args.check:
        if not OUTPUT_PATH.is_file():
            print(f"Arquivo ausente: {OUTPUT_PATH}", file=sys.stderr)
            return 1

        on_disk = OUTPUT_PATH.read_text(encoding="utf-8")

        if on_disk != generated:
            print("Drift detectado em chatFeedbackReasons.ts — rode --write.", file=sys.stderr)
            return 1

        print("OK chatFeedbackReasons.ts sincronizado com o playbook.")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(generated, encoding="utf-8")
    print(f"Gerado: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
