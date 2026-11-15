#!/usr/bin/env python3
"""Install (or uninstall) the delpi-verifier for Cursor, Devin and, optionally, Claude Code.

Installs at user level, so the verifier is available in every project:

  ~/.delpi-agent-kit/                  hook script, VERSION, install manifest, runtime state
  ~/.cursor/agents/delpi-verifier.md   + entries merged into ~/.cursor/hooks.json
  ~/.config/devin/agents/delpi-verifier.md (Windows: %APPDATA%\\devin\\agents)
                                       + entries merged into the "hooks" key of devin config.json
  ~/.claude/agents/delpi-verifier.md   (only with --platforms ...,claude)

Safe by default: --dry-run shows the plan; every config file is backed up before it is
changed; re-running updates in place; --uninstall removes only what this kit added.

Examples:
  python agent-kit/scripts/install.py --dry-run --cursor-model <id> --devin-model <id>
  python agent-kit/scripts/install.py --cursor-model <id> --devin-model <id>
  python agent-kit/scripts/install.py --uninstall
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402  (sibling module)

OURS = build.HOOK_SCRIPT_NAME


class Plan:
    """Collects actions so --dry-run and the real run print the same summary."""

    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.lines: List[Tuple[str, str]] = []
        self.warnings: List[str] = []
        self.manual: List[str] = []

    def add(self, status: str, what: str) -> None:
        self.lines.append((status, what))

    def write_text(self, path: Path, content: str) -> None:
        if path.exists() and path.read_text(encoding="utf-8", errors="replace") == content:
            self.add("SEM_MUDANCA", str(path))
            return
        self.add("ATUALIZAR" if path.exists() else "CRIAR", str(path))
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            backup(path)
            path.write_text(content, encoding="utf-8")

    def report(self) -> None:
        mode = "SIMULAÇÃO (--dry-run): nada foi alterado" if self.dry_run else "Executado"
        print(f"\n== delpi-verifier · instalador · {mode} ==")
        for status, what in self.lines:
            print(f"  [{status:<11}] {what}")
        for item in self.manual:
            print(f"\n  AÇÃO MANUAL: {item}")
        for warning in self.warnings:
            print(f"\n  AVISO: {warning}")
        print()


def backup(path: Path) -> None:
    if path.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(path, path.with_name(f"{path.name}.bak-{stamp}"))


def locations(home: Path, windows: bool) -> Dict[str, Path]:
    if windows:
        appdata = Path(os.environ["APPDATA"]) if os.environ.get("APPDATA") and home == Path.home() else home / "AppData" / "Roaming"
        devin_dir = appdata / "devin"
    else:
        devin_dir = home / ".config" / "devin"
    return {
        "kit_home": home / ".delpi-agent-kit",
        "cursor_agent": home / ".cursor" / "agents" / "delpi-verifier.md",
        "cursor_hooks": home / ".cursor" / "hooks.json",
        "devin_agent": devin_dir / "agents" / "delpi-verifier.md",
        "devin_config": devin_dir / "config.json",
        "claude_agent": home / ".claude" / "agents" / "delpi-verifier.md",
    }


# --------------------------------------------------------------------------- #
# JSON / JSONC handling
# --------------------------------------------------------------------------- #


def has_comments(text: str) -> bool:
    in_string = False
    escape = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif text.startswith("//", i) or text.startswith("/*", i):
                return True
        i += 1
    return False


def load_json_object(path: Path) -> Tuple[Optional[dict], Optional[str]]:
    """Return (data, problem). Missing file -> ({}, None)."""
    if not path.exists():
        return {}, None
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return {}, None
    if has_comments(text):
        return None, "o arquivo tem comentários (JSONC); reescrever apagaria os comentários"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"JSON inválido ({exc})"
    if not isinstance(data, dict):
        return None, "o conteúdo não é um objeto JSON"
    return data, None


def is_ours(entry: object) -> bool:
    return OURS in json.dumps(entry)


def merge_cursor_hooks(existing: dict, ours: Dict[str, List[dict]]) -> dict:
    merged = dict(existing)
    merged.setdefault("version", 1)
    hooks = {k: [e for e in v if not is_ours(e)] for k, v in (merged.get("hooks") or {}).items() if isinstance(v, list)}
    for event, entries in ours.items():
        hooks.setdefault(event, []).extend(entries)
    merged["hooks"] = {k: v for k, v in hooks.items() if v}
    return merged


def strip_cursor_hooks(existing: dict) -> dict:
    merged = dict(existing)
    hooks = {k: [e for e in v if not is_ours(e)] for k, v in (merged.get("hooks") or {}).items() if isinstance(v, list)}
    merged["hooks"] = {k: v for k, v in hooks.items() if v}
    return merged


def strip_devin_groups(groups: List[dict]) -> List[dict]:
    result = []
    for group in groups:
        if not isinstance(group, dict):
            result.append(group)
            continue
        inner = [h for h in group.get("hooks", []) if not is_ours(h)]
        if inner:
            result.append({**group, "hooks": inner})
    return result


def merge_devin_hooks(existing: dict, ours: Dict[str, List[dict]]) -> dict:
    merged = dict(existing)
    hooks = {k: strip_devin_groups(v) for k, v in (merged.get("hooks") or {}).items() if isinstance(v, list)}
    for event, groups in ours.items():
        hooks.setdefault(event, []).extend(groups)
    merged["hooks"] = {k: v for k, v in hooks.items() if v}
    return merged


def strip_devin_hooks(existing: dict) -> dict:
    merged = dict(existing)
    hooks = {k: strip_devin_groups(v) for k, v in (merged.get("hooks") or {}).items() if isinstance(v, list)}
    merged["hooks"] = {k: v for k, v in hooks.items() if v}
    if not merged["hooks"]:
        merged.pop("hooks")
    return merged


# --------------------------------------------------------------------------- #
# Install / uninstall
# --------------------------------------------------------------------------- #


def write_agent(plan: Plan, path: Path, content: str) -> None:
    if path.exists():
        current = path.read_text(encoding="utf-8", errors="replace")
        if build.AGENT_FILE_MARKER not in current:
            plan.warnings.append(f"{path} existia e não era deste kit: foi salvo como backup antes de substituir.")
    plan.write_text(path, content)


def write_json(plan: Plan, path: Path, data: dict) -> None:
    plan.write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def install(args: argparse.Namespace, loc: Dict[str, Path]) -> Plan:
    plan = Plan(args.dry_run)
    kit_home = loc["kit_home"]
    python = args.python
    source_hook = build.KIT_ROOT / "hooks" / OURS

    plan.write_text(kit_home / OURS, source_hook.read_text(encoding="utf-8"))
    plan.write_text(kit_home / "VERSION", build.kit_version() + "\n")

    models = {p: getattr(args, f"{p}_model") for p in build.PLATFORMS}
    for platform in args.platforms:
        if not models[platform]:
            plan.warnings.append(
                f"{platform}: sem --{platform}-model. O verificador vai usar o modelo padrão da plataforma, e a "
                "independência (família diferente do executor) não fica garantida."
            )
        write_agent(plan, loc[f"{platform}_agent"], build.render_agent(platform, models[platform], python, kit_home))

    if not args.no_hooks:
        if "cursor" in args.platforms:
            data, problem = load_json_object(loc["cursor_hooks"])
            ours = build.cursor_hooks(python, kit_home)
            if problem:
                snippet = kit_home / "cursor-hooks.snippet.json"
                plan.write_text(snippet, json.dumps({"version": 1, "hooks": ours}, indent=2) + "\n")
                plan.manual.append(f"{loc['cursor_hooks']}: {problem}. Mescle à mão o conteúdo de {snippet}.")
            else:
                write_json(plan, loc["cursor_hooks"], merge_cursor_hooks(data or {}, ours))
        if "devin" in args.platforms:
            data, problem = load_json_object(loc["devin_config"])
            ours = build.devin_hooks(python, kit_home)
            if problem:
                snippet = kit_home / "devin-hooks.snippet.json"
                plan.write_text(snippet, json.dumps({"hooks": ours}, indent=2) + "\n")
                plan.manual.append(
                    f"{loc['devin_config']}: {problem}. Mescle à mão a chave \"hooks\" de {snippet} nesse arquivo."
                )
            else:
                write_json(plan, loc["devin_config"], merge_devin_hooks(data or {}, ours))
        if "claude" in args.platforms:
            plan.add("INFO", "claude: o guard vai no frontmatter do agente; o stop gate não é instalado no Claude Code")

    manifest = {
        "version": build.kit_version(),
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "platforms": args.platforms,
        "models": {p: models[p] for p in args.platforms},
        "python": python,
        "hooks": not args.no_hooks,
        "paths": {k: str(v) for k, v in loc.items()},
    }
    write_json(plan, kit_home / "install.json", manifest)
    return plan


def uninstall(args: argparse.Namespace, loc: Dict[str, Path]) -> Plan:
    plan = Plan(args.dry_run)
    for platform in build.PLATFORMS:
        path = loc[f"{platform}_agent"]
        if path.exists() and build.AGENT_FILE_MARKER in path.read_text(encoding="utf-8", errors="replace"):
            plan.add("REMOVER", str(path))
            if not args.dry_run:
                backup(path)
                path.unlink()
    for key, stripper in (("cursor_hooks", strip_cursor_hooks), ("devin_config", strip_devin_hooks)):
        path = loc[key]
        data, problem = load_json_object(path)
        if problem:
            if path.exists() and OURS in path.read_text(encoding="utf-8", errors="replace"):
                plan.manual.append(f"{path}: {problem}. Remova à mão as entradas que citam {OURS}.")
            continue
        if data and is_ours(data):
            write_json(plan, path, stripper(data))
    kit_home = loc["kit_home"]
    if kit_home.exists():
        plan.add("REMOVER", f"{kit_home} (inclui estado)")
        if not args.dry_run:
            shutil.rmtree(kit_home)
    return plan


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platforms", default="cursor,devin", help="lista separada por vírgula: cursor,devin,claude")
    for platform in build.PLATFORMS:
        parser.add_argument(f"--{platform}-model", default=None, help=f"ID do modelo do verificador no {platform}")
    parser.add_argument("--python", default=sys.executable, help="Python usado pelos hooks (padrão: o que roda este script)")
    parser.add_argument("--home", type=Path, default=Path.home(), help="diretório home alvo (testes)")
    parser.add_argument("--no-hooks", action="store_true", help="instala só os agentes, sem hooks")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args(argv)
    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    unknown = [p for p in platforms if p not in build.PLATFORMS]
    if unknown:
        parser.error(f"plataforma desconhecida: {', '.join(unknown)}")
    args.platforms = platforms
    for platform in build.PLATFORMS:
        model = getattr(args, f"{platform}_model")
        if model and not re.match(r"^[A-Za-z0-9._:\[\]=/@-]+$", model):
            parser.error(f"--{platform}-model com caracteres inválidos: {model!r}")
    return args


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    loc = locations(args.home, windows=(os.name == "nt"))
    plan = uninstall(args, loc) if args.uninstall else install(args, loc)
    plan.report()
    return 3 if plan.manual else 0


if __name__ == "__main__":
    raise SystemExit(main())
