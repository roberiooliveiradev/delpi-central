#!/usr/bin/env python3
"""Render headless protocol and hook configs for Cursor / Devin (agent-kit 0.3+).

The protocol lives in verifier/protocol.md + verifier/report-format.md.
Legacy Task-agent files are no longer generated.

Usage (inspection only — install.py calls these functions directly):
    python agent-kit/scripts/build.py --out /tmp/dak-dist
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

KIT_ROOT = Path(__file__).resolve().parents[1]
# Kept only so install migration can recognize kit-authored agent files from 0.1/0.2.
AGENT_FILE_MARKER = "delpi-verifier — protocolo de verificação independente"
HOOK_SCRIPT_NAME = "verifier_hooks.py"
HOOK_HOSTS = ("cursor", "devin")


def kit_version() -> str:
    return (KIT_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def quoted(path: object) -> str:
    return f'"{path}"'


def hook_command(python: str, kit_home: Path, *args: str) -> str:
    return " ".join([quoted(python), quoted(kit_home / HOOK_SCRIPT_NAME), *args])


def protocol_body(python: str, kit_home: Path, platform: str) -> str:
    body = (
        (KIT_ROOT / "verifier" / "protocol.md").read_text(encoding="utf-8").rstrip()
        + "\n\n---\n\n"
        + (KIT_ROOT / "verifier" / "report-format.md").read_text(encoding="utf-8").rstrip()
        + "\n"
    )
    return (
        body.replace("{{KIT_VERSION}}", kit_version())
        .replace("{{PLATFORM}}", platform)
        .replace("{{RECORD_CMD}}", hook_command(python, kit_home, "record"))
        .replace("{{GUARD_ALWAYS_CMD}}", "")
        .replace("{{MODEL}}", "")
    )


def render_headless(python: str, kit_home: Path) -> str:
    """Protocol for verify.py — no YAML frontmatter."""
    text = protocol_body(python, kit_home, "headless")
    leftover = [tok for tok in ("{{MODEL}}", "{{KIT_VERSION}}", "{{PLATFORM}}", "{{RECORD_CMD}}", "{{GUARD_ALWAYS_CMD}}") if tok in text]
    if leftover:
        raise RuntimeError(f"placeholders não substituídos: {leftover}")
    return text


def cursor_hooks(python: str, kit_home: Path) -> Dict[str, List[dict]]:
    """Entries for ~/.cursor/hooks.json (merged under the "hooks" key)."""
    cmd = lambda *a: hook_command(python, kit_home, *a)  # noqa: E731
    return {
        "sessionStart": [{"command": cmd("session-start", "--host", "cursor")}],
        "afterFileEdit": [{"command": cmd("track-edit", "--host", "cursor")}],
        "beforeShellExecution": [{"command": cmd("guard", "--host", "cursor")}],
        "preToolUse": [{"command": cmd("guard", "--host", "cursor")}],
        "stop": [{"command": cmd("stop-gate", "--host", "cursor"), "loop_limit": 2}],
    }


def devin_hooks(python: str, kit_home: Path) -> Dict[str, List[dict]]:
    """Entries for the "hooks" key of ~/.config/devin/config.json (and Windows %APPDATA%)."""

    def group(matcher: str, *args: str) -> dict:
        return {"matcher": matcher, "hooks": [{"type": "command", "command": hook_command(python, kit_home, *args)}]}

    return {
        "SessionStart": [group("", "session-start", "--host", "devin")],
        "PreToolUse": [
            group("^(exec|write|edit|apply_patch|notebook_edit)$", "guard", "--host", "devin"),
        ],
        "PostToolUse": [
            group("^(write|edit|apply_patch|notebook_edit)$", "track-edit", "--host", "devin"),
        ],
        "Stop": [group("", "stop-gate", "--host", "devin")],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--kit-home", type=Path, default=Path.home() / ".delpi-agent-kit")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "protocol.headless.md").write_text(render_headless(args.python, args.kit_home), encoding="utf-8")
    (args.out / "cursor" / "hooks.json").parent.mkdir(parents=True, exist_ok=True)
    (args.out / "cursor" / "hooks.json").write_text(
        json.dumps({"version": 1, "hooks": cursor_hooks(args.python, args.kit_home)}, indent=2), encoding="utf-8"
    )
    (args.out / "devin" / "hooks.json").parent.mkdir(parents=True, exist_ok=True)
    (args.out / "devin" / "hooks.json").write_text(
        json.dumps({"hooks": devin_hooks(args.python, args.kit_home)}, indent=2), encoding="utf-8"
    )
    print(f"gerado em {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
