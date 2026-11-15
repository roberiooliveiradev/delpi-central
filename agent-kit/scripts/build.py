#!/usr/bin/env python3
"""Render the delpi-verifier agent files and hook configs for each platform.

The protocol lives in one place (verifier/protocol.md + verifier/report-format.md).
This module wraps it with each platform's frontmatter and fills the absolute paths
of the installed hook script, so every generated agent file is self-contained.

Usage (inspection only — install.py calls these functions directly):
    python agent-kit/scripts/build.py --out /tmp/dak-dist --cursor-model <id> --devin-model <id>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

KIT_ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("cursor", "devin", "claude")
AGENT_FILE_MARKER = "delpi-verifier — protocolo de verificação independente"
HOOK_SCRIPT_NAME = "verifier_hooks.py"


def kit_version() -> str:
    return (KIT_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def quoted(path: object) -> str:
    return f'"{path}"'


def hook_command(python: str, kit_home: Path, *args: str) -> str:
    return " ".join([quoted(python), quoted(kit_home / HOOK_SCRIPT_NAME), *args])


def render_agent(platform: str, model: Optional[str], python: str, kit_home: Path) -> str:
    if platform not in PLATFORMS:
        raise ValueError(f"plataforma desconhecida: {platform}")
    frontmatter = (KIT_ROOT / "adapters" / f"{platform}.frontmatter.yaml").read_text(encoding="utf-8")
    if model:
        frontmatter = frontmatter.replace("{{MODEL}}", model)
    else:
        frontmatter = "\n".join(line for line in frontmatter.splitlines() if "{{MODEL}}" not in line) + "\n"
    frontmatter = frontmatter.replace(
        "{{GUARD_ALWAYS_CMD}}", hook_command(python, kit_home, "guard", "--host", "claude", "--always")
    )
    body = (
        (KIT_ROOT / "verifier" / "protocol.md").read_text(encoding="utf-8").rstrip()
        + "\n\n---\n\n"
        + (KIT_ROOT / "verifier" / "report-format.md").read_text(encoding="utf-8").rstrip()
        + "\n"
    )
    body = (
        body.replace("{{KIT_VERSION}}", kit_version())
        .replace("{{PLATFORM}}", platform)
        .replace("{{RECORD_CMD}}", hook_command(python, kit_home, "record"))
    )
    rendered = f"---\n{frontmatter.rstrip()}\n---\n\n{body}"
    leftover = [tok for tok in ("{{MODEL}}", "{{KIT_VERSION}}", "{{PLATFORM}}", "{{RECORD_CMD}}", "{{GUARD_ALWAYS_CMD}}") if tok in rendered]
    if leftover:
        raise RuntimeError(f"placeholders não substituídos: {leftover}")
    return rendered


def cursor_hooks(python: str, kit_home: Path) -> Dict[str, List[dict]]:
    """Entries for ~/.cursor/hooks.json (merged under the "hooks" key)."""
    cmd = lambda *a: hook_command(python, kit_home, *a)  # noqa: E731
    return {
        "sessionStart": [{"command": cmd("session-start", "--host", "cursor")}],
        "subagentStart": [{"command": cmd("mark-start", "--host", "cursor"), "matcher": "delpi-verifier"}],
        "subagentStop": [{"command": cmd("mark-stop", "--host", "cursor"), "matcher": "delpi-verifier"}],
        "afterFileEdit": [{"command": cmd("track-edit", "--host", "cursor")}],
        "beforeShellExecution": [{"command": cmd("guard", "--host", "cursor")}],
        "preToolUse": [{"command": cmd("guard", "--host", "cursor")}],
        "stop": [{"command": cmd("stop-gate", "--host", "cursor"), "loop_limit": 2}],
    }


def devin_hooks(python: str, kit_home: Path) -> Dict[str, List[dict]]:
    """Entries for the "hooks" key of ~/.config/devin/config.json."""

    def group(matcher: str, *args: str) -> dict:
        return {"matcher": matcher, "hooks": [{"type": "command", "command": hook_command(python, kit_home, *args)}]}

    return {
        "SessionStart": [group("", "session-start", "--host", "devin")],
        "PreToolUse": [
            group("^run_subagent$", "mark-start", "--host", "devin"),
            group("^(exec|write|edit|apply_patch|notebook_edit)$", "guard", "--host", "devin"),
        ],
        "PostToolUse": [
            group("^run_subagent$", "mark-stop", "--host", "devin"),
            group("^(write|edit|apply_patch|notebook_edit)$", "track-edit", "--host", "devin"),
        ],
        "Stop": [group("", "stop-gate", "--host", "devin")],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--kit-home", type=Path, default=Path.home() / ".delpi-agent-kit")
    for platform in PLATFORMS:
        parser.add_argument(f"--{platform}-model", default=None)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for platform in PLATFORMS:
        target = args.out / platform / "delpi-verifier.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_agent(platform, getattr(args, f"{platform}_model"), args.python, args.kit_home), encoding="utf-8")
    (args.out / "cursor" / "hooks.json").write_text(
        json.dumps({"version": 1, "hooks": cursor_hooks(args.python, args.kit_home)}, indent=2), encoding="utf-8"
    )
    (args.out / "devin" / "hooks.json").write_text(
        json.dumps({"hooks": devin_hooks(args.python, args.kit_home)}, indent=2), encoding="utf-8"
    )
    print(f"gerado em {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
