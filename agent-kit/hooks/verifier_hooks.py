#!/usr/bin/env python3
"""delpi-verifier hooks — guard, verifier marker, stop gate and verdict ledger.

One stdlib-only script serves Cursor, Devin and Claude Code hooks. Every hook
reads the host's JSON payload from stdin and answers in the host's format.

Subcommands
  mark-start     subagent is starting  -> create the "verifier active" marker
  mark-stop      subagent finished     -> remove the marker
  activate       verify.py is launching a headless verifier session -> set marker
  guard          before a tool call    -> block writes while the verifier runs
  session-start  session began         -> store the repository baseline fingerprint
  track-edit     file edited by a tool -> mark that this session changed files
  stop-gate      agent wants to stop   -> require a recorded verdict for changes
  record         verifier's last step  -> append the verdict to the ledger
  status         print marker, baseline and latest verdict (diagnostics)
  clear          remove a stuck marker

Exit codes follow the shared hook convention: 0 = proceed, 2 = block.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

AGENT_NAME = "delpi-verifier"
CONTRACT_MARKER = "<!-- delpi-verifier:contract"
MAX_ROUNDS = 3
DEFAULT_MARKER_TTL_SECONDS = 45 * 60
GATE_PASS_VERDICTS = {
    "ACCEPT",
    "ACCEPT_WITH_RESIDUAL",
    "INCONCLUSIVE",
    "EXECUTION_DRIFT",
    "SKIPPED",
}
ALL_VERDICTS = GATE_PASS_VERDICTS | {"REWORK"}
FINGERPRINT_IGNORED_DIRS = {
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "__pycache__",
    "node_modules",
    ".next",
    ".turbo",
    ".vite",
    "coverage",
    "htmlcov",
    "dist",
    "build",
}


# --------------------------------------------------------------------------- #
# Paths and small helpers
# --------------------------------------------------------------------------- #


def kit_home() -> Path:
    override = os.environ.get("DELPI_AGENT_KIT_HOME")
    if override:
        return Path(override)
    return Path.home() / ".delpi-agent-kit"


def state_dir() -> Path:
    path = kit_home() / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def marker_path() -> Path:
    return state_dir() / "verifier-active.json"


def marker_ttl() -> int:
    try:
        return int(os.environ.get("DELPI_VERIFIER_MARKER_TTL", DEFAULT_MARKER_TTL_SECONDS))
    except ValueError:
        return DEFAULT_MARKER_TTL_SECONDS


def read_payload(raw: Optional[str] = None) -> Tuple[dict, bool]:
    """Return (payload, ok). ok=False when stdin is not a JSON object."""
    if raw is None:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not raw.strip():
        return {}, True
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}, False
    return (data, True) if isinstance(data, dict) else ({}, False)


def mentions_agent(value: object) -> bool:
    """True when any string inside value names the verifier agent."""
    if isinstance(value, str):
        return AGENT_NAME in value
    if isinstance(value, dict):
        return any(mentions_agent(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(mentions_agent(v) for v in value)
    return False


def run_git(repo: Path, args: Sequence[str]) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def repo_root(start: Path) -> Optional[Path]:
    out = run_git(start, ["rev-parse", "--show-toplevel"])
    return Path(out.strip()) if out else None


def git_dir(repo: Path) -> Optional[Path]:
    out = run_git(repo, ["rev-parse", "--absolute-git-dir"])
    return Path(out.strip()) if out else None


def ledger_path(repo: Path) -> Optional[Path]:
    gdir = git_dir(repo)
    if gdir is None:
        return None
    path = gdir / "delpi-verifier"
    path.mkdir(parents=True, exist_ok=True)
    return path / "verdicts.jsonl"


def has_contract(repo: Path) -> bool:
    agents = repo / "AGENTS.md"
    try:
        return CONTRACT_MARKER in agents.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def fingerprint(repo: Path) -> Optional[str]:
    """Hash of HEAD + tracked diff + untracked (non-ignored, non-cache) files."""
    head = run_git(repo, ["rev-parse", "HEAD"])
    if head is None:
        return None
    digest = hashlib.sha256()
    digest.update(head.strip().encode())
    diff = run_git(repo, ["diff", "HEAD", "--binary", "--no-color", "--no-ext-diff"])
    digest.update((diff or "").encode("utf-8", errors="replace"))
    untracked = run_git(repo, ["ls-files", "--others", "--exclude-standard", "-z"]) or ""
    for rel in sorted(p for p in untracked.split("\0") if p):
        if FINGERPRINT_IGNORED_DIRS.intersection(Path(rel).parts):
            continue
        digest.update(rel.encode("utf-8", errors="replace"))
        try:
            digest.update(hashlib.sha256((repo / rel).read_bytes()).digest())
        except OSError:
            digest.update(b"<unreadable>")
    return digest.hexdigest()


def session_key(payload: dict) -> str:
    for key in ("conversation_id", "session_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "unknown-session"


def payload_repo(payload: dict, host: str) -> Optional[Path]:
    candidates: List[str] = []
    roots = payload.get("workspace_roots")
    if isinstance(roots, list):
        candidates.extend(str(r) for r in roots if r)
    for key in ("cwd", "workspace_root"):
        if isinstance(payload.get(key), str):
            candidates.append(payload[key])
    if host == "devin" and os.environ.get("DEVIN_PROJECT_DIR"):
        candidates.insert(0, os.environ["DEVIN_PROJECT_DIR"])
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        candidates.append(os.environ["CLAUDE_PROJECT_DIR"])
    candidates.append(os.getcwd())
    for candidate in candidates:
        root = repo_root(Path(candidate))
        if root is not None:
            return root
    return None


def baseline_path(session: str, repo: Path) -> Path:
    key = hashlib.sha256(f"{session}|{repo}".encode()).hexdigest()[:32]
    path = state_dir() / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{key}.json"


def edits_flag_path(session: str) -> Path:
    key = hashlib.sha256(session.encode()).hexdigest()[:32]
    path = state_dir() / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{key}.edited"


def read_json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def latest_verdict(repo: Path, fp: str) -> Optional[dict]:
    ledger = ledger_path(repo)
    if ledger is None or not ledger.exists():
        return None
    found = None
    for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict) and entry.get("fingerprint") == fp:
            found = entry
    return found


def record_command_hint() -> str:
    script = kit_home() / "verifier_hooks.py"
    return f'"{sys.executable}" "{script}" record'


def clear_command_hint() -> str:
    script = kit_home() / "verifier_hooks.py"
    return f'"{sys.executable}" "{script}" clear'


# --------------------------------------------------------------------------- #
# Verifier marker
# --------------------------------------------------------------------------- #


def env_verifier_active() -> bool:
    return os.environ.get("DELPI_VERIFIER_ACTIVE", "").strip() in {"1", "true", "TRUE", "yes", "YES"}


def marker_active(now: Optional[float] = None) -> bool:
    if env_verifier_active():
        return True
    data = read_json(marker_path())
    if not data:
        return False
    started = data.get("started_at")
    if not isinstance(started, (int, float)):
        return False
    return ((now or time.time()) - started) < marker_ttl()


def set_marker(host: str, payload: Optional[dict] = None) -> None:
    payload = payload or {}
    marker_path().write_text(
        json.dumps(
            {
                "started_at": time.time(),
                "host": host,
                "session": session_key(payload) if payload else "verify.py",
            }
        ),
        encoding="utf-8",
    )


def clear_marker() -> None:
    try:
        marker_path().unlink()
    except FileNotFoundError:
        pass


# --------------------------------------------------------------------------- #
# Command classifier (used by guard)
# --------------------------------------------------------------------------- #

SEPARATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", ";;"}
REDIRECTS_TO_FILE = {">", ">>", ">|", "&>", "&>>"}
WRAPPERS = {"sudo", "env", "command", "time", "nohup", "nice", "stdbuf", "timeout", "builtin"}
READ_ONLY_FIND_EXEC = {"grep", "egrep", "fgrep", "rg", "cat", "head", "tail", "wc", "ls", "file", "stat", "md5sum", "sha256sum"}

ALWAYS_BLOCKED = {
    "rm", "rmdir", "mv", "cp", "touch", "mkdir", "chmod", "chown", "chgrp", "ln",
    "truncate", "dd", "tee", "install", "unlink", "shred", "ssh", "scp", "sftp",
    "rsync", "kill", "pkill", "killall", "shutdown", "reboot", "crontab",
    "systemctl", "service", "eval", "apt", "apt-get", "yum", "dnf", "apk", "brew",
    "choco", "winget", "scoop", "wget", "patch", "git-lfs", "mount", "umount",
}
GIT_READ = {
    "status", "diff", "log", "show", "blame", "rev-parse", "ls-files", "ls-tree",
    "cat-file", "describe", "shortlog", "grep", "merge-base", "name-rev",
    "for-each-ref", "count-objects", "help", "version", "show-ref", "rev-list",
    "check-ignore", "var", "whatchanged",
}
PKG_MANAGERS = {"npm", "pnpm", "yarn", "bun"}
PKG_WRITE_SUBCOMMANDS = {
    "install", "i", "add", "remove", "rm", "uninstall", "un", "update", "up",
    "upgrade", "ci", "publish", "link", "unlink", "prune", "dedupe", "pack",
    "version", "init", "create", "set", "import",
}
PY_PKG = {"pip", "pip3", "uv", "poetry", "pipenv", "conda", "mamba", "pdm"}
PY_PKG_WRITE = {"install", "uninstall", "add", "remove", "sync", "lock", "update", "upgrade", "venv", "init", "publish", "build"}
RISKY_SCRIPT_NAME = re.compile(
    r"(deploy|release|publish|migrat|seed|reset|prod|push|install|clean|teardown|destroy|drop|upgrade|db:)",
    re.IGNORECASE,
)
SQL_WRITE = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|merge|replace|copy|vacuum|reindex|call|exec)\b",
    re.IGNORECASE,
)
INLINE_CODE_WRITE = re.compile(
    r"(open\([^)]*['\"][wax+]|write_text|write_bytes|unlink|rmtree|remove\(|rename\(|"
    r"os\.system|subprocess|shutil\.|writeFile|appendFile|fs\.rm|rmSync|mkdir|"
    r"child_process|execSync|spawn)",
)
CLI_RO_SUBCOMMANDS = {
    "docker": {"ps", "images", "logs", "inspect", "version", "info", "stats", "top", "port", "diff", "history"},
    "podman": {"ps", "images", "logs", "inspect", "version", "info", "stats", "top", "port"},
    "kubectl": {"get", "describe", "logs", "top", "version", "explain", "api-resources", "cluster-info"},
    "helm": {"list", "ls", "status", "template", "lint", "show", "get", "history", "version"},
    "terraform": {"plan", "validate", "show", "version", "providers", "output", "fmt"},
    "alembic": {"current", "history", "heads", "branches", "show", "check"},
    "gh": {"pr", "issue", "run", "repo", "status", "search", "release", "workflow"},
}
DOCKER_COMPOSE_RO = {"ps", "logs", "config", "images", "ls", "top", "version", "port"}
GH_RO_ACTIONS = {"view", "list", "diff", "checks", "status", "watch"}


def tokenize(command: str) -> Optional[List[str]]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return None


def split_segments(tokens: List[str]) -> List[List[str]]:
    segments: List[List[str]] = [[]]
    for tok in tokens:
        if tok in SEPARATORS:
            segments.append([])
        else:
            segments[-1].append(tok)
    return [s for s in segments if s]


def find_redirect_problem(tokens: List[str]) -> Optional[str]:
    for i, tok in enumerate(tokens):
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        if tok in REDIRECTS_TO_FILE and nxt != "/dev/null":
            return f"redirecionamento para arquivo ({tok} {nxt})"
        if tok in {">&", "&>"} and nxt and not nxt.isdigit() and nxt != "/dev/null" and nxt != "-":
            return f"redirecionamento para arquivo ({tok} {nxt})"
    return None


def strip_wrappers(segment: List[str]) -> List[str]:
    seg = list(segment)
    while seg:
        head = seg[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", head):
            seg = seg[1:]
            continue
        if Path(head).name in WRAPPERS:
            seg = seg[1:]
            while seg and seg[0].startswith("-"):
                seg = seg[1:]
            if Path(segment[0]).name == "timeout" and seg and re.match(r"^\d", seg[0]):
                seg = seg[1:]
            continue
        break
    return seg


def first_positional(args: List[str], skip_with_value: Iterable[str] = ()) -> Tuple[Optional[str], List[str]]:
    skip = set(skip_with_value)
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in skip:
            i += 2
            continue
        if arg.startswith("-"):
            i += 1
            continue
        return arg, args[i + 1:]
    return None, []


def is_record_command(segment: List[str]) -> bool:
    if len(segment) < 2:
        return False
    if not re.match(r"^python[0-9.]*(\.exe)?$", Path(segment[0]).name, re.IGNORECASE):
        return False
    return Path(segment[1]).name == "verifier_hooks.py" and len(segment) > 2 and segment[2] in {"record", "status", "clear", "activate"}


def is_verify_command(segment: List[str]) -> bool:
    """Allow the executor to launch verify.py (python …/verify.py …) only."""
    if len(segment) < 2:
        return False
    if not re.match(r"^python[0-9.]*(\.exe)?$", Path(segment[0]).name, re.IGNORECASE):
        return False
    return Path(segment[1]).name.lower() == "verify.py"


def classify_git(args: List[str]) -> Optional[str]:
    sub, rest = first_positional(args, skip_with_value={"-C", "-c", "--git-dir", "--work-tree"})
    if sub is None:
        return None
    if sub in GIT_READ:
        return None
    if sub == "branch":
        writing = [a for a in rest if not a.startswith("-") or a in {"-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy", "-f", "--force", "-u", "--set-upstream-to", "--unset-upstream"}]
        return None if not writing else "git branch com alteração"
    if sub == "remote":
        return None if (not rest or rest[0] in {"-v", "show", "get-url"}) else "git remote com alteração"
    if sub == "config":
        return None if any(a in {"--get", "--get-all", "--list", "-l", "--get-regexp", "--show-origin"} for a in rest) else "git config com escrita"
    if sub in {"worktree", "stash"}:
        return None if (rest and rest[0] in {"list", "show"}) else f"git {sub} com alteração"
    if sub == "reflog":
        return None if (not rest or rest[0] in {"show"} or rest[0].startswith("-")) else "git reflog com alteração"
    if sub == "tag":
        return None if (not rest or rest[0] in {"-l", "--list", "-n", "--contains", "--points-at"}) else "git tag com alteração"
    if sub == "symbolic-ref":
        return None if len([a for a in rest if not a.startswith("-")]) <= 1 else "git symbolic-ref com escrita"
    return f"git {sub} altera estado"


def classify_segment(segment: List[str], depth: int = 0) -> Optional[str]:
    seg = strip_wrappers(segment)
    if not seg:
        return None
    cmd = Path(seg[0]).name.lower()
    if cmd.endswith(".exe"):
        cmd = cmd[:-4]
    args = seg[1:]

    if cmd == "xargs":
        inner, inner_rest = first_positional(args, skip_with_value={"-I", "-n", "-P", "-L", "-d", "-a", "-E", "-s"})
        return classify_segment([inner, *inner_rest], depth + 1) if inner else None
    if cmd in {"bash", "sh", "zsh", "dash", "fish", "pwsh", "powershell", "cmd"} and depth < 3:
        for flag in ("-c", "-Command", "/c", "/C"):
            if flag in args:
                idx = args.index(flag)
                inner = args[idx + 1] if idx + 1 < len(args) else ""
                return classify_command(inner, depth + 1)
        return None
    if cmd in ALWAYS_BLOCKED:
        return f"`{cmd}` altera estado"
    if re.search(r"(deploy|up-prod|release\.sh|publish)", cmd):
        return f"`{cmd}` parece deploy/publicação"
    if cmd == "git":
        return classify_git(args)
    if cmd == "sed" and any(a == "-i" or a.startswith("-i") or a.startswith("--in-place") for a in args):
        return "sed -i edita arquivo"
    if cmd == "perl" and any(re.match(r"^-\w*i", a) for a in args):
        return "perl -i edita arquivo"
    if cmd == "find":
        if "-delete" in args:
            return "find -delete apaga arquivos"
        for flag in ("-exec", "-execdir", "-ok", "-okdir"):
            if flag in args:
                idx = args.index(flag)
                inner = Path(args[idx + 1]).name if idx + 1 < len(args) else ""
                if inner not in READ_ONLY_FIND_EXEC:
                    return f"find {flag} {inner}"
        return None
    if cmd in PKG_MANAGERS:
        sub, rest = first_positional(args)
        if sub in PKG_WRITE_SUBCOMMANDS:
            return f"{cmd} {sub} altera dependências"
        if sub == "run" and rest and RISKY_SCRIPT_NAME.search(rest[0]):
            return f"{cmd} run {rest[0]} parece operação de escrita"
        if sub and sub not in {"run", "test", "t", "exec", "x", "list", "ls", "why", "outdated", "audit", "view", "info", "help", "-v", "--version", "dlx"} and RISKY_SCRIPT_NAME.search(sub):
            return f"{cmd} {sub} parece operação de escrita"
        return None
    if cmd in PY_PKG:
        sub, _ = first_positional(args)
        return f"{cmd} {sub} altera dependências" if sub in PY_PKG_WRITE else None
    if re.match(r"^python[0-9.]*$", cmd) or cmd in {"py", "node", "ruby", "deno"}:
        if "-m" in args:
            mod = args[args.index("-m") + 1] if args.index("-m") + 1 < len(args) else ""
            if mod in {"pip", "pip3"}:
                sub, _ = first_positional(args[args.index("-m") + 2:])
                return f"pip {sub} altera dependências" if sub in PY_PKG_WRITE else None
        for flag in ("-c", "-e", "--eval", "-p"):
            if flag in args:
                idx = args.index(flag)
                code = args[idx + 1] if idx + 1 < len(args) else ""
                if INLINE_CODE_WRITE.search(code):
                    return "código inline com escrita/processo"
        if any(Path(a).name == "manage.py" for a in args):
            mgmt = args[[Path(a).name for a in args].index("manage.py") + 1:]
            if mgmt and mgmt[0] in {"migrate", "makemigrations", "flush", "loaddata", "createsuperuser", "dbshell", "shell", "collectstatic", "squashmigrations"}:
                return f"manage.py {mgmt[0]} altera estado"
        return None
    if cmd in {"docker", "podman"}:
        sub, rest = first_positional(args, skip_with_value={"-H", "--context", "-c"})
        if sub == "compose":
            csub, _ = first_positional(rest, skip_with_value={"-f", "--file", "-p", "--project-name", "--profile", "--env-file"})
            return None if csub in DOCKER_COMPOSE_RO else f"docker compose {csub} altera containers"
        return None if sub in CLI_RO_SUBCOMMANDS[cmd] else f"{cmd} {sub} altera estado"
    if cmd == "docker-compose":
        csub, _ = first_positional(args, skip_with_value={"-f", "--file", "-p", "--project-name", "--profile", "--env-file"})
        return None if csub in DOCKER_COMPOSE_RO else f"docker-compose {csub} altera containers"
    if cmd == "gh":
        sub, rest = first_positional(args)
        if sub == "api":
            write_flags = {"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input"}
            if any(a in write_flags for a in rest):
                method_idx = next((i for i, a in enumerate(rest) if a in {"-X", "--method"}), None)
                if method_idx is not None and method_idx + 1 < len(rest) and rest[method_idx + 1].upper() in {"GET", "HEAD"} and not any(a in {"-f", "-F", "--field", "--raw-field", "--input"} for a in rest):
                    return None
                return "gh api com escrita"
            return None
        if sub in CLI_RO_SUBCOMMANDS["gh"]:
            action, _ = first_positional(rest)
            return None if (action is None or action in GH_RO_ACTIONS) else f"gh {sub} {action} altera estado"
        return f"gh {sub} altera estado" if sub else None
    if cmd in {"kubectl", "helm", "terraform", "alembic"}:
        sub, _ = first_positional(args)
        return None if (sub is None or sub in CLI_RO_SUBCOMMANDS[cmd]) else f"{cmd} {sub} altera estado"
    if cmd in {"flyway", "liquibase"}:
        sub, _ = first_positional(args)
        return None if sub in {"info", "validate", "status", "history", "diff"} else f"{cmd} {sub} altera banco"
    if cmd in {"prisma", "knex", "sequelize", "rails", "rake"}:
        joined = " ".join(args)
        if re.search(r"(migrate|db:|db push|seed|reset)", joined):
            return f"{cmd} {joined[:40]} altera banco"
        return None
    if cmd in {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "mongo", "mongosh", "redis-cli", "cqlsh"}:
        if any(a in {"-f", "--file", "-i"} for a in args):
            return f"{cmd} executando arquivo SQL (não inspecionável)"
        if SQL_WRITE.search(" ".join(args)):
            return f"{cmd} com comando de escrita"
        if cmd == "redis-cli" and any(a.upper() in {"SET", "DEL", "FLUSHALL", "FLUSHDB", "HSET", "LPUSH", "RPUSH", "EXPIRE", "INCR"} for a in args):
            return "redis-cli com escrita"
        return None
    if cmd == "curl":
        flags = set(args)
        for i, a in enumerate(args):
            if a in {"-X", "--request"} and i + 1 < len(args) and args[i + 1].upper() not in {"GET", "HEAD", "OPTIONS"}:
                return f"curl {args[i + 1]} escreve"
            if re.match(r"^-X(?!GET|HEAD|OPTIONS)[A-Z]+$", a):
                return f"curl {a} escreve"
        writing = {"-d", "--data", "--data-raw", "--data-binary", "--data-urlencode", "-F", "--form", "-T", "--upload-file", "-o", "--output", "-O", "--remote-name", "--json"}
        if flags & writing:
            return "curl envia dados ou grava arquivo"
        return None
    if cmd in {"http", "https", "xh"}:
        if args and args[0].upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            return f"{cmd} {args[0]} escreve"
        return None
    if cmd == "make":
        targets = [a for a in args if not a.startswith("-") and "=" not in a]
        risky = [t for t in targets if RISKY_SCRIPT_NAME.search(t)]
        return f"make {risky[0]} parece operação de escrita" if risky else None
    return None


def classify_command(command: str, depth: int = 0) -> Optional[str]:
    """Return a block reason for a shell command, or None when it is allowed."""
    if not command or not command.strip():
        return None
    tokens = tokenize(command)
    if tokens is None:
        return "comando com aspas desbalanceadas (não inspecionável)"
    if "`" in command or "$(" in command or "<(" in command or ">(" in command:
        return "substituição de comando (`...`, $(...), <(...)) não é inspecionável"
    problem = find_redirect_problem(tokens)
    if problem:
        return problem
    segments = split_segments(tokens)
    if len(segments) == 1 and (is_record_command(segments[0]) or is_verify_command(segments[0])):
        return None
    for segment in segments:
        reason = classify_segment(segment, depth)
        if reason:
            return reason
    return None


# --------------------------------------------------------------------------- #
# Tool classifier per host
# --------------------------------------------------------------------------- #

WRITE_TOOL = re.compile(r"(write|edit|replace|delete|patch|create|move|rename|notebook|apply)", re.IGNORECASE)
READ_TOOL = re.compile(r"(read|get|list|search|query|fetch|describe|find|show|grep|glob|view|status)", re.IGNORECASE)
SHELL_TOOLS = {"shell", "bash", "terminal", "run_terminal_cmd", "exec", "powershell"}


def extract_shell_command(payload: dict) -> Optional[str]:
    if isinstance(payload.get("command"), str):
        return payload["command"]
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    return None


def classify_tool_call(payload: dict) -> Optional[str]:
    tool = str(payload.get("tool_name") or payload.get("hook_event_name") or "")
    lower = tool.lower()
    command = extract_shell_command(payload)
    if lower in SHELL_TOOLS or payload.get("hook_event_name") == "beforeShellExecution" or (command is not None and not WRITE_TOOL.search(lower)):
        return classify_command(command or "")
    if lower in {"task", "run_subagent"}:
        return "o verificador não delega para outros agentes"
    if "mcp" in lower:
        return None if READ_TOOL.search(lower) else f"ferramenta MCP `{tool}` pode alterar dados"
    if lower in {"read", "grep", "glob", "ls", "webfetch", "todo_write", "todowrite", "get_output"}:
        return None
    if WRITE_TOOL.search(lower) and not READ_TOOL.search(lower):
        return f"ferramenta `{tool}` edita arquivos"
    return None


# --------------------------------------------------------------------------- #
# Host-specific responses
# --------------------------------------------------------------------------- #


def respond_allow(host: str) -> int:
    if host == "cursor":
        print("{}")
    return 0


def respond_block(host: str, reason: str) -> int:
    message = (
        f"[delpi-verifier] Bloqueado: {reason}. O verificador não altera estado. "
        "Se este comando era necessário para verificar, marque o item como TEST_NOT_RUN "
        "e explique no relatório; não tente contornar. Se você é o executor e o verificador já "
        f"terminou, o marcador ficou preso: rode {clear_command_hint()}."
    )
    if host == "cursor":
        print(json.dumps({"permission": "deny", "agent_message": message, "user_message": message}))
    elif host == "devin":
        print(json.dumps({"decision": "block", "reason": message}))
    elif host == "claude":
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            }
        }))
    sys.stderr.write(message + "\n")
    return 2


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #


def targets_verifier(payload: dict) -> bool:
    """True when the subagent being started/stopped is the verifier.

    Cursor and Claude name the subagent in a dedicated field. Devin passes the
    run_subagent arguments; we look at identity-like keys first so that a prompt
    that merely mentions the verifier does not count.
    """
    for key in ("subagent_type", "agent_type"):
        if mentions_agent(payload.get(key)):
            return True
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        identity_keys = [k for k in tool_input if re.search(r"(profile|agent|subagent|type|name)", k, re.IGNORECASE)]
        if identity_keys:
            return any(mentions_agent(tool_input[k]) for k in identity_keys)
        return mentions_agent(tool_input)
    return False


def cmd_mark_start(host: str, payload: dict) -> int:
    if targets_verifier(payload):
        set_marker(host, payload)
    return respond_allow(host)


def cmd_mark_stop(host: str, payload: dict) -> int:
    if targets_verifier(payload):
        clear_marker()
    if host == "cursor":
        print("{}")
    return 0


def cmd_guard(host: str, payload: dict, ok: bool, always: bool) -> int:
    active = always or marker_active()
    if not active:
        return respond_allow(host)
    if not ok:
        return respond_block(host, "payload do hook ilegível enquanto o verificador roda")
    reason = classify_tool_call(payload)
    return respond_block(host, reason) if reason else respond_allow(host)


def prune_old_sessions(max_age_days: int = 7) -> None:
    cutoff = time.time() - max_age_days * 86400
    for entry in (state_dir() / "sessions").glob("*"):
        try:
            if entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            pass


def cmd_session_start(host: str, payload: dict) -> int:
    prune_old_sessions()
    repo = payload_repo(payload, host)
    if repo is not None:
        fp = fingerprint(repo)
        if fp:
            baseline_path(session_key(payload), repo).write_text(
                json.dumps({"fingerprint": fp, "repo": str(repo), "created_at": time.time()}),
                encoding="utf-8",
            )
    if host == "cursor":
        print("{}")
    return 0


def cmd_track_edit(host: str, payload: dict) -> int:
    edits_flag_path(session_key(payload)).write_text(str(time.time()), encoding="utf-8")
    if host == "cursor":
        print("{}")
    return 0


def verify_command_hint() -> str:
    script = kit_home() / "verify.py"
    return f'"{sys.executable}" "{script}" --request-file <git-dir>/delpi-verifier/requests/<pedido>.md'


def gate_message(repo: Path, last: Optional[dict]) -> Optional[str]:
    hint = record_command_hint()
    verify_hint = verify_command_hint()
    if last is None:
        return (
            "[delpi-verifier] Há alterações neste repositório desde o início da sessão e nenhum veredito "
            "registrado para o estado atual. Antes de encerrar, grave o PEDIDO DE VERIFICAÇÃO em "
            f"<git-dir>/delpi-verifier/requests/ e rode: {verify_hint} "
            "(seção 'Verificação (delpi-verifier)' do AGENTS.md). Se esta alteração dispensa verificação "
            f"(ex.: só texto de documentação), registre a dispensa com: {hint} --verdict SKIPPED --round 0 "
            '--summary "<motivo>" e cite a dispensa no relatório final.'
        )
    verdict = str(last.get("verdict", ""))
    rnd = int(last.get("round", 0) or 0)
    if verdict in GATE_PASS_VERDICTS:
        return None
    if verdict == "REWORK" and rnd >= MAX_ROUNDS:
        return None
    return (
        f"[delpi-verifier] Último veredito para o estado atual: {verdict} (rodada {rnd}). Aplique as ordens de "
        f"correção no código de produção (ou conteste com evidência) e rode de novo o verify.py para a rodada "
        f"{rnd + 1}: {verify_hint}. Se houver DECISION_REQUIRED, pare e devolva a decisão ao usuário."
    )


def cmd_stop_gate(host: str, payload: dict) -> int:
    if os.environ.get("DELPI_VERIFIER_GATE", "").lower() in {"off", "0", "false"}:
        return _gate_pass(host)
    if host == "devin" and payload.get("stop_hook_active"):
        return _gate_pass(host)
    if host == "cursor" and int(payload.get("loop_count", 0) or 0) >= 2:
        return _gate_pass(host)
    if payload.get("status") in {"aborted", "error"}:
        return _gate_pass(host)
    if not edits_flag_path(session_key(payload)).exists():
        # Only sessions that edited files through a tool are gated. Changes made by other
        # agents working in the same tree must not nag this session.
        return _gate_pass(host)
    repo = payload_repo(payload, host)
    if repo is None or not has_contract(repo):
        return _gate_pass(host)
    baseline = read_json(baseline_path(session_key(payload), repo))
    if not baseline:
        return _gate_pass(host)
    fp = fingerprint(repo)
    if not fp or fp == baseline.get("fingerprint"):
        return _gate_pass(host)
    message = gate_message(repo, latest_verdict(repo, fp))
    if message is None:
        return _gate_pass(host)
    if host == "cursor":
        print(json.dumps({"followup_message": message}))
        return 0
    print(json.dumps({"decision": "block", "reason": message}))
    return 0


def _gate_pass(host: str) -> int:
    if host == "cursor":
        print("{}")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    verdict = args.verdict.upper()
    if verdict not in ALL_VERDICTS:
        sys.stderr.write(f"veredito inválido: {verdict}. Use um de: {', '.join(sorted(ALL_VERDICTS))}\n")
        return 1
    repo = repo_root(Path(args.repo or os.getcwd()))
    if repo is None:
        sys.stderr.write("não encontrei um repositório git a partir do diretório atual\n")
        return 1
    fp = fingerprint(repo)
    ledger = ledger_path(repo)
    if not fp or ledger is None:
        sys.stderr.write("não consegui calcular o fingerprint do repositório\n")
        return 1
    entry = {
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "verdict": verdict,
        "round": args.round,
        "summary": args.summary or "",
        "fingerprint": fp,
        "head": (run_git(repo, ["rev-parse", "HEAD"]) or "").strip(),
        "recorded_by": getattr(args, "recorded_by", None) or "verifier_hooks.py",
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"registrado: {verdict} rodada {args.round} @ {entry['head'][:10]} ({ledger})")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or os.getcwd()))
    info = {
        "kit_home": str(kit_home()),
        "marker_active": marker_active(),
        "marker": read_json(marker_path()),
        "repo": str(repo) if repo else None,
        "contract": has_contract(repo) if repo else False,
    }
    if repo:
        fp = fingerprint(repo)
        info["fingerprint"] = fp
        info["latest_verdict_for_state"] = latest_verdict(repo, fp) if fp else None
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("mark-start", "mark-stop", "guard", "session-start", "track-edit", "stop-gate"):
        p = sub.add_parser(name)
        p.add_argument("--host", choices=["cursor", "devin", "claude"], required=True)
        if name == "guard":
            p.add_argument("--always", action="store_true", help="guard sem depender do marcador (hook com escopo do subagent)")
    act = sub.add_parser("activate")
    act.add_argument("--host", default="verify", help="quem ativa o marcador (padrão: verify)")
    rec = sub.add_parser("record")
    rec.add_argument("--verdict", required=True)
    rec.add_argument("--recorded-by", default=None, help="origem do registro (ex.: verify.py)")
    rec.add_argument("--round", type=int, default=1)
    rec.add_argument("--summary", default="")
    rec.add_argument("--repo")
    st = sub.add_parser("status")
    st.add_argument("--repo")
    sub.add_parser("clear")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "record":
        return cmd_record(args)
    if args.command == "status":
        return cmd_status(args)
    if args.command == "clear":
        clear_marker()
        print("marcador removido")
        return 0
    if args.command == "activate":
        set_marker(getattr(args, "host", "verify") or "verify", {"session_id": "verify.py"})
        print("marcador ativo")
        return 0
    payload, ok = read_payload()
    try:
        if args.command == "mark-start":
            return cmd_mark_start(args.host, payload)
        if args.command == "mark-stop":
            return cmd_mark_stop(args.host, payload)
        if args.command == "guard":
            return cmd_guard(args.host, payload, ok, args.always)
        if args.command == "session-start":
            return cmd_session_start(args.host, payload)
        if args.command == "track-edit":
            return cmd_track_edit(args.host, payload)
        if args.command == "stop-gate":
            return cmd_stop_gate(args.host, payload)
    except Exception as exc:  # noqa: BLE001 — a crashing hook must not wedge the agent
        if args.command == "guard" and (args.always or marker_active()):
            return respond_block(args.host, f"erro interno do guard ({type(exc).__name__})")
        sys.stderr.write(f"[delpi-verifier] hook {args.command} falhou: {exc}\n")
        if args.host == "cursor":
            print("{}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
