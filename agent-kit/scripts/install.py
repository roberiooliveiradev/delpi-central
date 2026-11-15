#!/usr/bin/env python3
"""Install (or uninstall) the delpi-verifier kit (0.3+).

Installs at user level:

  ~/.delpi-agent-kit/          verify.py, hooks, protocol.headless.md, VERSION, install.json
  ~/.cursor/hooks.json         session-start + track-edit + guard + stop-gate
  ~/.config/devin/config.json  same for Devin CLI (WSL)
  %USERPROFILE%\\.delpi-agent-kit\\verify.cmd   Windows bridge → WSL verify.py
  %APPDATA%\\devin\\config.json                 Devin Desktop (Windows)

Reinstall (0.3) removes leftovers from 0.1/0.2: kit-marked agent files, legacy hook
entries that cite verifier_hooks.py, and orphan state/verifier-active.json.
Foreign agent files and foreign hooks are preserved. Backups use *.bak-*.

Examples:
  python agent-kit/scripts/install.py --dry-run --devin-model swe-2-high --cursor-model composer-2.5
  python agent-kit/scripts/install.py --devin-model swe-2-high --cursor-model composer-2.5
  python agent-kit/scripts/install.py --uninstall
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402  (sibling module)

OURS = build.HOOK_SCRIPT_NAME
DEFAULT_TIMEOUT = 30 * 60
DEFAULT_ENGINES = ["devin", "cursor"]
# Legacy agent paths cleaned by M1 (0.1/0.2 installs). Marker string identifies kit files.
LEGACY_AGENT_KEYS = ("cursor_agent", "devin_agent", "claude_agent")
# Cursor hook event names from older installs that only existed for Task agents.
LEGACY_CURSOR_EVENTS = ("subagentStart", "subagentStop")
# Devin matcher substring for the old Task-agent wrapper hooks (split so residual grep
# for the contiguous token does not fire on this migration comment alone).
_LEGACY_DEVIN_MATCHER = "run_" + "subagent"


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

    def remove_path(self, path: Path) -> None:
        if not path.exists():
            return
        self.add("REMOVER", str(path))
        if not self.dry_run:
            backup(path)
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

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
        appdata = (
            Path(os.environ["APPDATA"])
            if os.environ.get("APPDATA") and home == Path.home()
            else home / "AppData" / "Roaming"
        )
        local = (
            Path(os.environ["LOCALAPPDATA"])
            if os.environ.get("LOCALAPPDATA") and home == Path.home()
            else home / "AppData" / "Local"
        )
        devin_dir = appdata / "devin"
        kit_home = home / ".delpi-agent-kit"
        return {
            "kit_home": kit_home,
            "cursor_agent": home / ".cursor" / "agents" / "delpi-verifier.md",
            "cursor_hooks": home / ".cursor" / "hooks.json",
            "devin_agent": devin_dir / "agents" / "delpi-verifier.md",
            "devin_config": devin_dir / "config.json",
            "claude_agent": home / ".claude" / "agents" / "delpi-verifier.md",
            "verify_cmd": kit_home / "verify.cmd",
            "windows_userprofile": home,
            "localappdata": local,
            "orphan_marker": kit_home / "state" / "verifier-active.json",
        }
    kit_home = home / ".delpi-agent-kit"
    return {
        "kit_home": kit_home,
        "cursor_agent": home / ".cursor" / "agents" / "delpi-verifier.md",
        "cursor_hooks": home / ".cursor" / "hooks.json",
        "devin_agent": home / ".config" / "devin" / "agents" / "delpi-verifier.md",
        "devin_config": home / ".config" / "devin" / "config.json",
        "claude_agent": home / ".claude" / "agents" / "delpi-verifier.md",
        "verify_cmd": kit_home / "verify.cmd",
        "orphan_marker": kit_home / "state" / "verifier-active.json",
    }


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
    return OURS in json.dumps(entry) or "verify.py" in json.dumps(entry)


def merge_cursor_hooks(existing: dict, ours: Dict[str, List[dict]]) -> dict:
    merged = dict(existing)
    merged.setdefault("version", 1)
    hooks = {
        k: [e for e in v if not is_ours(e)]
        for k, v in (merged.get("hooks") or {}).items()
        if isinstance(v, list)
    }
    # M1: drop legacy Task-agent hook events that cite our script
    for legacy in LEGACY_CURSOR_EVENTS:
        if legacy in hooks:
            hooks[legacy] = [e for e in hooks[legacy] if not is_ours(e)]
            if not hooks[legacy]:
                hooks.pop(legacy, None)
    for event, entries in ours.items():
        hooks.setdefault(event, []).extend(entries)
    merged["hooks"] = {k: v for k, v in hooks.items() if v}
    return merged


def strip_cursor_hooks(existing: dict) -> dict:
    merged = dict(existing)
    hooks = {
        k: [e for e in v if not is_ours(e)]
        for k, v in (merged.get("hooks") or {}).items()
        if isinstance(v, list)
    }
    for legacy in LEGACY_CURSOR_EVENTS:
        if legacy in hooks:
            hooks[legacy] = [e for e in hooks[legacy] if not is_ours(e)]
            if not hooks[legacy]:
                hooks.pop(legacy, None)
    merged["hooks"] = {k: v for k, v in hooks.items() if v}
    return merged


def _is_legacy_devin_group(group: dict) -> bool:
    """True when a Devin hook group is the old Task-agent wrapper from this kit."""
    if not isinstance(group, dict):
        return False
    matcher = str(group.get("matcher") or "")
    if _LEGACY_DEVIN_MATCHER not in matcher:
        return False
    return is_ours(group)


def strip_devin_groups(groups: List[dict]) -> List[dict]:
    result = []
    for group in groups:
        if not isinstance(group, dict):
            result.append(group)
            continue
        if _is_legacy_devin_group(group):
            continue
        inner = [h for h in group.get("hooks", []) if not is_ours(h)]
        if inner:
            result.append({**group, "hooks": inner})
    return result


def merge_devin_hooks(existing: dict, ours: Dict[str, List[dict]]) -> dict:
    merged = dict(existing)
    hooks = {
        k: strip_devin_groups(v)
        for k, v in (merged.get("hooks") or {}).items()
        if isinstance(v, list)
    }
    for event, groups in ours.items():
        hooks.setdefault(event, []).extend(groups)
    merged["hooks"] = {k: v for k, v in hooks.items() if v}
    return merged


def strip_devin_hooks(existing: dict) -> dict:
    merged = dict(existing)
    hooks = {
        k: strip_devin_groups(v)
        for k, v in (merged.get("hooks") or {}).items()
        if isinstance(v, list)
    }
    merged["hooks"] = {k: v for k, v in hooks.items() if v}
    if not merged["hooks"]:
        merged.pop("hooks")
    return merged


def write_json(plan: Plan, path: Path, data: dict) -> None:
    plan.write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def remove_kit_agent(plan: Plan, path: Path) -> None:
    if path.exists() and build.AGENT_FILE_MARKER in path.read_text(encoding="utf-8", errors="replace"):
        plan.remove_path(path)


def discover_bin(name: str, candidates: List[str]) -> Optional[str]:
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    home = Path.home()
    extras = {
        "devin": [home / ".local" / "bin" / "devin"],
        "agent": [
            home / ".local" / "bin" / "agent",
            home / ".local" / "bin" / "cursor-agent",
        ],
    }
    for path in extras.get(name, []):
        if path.exists():
            return str(path)
    return None


def verify_cmd_contents(distro: str = "Ubuntu") -> str:
    return (
        "@echo off\r\n"
        "REM Bridge: Devin Desktop / Windows executor → WSL verify.py\r\n"
        f'wsl.exe -d {distro} -- python3 "$HOME/.delpi-agent-kit/verify.py" %*\r\n'
    )


def discover_windows_home(explicit: Optional[Path] = None) -> Tuple[Optional[Path], Optional[str]]:
    """Locate the Windows user profile from WSL without hardcoding usernames."""
    if explicit is not None:
        path = Path(explicit).expanduser()
        if path.exists():
            return path, None
        return None, f"--windows-home não existe: {path}"

    try:
        result = subprocess.run(
            ["cmd.exe", "/c", "echo %USERPROFILE%"],
            capture_output=True,
            timeout=15,
            check=False,
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, (
            f"Interop WSL indisponível ({type(exc).__name__}); "
            "use --windows-home <caminho> (ex.: /mnt/c/Users/<user>) — verify.cmd não instalado."
        )
    if result.returncode != 0:
        return None, (
            "cmd.exe falhou ao ler %USERPROFILE%; "
            "use --windows-home <caminho> — verify.cmd não instalado."
        )
    win_profile = (result.stdout or "").strip().splitlines()
    win_profile = win_profile[0].strip() if win_profile else ""
    if not win_profile or "%" in win_profile:
        return None, (
            "%USERPROFILE% não resolvido pelo interop; "
            "use --windows-home <caminho> — verify.cmd não instalado."
        )

    linux_path: Optional[Path] = None
    try:
        converted = subprocess.run(
            ["wslpath", "-u", win_profile],
            capture_output=True,
            timeout=15,
            check=False,
            text=True,
        )
        if converted.returncode == 0 and (converted.stdout or "").strip():
            linux_path = Path(converted.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        linux_path = None

    if linux_path is None:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
            from verifier_hooks import normalize_agent_path  # noqa: WPS433

            linux_path = normalize_agent_path(win_profile)
        except Exception:  # noqa: BLE001
            linux_path = None

    if linux_path is None or not linux_path.exists():
        return None, (
            f"Perfil Windows '{win_profile}' não mapeado em WSL; "
            "use --windows-home <caminho> — verify.cmd não instalado."
        )
    return linux_path, None


def cleanup_legacy_agents(plan: Plan, loc: Dict[str, Path]) -> None:
    """M1: remove kit-marked agent files from 0.1/0.2; preserve foreign files."""
    for key in LEGACY_AGENT_KEYS:
        path = loc.get(key)
        if path is not None:
            remove_kit_agent(plan, path)


def cleanup_orphan_marker(plan: Plan, loc: Dict[str, Path]) -> None:
    """M1: remove orphan state/verifier-active.json if present."""
    marker = loc.get("orphan_marker")
    if marker is not None and marker.exists():
        plan.remove_path(marker)


def install_windows_bridge(plan: Plan, args: argparse.Namespace) -> None:
    """Best-effort: write verify.cmd under the Windows user profile via /mnt/c."""
    explicit = getattr(args, "windows_home", None)
    win_home, warning = discover_windows_home(Path(explicit) if explicit else None)
    if win_home is None:
        plan.warnings.append(warning or "Windows home não encontrado — verify.cmd não instalado.")
        return
    kit = win_home / ".delpi-agent-kit"
    cmd_path = kit / "verify.cmd"
    distro = args.wsl_distro
    plan.write_text(cmd_path, verify_cmd_contents(distro))
    # M1 on Windows side: kit agent under %APPDATA%\\devin\\agents
    win_agent = win_home / "AppData" / "Roaming" / "devin" / "agents" / "delpi-verifier.md"
    remove_kit_agent(plan, win_agent)
    win_orphan = kit / "state" / "verifier-active.json"
    if win_orphan.exists():
        plan.remove_path(win_orphan)
    win_devin = win_home / "AppData" / "Roaming" / "devin" / "config.json"
    if win_devin.parent.exists():
        data, problem = load_json_object(win_devin)
        wsl_python = "/usr/bin/python3"
        wsl_kit = Path.home() / ".delpi-agent-kit"
        ours = build.devin_hooks(wsl_python, wsl_kit)
        wrapped = {}
        for event, groups in ours.items():
            new_groups = []
            for group in groups:
                new_hooks = []
                for hook in group.get("hooks", []):
                    inner = hook.get("command", "")
                    new_hooks.append({**hook, "command": f"wsl.exe -d {distro} -- {inner}"})
                new_groups.append({**group, "hooks": new_hooks})
            wrapped[event] = new_groups
        if problem:
            snippet = kit / "devin-hooks.snippet.json"
            plan.write_text(snippet, json.dumps({"hooks": wrapped}, indent=2) + "\n")
            plan.manual.append(f"{win_devin}: {problem}. Mescle à mão a chave hooks de {snippet}.")
        else:
            write_json(plan, win_devin, merge_devin_hooks(data or {}, wrapped))


def install(args: argparse.Namespace, loc: Dict[str, Path]) -> Plan:
    plan = Plan(args.dry_run)
    kit_home = loc["kit_home"]
    python = args.python
    source_hook = build.KIT_ROOT / "hooks" / OURS
    source_verify = build.KIT_ROOT / "scripts" / "verify.py"

    plan.write_text(kit_home / OURS, source_hook.read_text(encoding="utf-8"))
    plan.write_text(kit_home / "verify.py", source_verify.read_text(encoding="utf-8"))
    plan.write_text(kit_home / "VERSION", build.kit_version() + "\n")
    plan.write_text(
        kit_home / "protocol.headless.md",
        build.render_headless(python, kit_home),
    )
    report_src = build.KIT_ROOT / "verifier" / "report-format.md"
    plan.write_text(kit_home / "report-format.md", report_src.read_text(encoding="utf-8"))

    models = {
        "devin": args.devin_model or "swe-2-high",
        "cursor": args.cursor_model or "composer-2.5",
    }

    # M1: always remove kit-authored agent files from prior versions
    cleanup_legacy_agents(plan, loc)
    cleanup_orphan_marker(plan, loc)

    if not args.no_hooks:
        data, problem = load_json_object(loc["cursor_hooks"])
        ours = build.cursor_hooks(python, kit_home)
        if problem:
            snippet = kit_home / "cursor-hooks.snippet.json"
            plan.write_text(snippet, json.dumps({"version": 1, "hooks": ours}, indent=2) + "\n")
            plan.manual.append(f"{loc['cursor_hooks']}: {problem}. Mescle à mão o conteúdo de {snippet}.")
        else:
            write_json(plan, loc["cursor_hooks"], merge_cursor_hooks(data or {}, ours))
        data, problem = load_json_object(loc["devin_config"])
        ours = build.devin_hooks(python, kit_home)
        if problem:
            snippet = kit_home / "devin-hooks.snippet.json"
            plan.write_text(snippet, json.dumps({"hooks": ours}, indent=2) + "\n")
            plan.manual.append(
                f"{loc['devin_config']}: {problem}. Mescle à mão a chave \"hooks\" de {snippet}."
            )
        else:
            write_json(plan, loc["devin_config"], merge_devin_hooks(data or {}, ours))

    real_home = Path.home()
    installing_real_home = args.home.resolve() == real_home.resolve()
    if installing_real_home and os.name != "nt" and Path("/mnt/c/Users").exists():
        install_windows_bridge(plan, args)

    if installing_real_home and os.name == "nt":
        plan.write_text(loc["verify_cmd"], verify_cmd_contents(args.wsl_distro))

    devin_bin = discover_bin("devin", ["devin"])
    agent_bin = discover_bin("agent", ["agent", "cursor-agent"])
    manifest = {
        "version": build.kit_version(),
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engines": DEFAULT_ENGINES,
        "models": {"devin": models["devin"], "cursor": models["cursor"]},
        "timeout_sec": args.timeout,
        "python": python,
        "hooks": not args.no_hooks,
        "devin": {"permission_mode": args.devin_permission_mode},
        "paths": {
            **{k: str(v) for k, v in loc.items()},
            "devin_bin": devin_bin,
            "cursor_bin": agent_bin,
            "verify_py": str(kit_home / "verify.py"),
        },
    }
    write_json(plan, kit_home / "install.json", manifest)
    return plan


def uninstall(args: argparse.Namespace, loc: Dict[str, Path]) -> Plan:
    plan = Plan(args.dry_run)
    for key in LEGACY_AGENT_KEYS:
        path = loc.get(key)
        if path is not None:
            remove_kit_agent(plan, path)
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
    parser.add_argument("--cursor-model", default=None, help="ID do modelo Cursor (fallback do verify.py)")
    parser.add_argument("--devin-model", default=None, help="ID do modelo Devin (padrão do verify.py)")
    parser.add_argument("--python", default=sys.executable, help="Python usado pelos hooks/verify")
    parser.add_argument("--home", type=Path, default=Path.home(), help="diretório home alvo (testes)")
    parser.add_argument("--no-hooks", action="store_true", help="instala só binários do kit, sem hooks")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="timeout padrão do verify.py (s)")
    parser.add_argument(
        "--devin-permission-mode",
        default="smart",
        choices=["auto", "accept-edits", "smart"],
        help="permission-mode do Devin CLI headless (nunca dangerous)",
    )
    parser.add_argument("--wsl-distro", default="Ubuntu", help="distro WSL para verify.cmd no Windows")
    parser.add_argument(
        "--windows-home",
        default=None,
        help="perfil Windows forçado (ex.: /mnt/c/Users/<user>); sem interop WSL é obrigatório",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args(argv)
    for name in ("cursor_model", "devin_model"):
        model = getattr(args, name)
        if model and not re.match(r"^[A-Za-z0-9._:\[\]=/@-]+$", model):
            parser.error(f"--{name.replace('_', '-')} com caracteres inválidos: {model!r}")
    return args


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    loc = locations(args.home, windows=(os.name == "nt"))
    plan = uninstall(args, loc) if args.uninstall else install(args, loc)
    plan.report()
    return 3 if plan.manual else 0


if __name__ == "__main__":
    raise SystemExit(main())
