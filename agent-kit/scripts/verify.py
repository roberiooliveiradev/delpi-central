#!/usr/bin/env python3
"""Launch an independent headless verification session (delpi-verifier 0.2+).

Usage:
  python ~/.delpi-agent-kit/verify.py --request-file <pedido.md> [--repo <path>]
                                      [--engine auto|devin|cursor]

Stdlib only. Python 3.8+. Identifiers in English; user-facing messages in PT-BR.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VERDICT_RE = re.compile(
    r"(?im)^\s*veredito\s*:\s*(ACCEPT_WITH_RESIDUAL|ACCEPT|REWORK|INCONCLUSIVE|EXECUTION_DRIFT|SKIPPED)\b"
)
RQ_OR_AC_RE = re.compile(r"\b(?:RQ|AC)-\d+\b", re.IGNORECASE)
FIELD_RE = re.compile(
    r"(?im)^(objetivo|escopo|repositorio|alegacoes|alegações|modelo_executor|rodada|ordens_anteriores)\s*:\s*(.*)$"
)
DEFAULT_TIMEOUT_SEC = 30 * 60
DEFAULT_ENGINE_ORDER = ["devin", "cursor"]
DEFAULT_MODELS = {"devin": "swe-2-high", "cursor": "composer-2.5"}
DEFAULT_DEVIN_PERMISSION_MODE = "smart"
DIFF_STAT_MAX_LINES = 200

# normalize_agent_path lives in verifier_hooks (installed beside this file; source in hooks/).
_SCRIPT_DIR = Path(__file__).resolve().parent
for _candidate in (_SCRIPT_DIR, _SCRIPT_DIR.parent / "hooks"):
    if _candidate.is_dir() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
from verifier_hooks import normalize_agent_path  # noqa: E402


def kit_home() -> Path:
    override = os.environ.get("DELPI_AGENT_KIT_HOME")
    if override:
        return Path(override)
    return Path.home() / ".delpi-agent-kit"


def load_install() -> dict:
    path = kit_home() / "install.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def run_git(repo: Path, args: List[str]) -> Optional[str]:
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


def verifier_dir(repo: Path) -> Optional[Path]:
    gdir = git_dir(repo)
    if gdir is None:
        return None
    path = gdir / "delpi-verifier"
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_request(text: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    current: Optional[str] = None
    buffer: List[str] = []
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if match:
            if current is not None:
                fields[current] = "\n".join(buffer).strip()
            key = match.group(1).lower().replace("ç", "c").replace("ã", "a")
            if key == "alegacoes":
                key = "alegacoes"
            current = key
            buffer = [match.group(2)]
        elif current is not None:
            buffer.append(line)
    if current is not None:
        fields[current] = "\n".join(buffer).strip()
    # Normalize accented key if present
    if "alegacoes" not in fields and "alegações" in fields:
        fields["alegacoes"] = fields["alegações"]
    return fields


def validate_request(fields: Dict[str, str], repo: Path) -> List[str]:
    missing: List[str] = []
    objetivo = fields.get("objetivo", "").strip()
    if not objetivo:
        missing.append("objetivo")
    elif not RQ_OR_AC_RE.search(objetivo):
        missing.append("objetivo (precisa conter ao menos um AC-* ou RQ-*)")

    escopo = fields.get("escopo", "").strip()
    if not escopo:
        missing.append("escopo")
    else:
        if escopo.lower() == "working tree":
            status = run_git(repo, ["status", "--porcelain"])
            if status is None:
                missing.append("escopo (não consegui ler git status)")
            elif not status.strip():
                missing.append("escopo (working tree sem alterações reais)")
        elif ".." in escopo:
            base, _, head = escopo.partition("..")
            base, head = base.strip(), head.strip()
            if not base or not head:
                missing.append("escopo (base..head incompleto)")
            else:
                ok = run_git(repo, ["rev-parse", "--verify", f"{base}^{{commit}}"])
                ok2 = run_git(repo, ["rev-parse", "--verify", f"{head}^{{commit}}"])
                if ok is None or ok2 is None:
                    missing.append(f"escopo (base..head inválido no repo: {escopo})")
        else:
            missing.append('escopo (use "working tree" ou base..head)')

    if not fields.get("alegacoes", "").strip():
        missing.append("alegacoes")
    if not fields.get("modelo_executor", "").strip():
        missing.append("modelo_executor")

    rodada_raw = fields.get("rodada", "").strip()
    if not rodada_raw:
        missing.append("rodada")
    else:
        try:
            rodada = int(rodada_raw.split()[0])
        except ValueError:
            missing.append("rodada (deve ser 1, 2 ou 3)")
            rodada = 0
        if rodada not in (1, 2, 3):
            missing.append("rodada (deve ser 1, 2 ou 3)")
        elif rodada >= 2 and not fields.get("ordens_anteriores", "").strip():
            missing.append("ordens_anteriores (obrigatório quando rodada >= 2)")
    return missing


def find_contract(repo: Path) -> Optional[Path]:
    for candidate in (repo / "AGENTS.md", repo / "agents.md"):
        if candidate.exists():
            return candidate
    return None


def truncate_diff_stat(text: str, max_lines: int = DIFF_STAT_MAX_LINES) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    omitted = len(lines) - max_lines
    return "\n".join(lines[:max_lines]) + f"\n… {omitted} arquivos omitidos"


def diff_stat(repo: Path, escopo: str) -> str:
    if escopo.lower() == "working tree":
        out = run_git(repo, ["diff", "--stat", "HEAD"])
        untracked = run_git(repo, ["status", "--short"])
        parts = [p for p in (out, untracked) if p and p.strip()]
        raw = "\n".join(parts) if parts else "(sem diff)"
    else:
        out = run_git(repo, ["diff", "--stat", escopo])
        raw = out.strip() if out else "(sem diff)"
    return truncate_diff_stat(raw)


REPORT_FORMAT_HEADING = "## Formato do relatório"
ACCEPTED_VERDICTS_LINE = (
    "ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE"
)
VERDICT_FORMAT_FOOTER = (
    f"Vereditos aceitos: {ACCEPTED_VERDICTS_LINE}.\n"
    "PASS/FAIL são status de item, nunca veredito."
)
RETRY_FORMAT_REMINDER = (
    "\n\n## Lembrete de formato (2ª tentativa)\n\n"
    "A saída anterior não tinha uma linha `veredito:` com valor válido.\n"
    f"Use exatamente uma linha `veredito: <VALOR>` com um de: {ACCEPTED_VERDICTS_LINE}.\n"
    "PASS/FAIL são status de item, nunca veredito.\n"
)


def render_headless_protocol() -> str:
    """Prefer installed headless protocol; fall back to source tree.

    ``protocol.headless.md`` (from install/build) already embeds report-format.md.
    Append report-format only when the loaded text lacks that section — once.
    """
    kit_root = Path(__file__).resolve().parents[1]
    candidates = [
        kit_home() / "protocol.headless.md",
        kit_root / "verifier" / "protocol.headless.md",
        kit_root / "verifier" / "protocol.md",
    ]
    report_candidates = [
        kit_home() / "report-format.md",
        kit_root / "verifier" / "report-format.md",
    ]
    protocol_text = None
    for candidate in candidates:
        if candidate.exists():
            protocol_text = candidate.read_text(encoding="utf-8")
            break
    if protocol_text is None:
        protocol_text = "(protocolo não encontrado — instale o kit)"
    report_text = ""
    for candidate in report_candidates:
        if candidate.exists():
            report_text = candidate.read_text(encoding="utf-8")
            break
    # Strip YAML frontmatter if present
    if protocol_text.startswith("---"):
        parts = protocol_text.split("---", 2)
        if len(parts) == 3:
            protocol_text = parts[2].lstrip("\n")
    body = protocol_text.rstrip()
    if report_text and REPORT_FORMAT_HEADING not in body:
        body += "\n\n---\n\n" + report_text.rstrip()
    version = "0.3.1"
    ver_path = kit_home() / "VERSION"
    if ver_path.exists():
        version = ver_path.read_text(encoding="utf-8").strip() or version
    return (
        body.replace("{{KIT_VERSION}}", version)
        .replace("{{PLATFORM}}", "headless")
        .replace("{{RECORD_CMD}}", f'"{sys.executable}" "{kit_home() / "verifier_hooks.py"}" record')
        .replace("{{GUARD_ALWAYS_CMD}}", "")
    )


def which_engine(name: str, install: dict) -> Optional[str]:
    paths = (install.get("paths") or {}) if isinstance(install.get("paths"), dict) else {}
    configured = paths.get(f"{name}_bin") or paths.get(name)
    if configured and Path(str(configured)).exists():
        return str(configured)
    # Common names
    names = {"devin": ["devin"], "cursor": ["agent", "cursor-agent"]}
    for candidate in names.get(name, [name]):
        found = shutil.which(candidate)
        if found:
            return found
    return None


def engine_available(name: str, install: dict) -> bool:
    return which_engine(name, install) is not None


def choose_engine(forced: str, install: dict) -> Optional[str]:
    order = install.get("engines") or DEFAULT_ENGINE_ORDER
    if not isinstance(order, list):
        order = DEFAULT_ENGINE_ORDER
    if forced != "auto":
        return forced if engine_available(forced, install) else None
    for name in order:
        if name in ("devin", "cursor") and engine_available(name, install):
            return name
    return None


def model_for(engine: str, install: dict) -> str:
    models = install.get("models") if isinstance(install.get("models"), dict) else {}
    return str(models.get(engine) or DEFAULT_MODELS.get(engine) or "")


def build_prompt(fields: Dict[str, str], repo: Path, request_text: str) -> str:
    contract = find_contract(repo)
    escopo = fields.get("escopo", "").strip()
    parts = [
        render_headless_protocol(),
        "",
        "## Pedido de verificação (já validado pelo verify.py)",
        "",
        request_text.strip(),
        "",
        "## Contrato do projeto",
        f"Leia o contrato em: {contract}" if contract else "AGENTS.md não encontrado — use só o protocolo.",
        "",
        "## Diff do escopo (`git diff --stat`)",
        "```",
        diff_stat(repo, escopo),
        "```",
        "",
        f"Trabalhe no repositório: {repo}",
        "Ao final, emita o relatório no formato fixo, com a linha `veredito:`.",
        VERDICT_FORMAT_FOOTER,
    ]
    return "\n".join(parts)


def launch_devin(binary: str, repo: Path, prompt_file: Path, model: str, install: dict, timeout: int) -> Tuple[int, str]:
    permission = (
        (install.get("devin") or {}).get("permission_mode")
        if isinstance(install.get("devin"), dict)
        else None
    ) or DEFAULT_DEVIN_PERMISSION_MODE
    # `devin -p` está indisponível (gate standalone quebrado nestas builds); o caminho suportado é `devin acp`.
    try:
        return launch_devin_acp(binary, repo, prompt_file, model, permission, timeout)
    except Exception as exc:
        return 1, f"[verify.py] falha ao lançar motor (devin acp: {type(exc).__name__}: {exc})"


def _devin_credentials() -> Optional[Dict[str, str]]:
    path = Path.home() / ".local" / "share" / "devin" / "credentials.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    def field(name: str) -> Optional[str]:
        match = re.search(rf"^{name}\s*=\s*[\"'](.+?)[\"']\s*$", text, re.M)
        return match.group(1) if match else None

    api_key = field("windsurf_api_key") or field("api_key")
    if not api_key:
        return None
    return {
        "api_key": api_key,
        "api_server_url": field("api_server_url") or "https://server.codeium.com",
    }


def _acp_send(proc: subprocess.Popen, obj: dict) -> None:
    assert proc.stdin is not None
    proc.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
    proc.stdin.flush()


def _acp_read(proc: subprocess.Popen, buf: bytearray, deadline: float) -> Optional[dict]:
    assert proc.stdout is not None
    while True:
        nl = buf.find(b"\n")
        if nl >= 0:
            line = bytes(buf[:nl])
            del buf[: nl + 1]
            try:
                msg = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if isinstance(msg, dict):
                return msg
            continue
        remaining = deadline - time.time()
        if remaining <= 0 or proc.poll() is not None:
            return None
        ready, _, _ = select.select([proc.stdout], [], [], min(remaining, 5.0))
        if not ready:
            continue
        chunk = os.read(proc.stdout.fileno(), 65536)
        if not chunk:
            return None
        buf += chunk


def _acp_handle_incoming(proc: subprocess.Popen, msg: dict, sink: List[str]) -> None:
    method = msg.get("method")
    if method == "session/request_permission" and msg.get("id") is not None:
        options = (msg.get("params") or {}).get("options") or []
        pick = next(
            (o for o in options if "allow" in str(o.get("optionId", "")).lower()),
            options[0] if options else {},
        )
        try:
            _acp_send(
                proc,
                {
                    "jsonrpc": "2.0",
                    "id": msg["id"],
                    "result": {
                        "outcome": {"outcome": "selected", "optionId": pick.get("optionId", "allow")}
                    },
                },
            )
        except (OSError, ValueError):
            pass
        return
    if method == "session/update":
        update = (msg.get("params") or {}).get("update") or {}
        kind = update.get("sessionUpdate")
        if kind == "agent_message_chunk":
            sink.append(str((update.get("content") or {}).get("text") or ""))
        elif kind == "tool_call":
            sink.append(f"\n[tool] {update.get('title', '')}\n")


def _acp_call(
    proc: subprocess.Popen,
    req_id: int,
    method: str,
    params: dict,
    deadline: float,
    sink: List[str],
    buf: bytearray,
) -> Tuple[Optional[dict], Optional[str]]:
    _acp_send(proc, {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
    while True:
        msg = _acp_read(proc, buf, deadline)
        if msg is None:
            return None, f"[verify.py] devin acp sem resposta em `{method}`"
        if msg.get("id") == req_id and ("result" in msg or "error" in msg):
            error = msg.get("error")
            if error:
                detail = error.get("message", error) if isinstance(error, dict) else error
                return None, f"[verify.py] devin acp `{method}` falhou: {detail}"
            return msg.get("result") or {}, None
        _acp_handle_incoming(proc, msg, sink)


def launch_devin_acp(
    binary: str,
    repo: Path,
    prompt_file: Path,
    model: str,
    permission: str,
    timeout: int,
) -> Tuple[int, str]:
    creds = _devin_credentials()
    if creds is None:
        return 1, "[verify.py] falha ao lançar motor (devin acp: credenciais ausentes em ~/.local/share/devin/credentials.toml)"
    env = os.environ.copy()
    env["DELPI_VERIFIER_ACTIVE"] = "1"
    cmd = [binary, "acp"] + (["--model", model] if model else [])
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(repo),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )
    except OSError as exc:
        return 1, f"[verify.py] falha ao lançar motor (devin acp: {type(exc).__name__}: {exc})"
    deadline = time.time() + timeout
    sink: List[str] = []
    buf = bytearray()
    session: Optional[dict] = None
    mode = {
        "auto": "accept-edits",
        "accept-edits": "accept-edits",
        "smart": "smart",
        "dangerous": "bypass",
    }.get(str(permission), "smart")
    try:
        _, err = _acp_call(
            proc,
            1,
            "initialize",
            {"protocolVersion": 1, "clientCapabilities": {}},
            deadline,
            sink,
            buf,
        )
        if err is None:
            _acp_send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            _, err = _acp_call(
                proc,
                2,
                "authenticate",
                {
                    "methodId": "windsurf-api-key",
                    "_meta": {
                        "api_key": creds["api_key"],
                        "api_server_url": creds["api_server_url"],
                    },
                },
                deadline,
                sink,
                buf,
            )
        if err is None:
            session, err = _acp_call(
                proc,
                3,
                "session/new",
                {"cwd": str(repo), "mcpServers": []},
                deadline,
                sink,
                buf,
            )
        if err is None:
            session_id = (session or {}).get("sessionId")
            if not session_id:
                err = "[verify.py] devin acp `session/new` sem sessionId"
            else:
                _acp_call(
                    proc,
                    4,
                    "session/set_mode",
                    {"sessionId": session_id, "modeId": mode},
                    deadline,
                    sink,
                    buf,
                )
                prompt = prompt_file.read_text(encoding="utf-8", errors="replace")
                _, err = _acp_call(
                    proc,
                    5,
                    "session/prompt",
                    {
                        "sessionId": session_id,
                        "prompt": [{"type": "text", "text": prompt}],
                    },
                    deadline,
                    sink,
                    buf,
                )
    finally:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass
    text = "".join(sink).strip()
    if err is None:
        return 0, text
    if time.time() >= deadline:
        return 124, text + "\n\n[verify.py] timeout\n"
    return 1, err + (("\n\n" + text) if text else "")


def launch_cursor(binary: str, repo: Path, prompt_file: Path, model: str, timeout: int) -> Tuple[int, str]:
    prompt = prompt_file.read_text(encoding="utf-8")
    cmd = [
        binary,
        "-p",
        "--trust",
        "--force",
        "--model",
        model,
        "--workspace",
        str(repo),
        "--output-format",
        "text",
        prompt,
    ]
    return run_engine(cmd, repo, timeout)


def run_engine(cmd: List[str], repo: Path, timeout: int) -> Tuple[int, str]:
    env = os.environ.copy()
    env["DELPI_VERIFIER_ACTIVE"] = "1"
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"").decode("utf-8", errors="replace")
        err = (exc.stderr or b"").decode("utf-8", errors="replace")
        return 124, out + (("\n" + err) if err else "") + "\n\n[verify.py] timeout\n"
    except OSError as exc:
        return 1, f"[verify.py] falha ao lançar motor ({type(exc).__name__}: {exc})"
    out = result.stdout.decode("utf-8", errors="replace")
    err = result.stderr.decode("utf-8", errors="replace")
    combined = out
    if err.strip():
        combined = out + (("\n" if out and not out.endswith("\n") else "") + err)
    return result.returncode, combined


def extract_verdict(report: str) -> Optional[str]:
    matches = list(VERDICT_RE.finditer(report))
    if not matches:
        return None
    return matches[-1].group(1).upper()


def ensure_ledger(repo: Path, verdict: str, rodada: int, summary: str, force: bool = False) -> None:
    hooks = kit_home() / "verifier_hooks.py"
    if not hooks.exists():
        return
    if not force:
        status = subprocess.run(
            [sys.executable, str(hooks), "status", "--repo", str(repo)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        try:
            info = json.loads(status.stdout or "{}")
        except json.JSONDecodeError:
            info = {}
        if info.get("latest_verdict_for_state"):
            return
    subprocess.run(
        [
            sys.executable,
            str(hooks),
            "record",
            "--verdict",
            verdict,
            "--round",
            str(rodada),
            "--summary",
            summary,
            "--repo",
            str(repo),
            "--recorded-by",
            "verify.py",
        ],
        capture_output=True,
        timeout=60,
        check=False,
    )


def write_inconclusive(
    repo: Path,
    reason: str,
    raw: str,
    engine: str,
    model: str,
    rodada: int,
    *,
    attempts: int = 1,
) -> Path:
    vdir = verifier_dir(repo)
    assert vdir is not None
    reports = vdir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = reports / f"{stamp}-r{rodada}-{engine or 'none'}.md"
    attempts_line = f"tentativas: {attempts}\n\n" if attempts > 1 else ""
    body = (
        f"# Relatório do delpi-verifier\n\n"
        f"motor: {engine or 'none'} · modelo: {model or 'n/a'}\n\n"
        f"{attempts_line}"
        f"veredito: INCONCLUSIVE\n\n"
        f"motivo: {reason}\n\n"
        f"## Saída bruta\n\n```\n{raw}\n```\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def save_report(
    repo: Path,
    text: str,
    engine: str,
    model: str,
    rodada: int,
    *,
    attempts: int = 1,
) -> Path:
    vdir = verifier_dir(repo)
    assert vdir is not None
    reports = vdir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = reports / f"{stamp}-r{rodada}-{engine}.md"
    header = f"motor: {engine} · modelo: {model}\n"
    if attempts > 1:
        header += f"tentativas: {attempts}\n"
    if not text.lstrip().startswith("motor:"):
        # Insert header after first markdown title if present
        lines = text.splitlines()
        if lines and lines[0].startswith("#"):
            text = lines[0] + "\n\n" + header + "\n" + "\n".join(lines[1:])
        else:
            text = header + "\n" + text
    elif attempts > 1 and "tentativas:" not in text[:400]:
        # Ensure tentativas is visible near the motor header
        text = text.replace(header.rstrip("\n"), header.rstrip("\n"), 1)
        lines = text.splitlines()
        inserted = False
        out_lines = []
        for line in lines:
            out_lines.append(line)
            if not inserted and line.startswith("motor:"):
                out_lines.append(f"tentativas: {attempts}")
                inserted = True
        text = "\n".join(out_lines)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return path


def run_verify(args: argparse.Namespace) -> int:
    install = load_install()
    # Isolation is DELPI_VERIFIER_ACTIVE in the child env only — no global marker file.
    repo = normalize_agent_path(args.repo).resolve() if args.repo else Path.cwd().resolve()
    root = repo_root(repo)
    if root is None:
        sys.stderr.write(f"não encontrei repositório git em {repo}\n")
        return 2
    repo = root

    request_path = normalize_agent_path(args.request_file).resolve()
    if not request_path.exists():
        sys.stderr.write(f"pedido não encontrado: {request_path}\n")
        return 2
    request_text = request_path.read_text(encoding="utf-8", errors="replace")
    fields = parse_request(request_text)
    # Optional repositorio field overrides
    if fields.get("repositorio"):
        alt = normalize_agent_path(fields["repositorio"]).expanduser().resolve()
        alt_root = repo_root(alt)
        if alt_root is None:
            sys.stderr.write(f"repositorio do pedido inválido: {fields['repositorio']}\n")
            return 2
        repo = alt_root

    missing = validate_request(fields, repo)
    if missing:
        sys.stderr.write("Pedido de verificação incompleto. Falta:\n")
        for item in missing:
            sys.stderr.write(f"  - {item}\n")
        return 2

    rodada = int(fields["rodada"].split()[0])
    timeout = int(args.timeout or install.get("timeout_sec") or DEFAULT_TIMEOUT_SEC)

    engine = choose_engine(args.engine, install)
    if engine is None:
        path = write_inconclusive(
            repo,
            "verificador indisponível",
            "Nenhum motor headless disponível (devin/agent).",
            "none",
            "",
            rodada,
        )
        ensure_ledger(repo, "INCONCLUSIVE", rodada, "verificador indisponível", force=True)
        sys.stdout.write(path.read_text(encoding="utf-8"))
        return 3

    model = model_for(engine, install)
    binary = which_engine(engine, install)
    assert binary is not None

    base_prompt = build_prompt(fields, repo, request_text)
    code = 0
    raw = ""
    verdict: Optional[str] = None
    attempts = 0
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        prompt = base_prompt if attempt == 1 else (base_prompt + RETRY_FORMAT_REMINDER)
        prompt_file = Path(tempfile.mkstemp(prefix="delpi-verify-", suffix=".md")[1])
        prompt_file.write_text(prompt, encoding="utf-8")
        try:
            if engine == "devin":
                code, raw = launch_devin(binary, repo, prompt_file, model, install, timeout)
            else:
                code, raw = launch_cursor(binary, repo, prompt_file, model, timeout)
        finally:
            try:
                prompt_file.unlink()
            except OSError:
                pass

        if raw.startswith("[verify.py] falha ao lançar motor"):
            report_path = write_inconclusive(
                repo, "falha ao lançar motor", raw, engine, model, rodada, attempts=attempts
            )
            ensure_ledger(repo, "INCONCLUSIVE", rodada, "falha ao lançar motor")
            sys.stdout.write(report_path.read_text(encoding="utf-8"))
            return 1

        verdict = extract_verdict(raw)
        if verdict is not None:
            break
        # Invalid format: one retry with the same engine and a short reminder.
        if attempt < max_attempts:
            continue

    if verdict is None:
        report_path = write_inconclusive(
            repo,
            "relatório fora do formato (2 tentativas)",
            raw,
            engine,
            model,
            rodada,
            attempts=attempts,
        )
        ensure_ledger(repo, "INCONCLUSIVE", rodada, "relatório fora do formato (2 tentativas)")
        sys.stdout.write(report_path.read_text(encoding="utf-8"))
        return 0 if code == 0 else 1

    report_path = save_report(repo, raw, engine, model, rodada, attempts=attempts)
    ensure_ledger(repo, verdict, rodada, f"veredito lido do relatório ({engine})")
    sys.stdout.write(report_path.read_text(encoding="utf-8"))
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--request-file", required=True, help="caminho do PEDIDO DE VERIFICAÇÃO")
    parser.add_argument("--repo", default=None, help="raiz do repositório (padrão: cwd)")
    parser.add_argument("--engine", default="auto", choices=["auto", "devin", "cursor"])
    parser.add_argument("--timeout", type=int, default=None, help="timeout em segundos (padrão: install.json ou 1800)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    return run_verify(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
