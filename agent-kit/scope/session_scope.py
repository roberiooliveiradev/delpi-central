#!/usr/bin/env python3
"""agent-scope — leases de escopo por sessão para agentes concorrentes.

Modelo híbrido:
  * ownership fixo:  agent-scope.json + agent-kit/scope/contexts.json (versionados)
  * lease de sessão: <git-common-dir>/agent-scope/sessions/<id>.json (local,
                     compartilhado por todos os worktrees do repositório)

Comandos:
  register      registra o lease da sessão (contextos + globs extras)
  release       encerra o lease de uma sessão
  expire        remove leases vencidos
  status        lista leases ativos
  check         classifica arquivos sujos/staged do worktree contra o lease
  pre-commit    modo hook: bloqueia commit fora do escopo ou em escopo alheio
  audit         audita todos os worktrees (sentinela): violações + sobreposições
  install-hook  instala o wrapper pre-commit em <git-common-dir>/hooks/
  uninstall-hook

O recurso só atua quando <repo>/agent-scope.json existe (opt-in por repo,
equivalente ao marcador delpi-verifier:contract do AGENTS.md). Sem o arquivo,
`pre-commit` sai 0 e nada é bloqueado.

Somente stdlib; Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

CONFIG_NAME = "agent-scope.json"
DEFAULT_CONTEXTS_FILE = "agent-kit/scope/contexts.json"
HOOK_MARKER = "agent-scope pre-commit"


# ---------------------------------------------------------------------------
# git / repo plumbing
# ---------------------------------------------------------------------------

def run_git(repo: Path, args: Sequence[str]) -> Optional[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def repo_root(start: Path) -> Optional[Path]:
    out = run_git(start, ["rev-parse", "--show-toplevel"])
    return Path(out.strip()) if out else None


def common_git_dir(repo: Path) -> Optional[Path]:
    out = run_git(repo, ["rev-parse", "--git-common-dir"])
    if not out:
        return None
    path = Path(out.strip())
    return path if path.is_absolute() else (repo / path).resolve()


def sessions_dir(repo: Path) -> Optional[Path]:
    common = common_git_dir(repo)
    return (common / "agent-scope" / "sessions") if common else None


def current_branch(repo: Path) -> str:
    out = run_git(repo, ["branch", "--show-current"])
    return out.strip() if out else "(detached)"


# ---------------------------------------------------------------------------
# config / contexts
# ---------------------------------------------------------------------------

def load_config(repo: Path) -> Optional[dict]:
    """Política do agent-scope.

    Ordem: <worktree>/agent-scope.json (versionada, canônica) →
    <git-common-dir>/agent-scope/config.json (semente local, cobre branches
    antigas que ainda não contêm o arquivo versionado) → None (feature off).
    """
    raw: Optional[str] = None
    path = repo / CONFIG_NAME
    if path.is_file():
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            raw = None
    else:
        # Só cai no fallback quando a história da branch nunca conheceu
        # o arquivo (branch antiga). Arquivo que existiu e foi removido
        # (worktree ou commit) = remoção intencional → feature off.
        known_in_history = bool(
            (run_git(repo, ["log", "-1", "--format=%H", "--", CONFIG_NAME]) or "").strip()
        )
        if not known_in_history:
            common = common_git_dir(repo)
            fallback = (common / "agent-scope" / "config.json") if common else None
            if fallback and fallback.is_file():
                try:
                    raw = fallback.read_text(encoding="utf-8")
                except OSError:
                    raw = None
    if raw is None:
        return None
    try:
        cfg = json.loads(raw)
    except ValueError:
        return None
    cfg.setdefault("require_lease", True)
    cfg.setdefault("overlap", "block")
    cfg.setdefault("lease_ttl_hours", 12)
    cfg.setdefault("contexts_file", DEFAULT_CONTEXTS_FILE)
    return cfg


def load_contexts(repo: Path, cfg: Optional[dict]) -> Dict[str, dict]:
    """Contextos: <worktree>/<contexts_file> (canônico) →
    <git-common-dir>/agent-scope/contexts.json (fallback local) → {}."""
    name = (cfg or {}).get("contexts_file", DEFAULT_CONTEXTS_FILE)
    candidates = [repo / name]
    common = common_git_dir(repo)
    if common:
        candidates.append(common / "agent-scope" / "contexts.json")
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        return data.get("contexts", {})
    return {}


# ---------------------------------------------------------------------------
# glob matching (gitignore-style: * não cruza '/', ** cruza)
# ---------------------------------------------------------------------------

def glob_to_regex(pattern: str) -> re.Pattern:
    pattern = pattern.strip().lstrip("/")
    out, i = [], 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*":
            if pattern[i:i + 2] == "**":
                if pattern[i:i + 3] == "**/":
                    out.append("(?:.*/)?")
                    i += 3
                else:
                    out.append(".*")
                    i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif ch == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(ch))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def compile_globs(globs: Iterable[str]) -> List[re.Pattern]:
    return [glob_to_regex(g) for g in globs]


def match_any(path: str, compiled: Sequence[re.Pattern]) -> bool:
    return any(rx.match(path) for rx in compiled)


def globs_overlap(g1: str, g2: str) -> bool:
    """Heurística: dois globs podem cobrir arquivos em comum?"""
    if g1 == g2:
        return True

    def prefix(g: str) -> str:
        base = re.split(r"[*?]", g, maxsplit=1)[0]
        return base.rstrip("/")

    p1, p2 = prefix(g1), prefix(g2)
    if not p1 or not p2:
        return True
    return p1 == p2 or p1.startswith(p2 + "/") or p2.startswith(p1 + "/")


# ---------------------------------------------------------------------------
# leases
# ---------------------------------------------------------------------------

def lease_path(repo: Path, session: str) -> Optional[Path]:
    directory = sessions_dir(repo)
    if directory is None:
        return None
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", session).strip("-.") or "session"
    return directory / f"{safe}.json"


def load_lease(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def iter_leases(repo: Path) -> List[Tuple[Path, dict]]:
    directory = sessions_dir(repo)
    if directory is None or not directory.is_dir():
        return []
    found = []
    for path in sorted(directory.glob("*.json")):
        lease = load_lease(path)
        if lease:
            found.append((path, lease))
    return found


def lease_expired(lease: dict, now: Optional[float] = None) -> bool:
    exp = lease.get("expires")
    return bool(exp) and (now or time.time()) >= float(exp)


def find_lease(repo: Path, worktree: Path, session: Optional[str]) -> Optional[dict]:
    """Resolve o lease da sessão: env AGENT_SESSION > worktree mais recente ativo."""
    now = time.time()
    candidates = [l for _, l in iter_leases(repo) if not lease_expired(l, now)]
    wanted = session or os.environ.get("AGENT_SESSION")
    if wanted:
        for lease in candidates:
            if lease.get("session") == wanted:
                return lease
        return None
    same = [l for l in candidates if l.get("worktree") == str(worktree)]
    if not same:
        return None
    same.sort(key=lambda l: float(l.get("created", 0)), reverse=True)
    return same[0]


def active_leases(repo: Path, exclude: Optional[str] = None) -> List[dict]:
    now = time.time()
    return [
        l for _, l in iter_leases(repo)
        if not lease_expired(l, now) and l.get("session") != exclude
    ]


# ---------------------------------------------------------------------------
# file classification
# ---------------------------------------------------------------------------

def staged_files(repo: Path) -> List[str]:
    out = run_git(repo, ["diff", "--cached", "--name-only", "-z"])
    if out is None:
        return []
    return [p for p in out.split("\0") if p]


def dirty_files(repo: Path) -> List[str]:
    # -uall: expande dirs não rastreados em arquivos — classificação por arquivo.
    out = run_git(repo, ["status", "--porcelain", "-z", "-uall"])
    if out is None:
        return []
    files, fields = [], out.split("\0")
    i = 0
    while i < len(fields):
        field = fields[i]
        i += 1
        if not field:
            continue
        status, path = field[:2], field[3:]
        if status and status[0] in {"R", "C"}:
            i += 1  # renomeado: consome o path original
        if path:
            files.append(path)
    return files


def diff_files(repo: Path, base: str) -> List[str]:
    out = run_git(repo, ["diff", "--name-only", f"{base}...HEAD"])
    if out is None:
        return []
    return [p for p in out.splitlines() if p]


def classify_file(
    path: str,
    mine: Sequence[re.Pattern],
    others: List[Tuple[str, List[re.Pattern]]],
) -> Tuple[str, Optional[str]]:
    """Retorna (veredito, sessão_dona): ok | foreign_scope | out_of_scope."""
    if match_any(path, mine):
        return "ok", None
    for session, compiled in others:
        if match_any(path, compiled):
            return "foreign_scope", session
    return "out_of_scope", None


def classify_files(
    files: Sequence[str], repo: Path, my_lease: Optional[dict],
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Retorna (out_of_scope, [(file, owner_session)])."""
    mine = compile_globs((my_lease or {}).get("globs", []))
    others = [
        (l.get("session", "?"), compile_globs(l.get("globs", [])))
        for l in active_leases(repo, exclude=(my_lease or {}).get("session"))
    ]
    out_of_scope, foreign = [], []
    for path in files:
        verdict, owner = classify_file(path, mine, others)
        if verdict == "foreign_scope":
            foreign.append((path, owner or "?"))
        elif verdict == "out_of_scope":
            out_of_scope.append(path)
    return out_of_scope, foreign


# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------

def print_block_header(title: str) -> None:
    print(f"\n[agent-scope] {title}", file=sys.stderr)


def register_hint(repo: Path) -> str:
    script = script_path(repo)
    return (
        f"  {sys.executable} {script} register --session <id> "
        f"--context <ctx> [--path <glob>]"
    )


def script_path(repo: Path) -> str:
    """Caminho deste script relativo ao repo, se for o caso."""
    try:
        me = Path(__file__).resolve()
        return str(me.relative_to(repo))
    except (OSError, ValueError):
        return str(Path(__file__).resolve())


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_register(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or os.getcwd()))
    if repo is None:
        print("[agent-scope] fora de um repositório git", file=sys.stderr)
        return 2
    cfg = load_config(repo) or {}
    contexts = load_contexts(repo, cfg)
    wt_raw = args.worktree or (run_git(repo, ["rev-parse", "--show-toplevel"]) or "").strip()
    worktree = Path(wt_raw or repo).resolve()

    globs: List[str] = list(args.path or [])
    chosen_contexts: List[str] = []
    unknown = [c for c in (args.context or []) if c not in contexts]
    if unknown:
        print(f"[agent-scope] contexto(s) desconhecido(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"  disponíveis: {', '.join(sorted(contexts)) or '(contexts.json vazio)'}", file=sys.stderr)
        return 2
    restricted = [
        c for c in (args.context or [])
        if contexts.get(c, {}).get("restricted") and not args.allow_restricted
    ]
    if restricted:
        print(
            f"[agent-scope] contexto(s) restrito(s) exigem --allow-restricted: "
            f"{', '.join(restricted)}",
            file=sys.stderr,
        )
        return 2
    for ctx in args.context or []:
        globs.extend(contexts[ctx].get("globs", []))
        chosen_contexts.append(ctx)
    if not args.allow_restricted:
        restricted_globs = [
            g for c in contexts.values() if c.get("restricted")
            for g in c.get("globs", [])
        ]
        hits = [
            g for g in globs
            if any(globs_overlap(g, rg) for rg in restricted_globs)
        ]
        if hits:
            print(
                f"[agent-scope] escopo toca zona(s) restrita(s), exige --allow-restricted: "
                f"{', '.join(hits[:5])}",
                file=sys.stderr,
            )
            return 2
    if not globs:
        print("[agent-scope] escopo vazio: informe --context e/ou --path", file=sys.stderr)
        return 2

    session = args.session or os.environ.get("AGENT_SESSION") or worktree.name
    ttl_hours = float(args.ttl if args.ttl is not None else cfg.get("lease_ttl_hours", 12))
    now = time.time()
    lease = {
        "session": session,
        "agent": args.agent or os.environ.get("AGENT_KIND") or "unknown",
        "worktree": str(worktree),
        "branch": current_branch(repo),
        "repo": str(repo),
        "created": now,
        "expires": now + ttl_hours * 3600 if ttl_hours > 0 else 0,
        "contexts": chosen_contexts,
        "globs": sorted(set(globs)),
        "note": args.note or "",
    }

    # Aviso de colisão com outras sessões ativas.
    for other in active_leases(repo, exclude=session):
        for g in lease["globs"]:
            for og in other.get("globs", []):
                if globs_overlap(g, og):
                    print(
                        f"[agent-scope] AVISO: glob '{g}' sobrepõe '{og}' "
                        f"da sessão '{other.get('session')}' ({other.get('worktree')})",
                        file=sys.stderr,
                    )

    path = lease_path(repo, session)
    if path is None:
        print("[agent-scope] não foi possível resolver <git-common-dir>", file=sys.stderr)
        return 2

    # Lease ativo existente: sobrescrita silenciosa permitiria uma sessão
    # capturar o id/escopo de outra. Exigir --amend explícito.
    existing = load_lease(path) if path.is_file() else None
    if existing and not lease_expired(existing, now) and not args.amend:
        print(
            f"[agent-scope] lease '{session}' já existe e está ativo "
            f"(worktree: {existing.get('worktree')}). "
            f"Para alterar o próprio escopo, repita com --amend; "
            f"para sessão diferente no mesmo worktree, use outro --session.",
            file=sys.stderr,
        )
        return 2

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(lease, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)  # escrita atômica: sem lease truncado em corrida
    exp = time.strftime("%H:%M", time.localtime(lease["expires"])) if lease["expires"] else "sem expiração"
    print(f"[agent-scope] lease '{session}' registrado em {worktree} (expira {exp})")
    for g in lease["globs"]:
        print(f"    {g}")
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or os.getcwd()))
    if repo is None:
        return 2
    session = args.session or os.environ.get("AGENT_SESSION") or repo.name
    path = lease_path(repo, session)
    if path is None or not path.is_file():
        print(f"[agent-scope] nenhum lease para '{session}'")
        return 1
    path.unlink()
    print(f"[agent-scope] lease '{session}' encerrado")
    return 0


def cmd_expire(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or os.getcwd()))
    if repo is None:
        return 2
    now = time.time()
    removed = []
    for path, lease in iter_leases(repo):
        if lease_expired(lease, now):
            path.unlink()
            removed.append(lease.get("session", path.stem))
    print(f"[agent-scope] {len(removed)} lease(s) expirado(s) removido(s): {', '.join(removed) or '-'}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or os.getcwd()))
    if repo is None:
        return 2
    leases = iter_leases(repo)
    if not leases:
        print("[agent-scope] nenhum lease registrado")
        return 0
    now = time.time()
    print(f"{'sessão':<32} {'worktree':<44} {'branch':<30} {'expira em':<10}")
    for _, lease in leases:
        exp = lease.get("expires") or 0
        left = "expirado" if exp and now >= exp else (f"{(exp - now) / 3600:.1f}h" if exp else "∞")
        print(
            f"{lease.get('session', '?'):<32} "
            f"{Path(lease.get('worktree', '')).name:<44} "
            f"{lease.get('branch', ''):<30} {left:<10}"
        )
    return 0


def resolve_repo_and_lease(args: argparse.Namespace) -> Tuple[Optional[Path], Path, Optional[dict], Optional[dict]]:
    start = Path(args.repo or os.getcwd())
    repo = repo_root(start)
    if repo is None:
        return None, start, None, None
    worktree = Path((run_git(repo, ["rev-parse", "--show-toplevel"]) or "").strip() or repo).resolve()
    cfg = load_config(repo)
    lease = find_lease(repo, worktree, args.session)
    return repo, worktree, cfg, lease


def cmd_check(args: argparse.Namespace) -> int:
    repo, worktree, cfg, lease = resolve_repo_and_lease(args)
    if repo is None:
        print("[agent-scope] fora de um repositório git", file=sys.stderr)
        return 2
    files = staged_files(repo) if args.staged else dirty_files(repo)
    if not files:
        print("[agent-scope] nenhum arquivo a classificar")
        return 0
    out_of_scope, foreign = classify_files(files, repo, lease)
    label = lease.get("session") if lease else "(sem lease)"
    print(f"[agent-scope] worktree={worktree.name} sessão={label} arquivos={len(files)}")
    for path in files:
        if any(path == f for f, _ in foreign):
            owner = next(o for f, o in foreign if f == path)
            print(f"    FOREIGN    {path}  (sessão '{owner}')")
        elif path in out_of_scope:
            print(f"    FORA       {path}")
        else:
            print(f"    ok         {path}")
    return 1 if (out_of_scope or foreign) else 0


def cmd_pre_commit(args: argparse.Namespace) -> int:
    start = Path(os.getcwd())
    repo = repo_root(start)
    if repo is None:
        return 0
    cfg = load_config(repo)
    if cfg is None:
        return 0  # feature desligada neste repo

    files = staged_files(repo)
    if not files:
        return 0
    worktree = Path((run_git(repo, ["rev-parse", "--show-toplevel"]) or "").strip() or repo).resolve()
    lease = find_lease(repo, worktree, args.session)

    if lease is None:
        if not cfg.get("require_lease", True):
            return 0
        print_block_header("COMMIT BLOQUEADO — nenhum lease de sessão para este worktree")
        print(f"  worktree: {worktree}", file=sys.stderr)
        print("  Registre o escopo desta sessão antes de commitar:", file=sys.stderr)
        print(register_hint(repo), file=sys.stderr)
        print("  Contextos em: agent-kit/scope/contexts.json", file=sys.stderr)
        print("  Escape manual (desaconselhado): git commit --no-verify", file=sys.stderr)
        return 1

    out_of_scope, foreign = classify_files(files, repo, lease)
    if not out_of_scope and not foreign:
        return 0

    print_block_header(
        f"COMMIT BLOQUEADO — sessão '{lease.get('session')}' fora do escopo declarado"
    )
    for path, owner in foreign:
        print(f"  {path}\n      → está no escopo da sessão '{owner}'", file=sys.stderr)
    for path in out_of_scope:
        print(f"  {path}\n      → fora de qualquer escopo", file=sys.stderr)
    print("  Escopo desta sessão:", file=sys.stderr)
    for g in lease.get("globs", []):
        print(f"    {g}", file=sys.stderr)
    print("  Corrija o stage ou coordene com a sessão dona.", file=sys.stderr)
    print("  Para ampliar O SEU lease (mesma sessão), repita o register com --amend;", file=sys.stderr)
    print("  sessão diferente neste worktree: registre com um --session próprio.", file=sys.stderr)
    print("  Escape manual (desaconselhado): git commit --no-verify", file=sys.stderr)
    return 1


def worktree_list(repo: Path) -> List[dict]:
    out = run_git(repo, ["worktree", "list", "--porcelain"])
    if out is None:
        return []
    entries, current = [], {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if current:
                entries.append(current)
            current = {"path": line[len("worktree "):], "detached": False, "branch": ""}
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):].replace("refs/heads/", "")
        elif line == "detached":
            current["detached"] = True
        elif line.startswith("prunable"):
            current["prunable"] = True
    if current:
        entries.append(current)
    return entries


def cmd_audit(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or os.getcwd()))
    if repo is None:
        print("[agent-scope] fora de um repositório git", file=sys.stderr)
        return 2
    cfg = load_config(repo)
    leases = iter_leases(repo)
    now = time.time()
    by_worktree = {}
    for _, lease in leases:
        by_worktree.setdefault(lease.get("worktree"), []).append(lease)

    report = {"worktrees": [], "violations": [], "stale_leases": []}
    worktrees = worktree_list(repo)

    def collect(entry: dict) -> Tuple[dict, List[str]]:
        wt_repo = Path(entry["path"])
        if not wt_repo.is_dir():
            return entry, []
        files = dirty_files(wt_repo)
        if args.diff:
            files = sorted(set(files) | set(diff_files(wt_repo, args.diff)))
        return entry, files

    max_workers = min(8, max(1, len(worktrees)))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        collected = list(pool.map(collect, worktrees))

    for entry, files in collected:
        wt_path = entry["path"]
        wt_repo = Path(wt_path)
        if not wt_repo.is_dir():
            continue
        leases_here = [l for l in by_worktree.get(wt_path, []) if not lease_expired(l, now)]
        lease = leases_here[0] if leases_here else None
        expired_here = [l for l in by_worktree.get(wt_path, []) if lease_expired(l, now)]

        record = {
            "worktree": wt_path,
            "branch": entry.get("branch") or "(detached)",
            "session": lease.get("session") if lease else None,
            "dirty_files": len(files),
            "out_of_scope": [],
            "foreign": [],
        }
        if files:
            out_of_scope, foreign = classify_files(files, wt_repo, lease)
            if lease is None:
                # Sem lease não há escopo a violar: um flag único por worktree.
                out_of_scope = [] if (cfg or {}).get("require_lease", True) else out_of_scope
            record["out_of_scope"] = out_of_scope[:200]
            record["foreign"] = [{"file": f, "owner": o} for f, o in foreign][:200]
            if len(out_of_scope) > 200 or len(foreign) > 200:
                record["truncated"] = True
            for f in out_of_scope:
                report["violations"].append(
                    {"worktree": wt_path, "file": f, "kind": "out_of_scope",
                     "session": record["session"]}
                )
            for f, o in foreign:
                report["violations"].append(
                    {"worktree": wt_path, "file": f, "kind": "foreign_scope",
                     "owner": o, "session": record["session"]}
                )
            if lease is None and (cfg or {}).get("require_lease", True):
                report["violations"].append(
                    {"worktree": wt_path, "file": None, "kind": "unregistered_dirty",
                     "session": None}
                )
        for l in expired_here:
            report["stale_leases"].append(
                {"session": l.get("session"), "worktree": wt_path,
                 "expired_at": l.get("expires")}
            )
        report["worktrees"].append(record)

    # leases sem worktree correspondente na lista
    known = {e["path"] for e in worktrees}
    for _, lease in leases:
        if lease.get("worktree") not in known:
            report["stale_leases"].append(
                {"session": lease.get("session"), "worktree": lease.get("worktree"),
                 "reason": "worktree ausente"}
            )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"[agent-scope] audit — {len(worktrees)} worktree(s), {len(leases)} lease(s)")
        for rec in report["worktrees"]:
            flag = ""
            if rec["out_of_scope"] or rec["foreign"]:
                flag = "  ⚠ VIOLAÇÃO"
            elif rec["dirty_files"] and rec["session"] is None:
                flag = "  ⚠ sujo sem lease"
            print(
                f"  {Path(rec['worktree']).name:<44} {rec['branch']:<30} "
                f"sessão={rec['session'] or '-':<24} sujos={rec['dirty_files']}{flag}"
            )
            for f in rec["out_of_scope"][:10]:
                print(f"      FORA     {f}")
            for item in rec["foreign"][:10]:
                print(f"      FOREIGN  {item['file']}  (sessão '{item['owner']}')")
        if report["stale_leases"]:
            print("  leases obsoletos:")
            for s in report["stale_leases"]:
                print(f"      {s['session']}  ({s.get('worktree')})")
        if not report["violations"]:
            print("  nenhuma violação detectada")
    return 1 if report["violations"] else 0


def cmd_install_hook(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or os.getcwd()))
    if repo is None:
        print("[agent-scope] fora de um repositório git", file=sys.stderr)
        return 2
    out = run_git(repo, ["rev-parse", "--git-path", "hooks"])
    if not out:
        return 2
    hooks = Path(out.strip())
    if not hooks.is_absolute():
        hooks = (repo / hooks).resolve()
    hooks.mkdir(parents=True, exist_ok=True)
    target = hooks / "pre-commit"
    if target.exists() and HOOK_MARKER not in target.read_text(encoding="utf-8", errors="replace"):
        if not args.force:
            print(
                f"[agent-scope] {target} já existe e não é nosso; use --force ou encadeie manualmente",
                file=sys.stderr,
            )
            return 2
        backup = target.with_name(f"pre-commit.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        target.rename(backup)
        print(f"[agent-scope] hook existente preservado em {backup.name}")
    script = Path(__file__).resolve()
    wrapper = (
        "#!/bin/sh\n"
        f"# {HOOK_MARKER} — gerado por session_scope.py install-hook\n"
        f'exec "{sys.executable}" "{script}" pre-commit "$@"\n'
    )
    target.write_text(wrapper, encoding="utf-8")
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[agent-scope] pre-commit instalado em {target} (válido para todos os worktrees)")

    # Semente de config no git comum: cobre worktrees em branches antigas que
    # ainda não têm agent-scope.json versionado. O arquivo commitado prevalece.
    src_cfg = repo / CONFIG_NAME
    common = common_git_dir(repo)
    if src_cfg.is_file() and common:
        seed_dir = common / "agent-scope"
        seed_dir.mkdir(parents=True, exist_ok=True)
        seed = seed_dir / "config.json"
        if not seed.is_file():
            seed.write_text(src_cfg.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"[agent-scope] config semeada em {seed} (fallback para branches sem {CONFIG_NAME})")
        src_ctx = repo / (load_config(repo) or {}).get("contexts_file", DEFAULT_CONTEXTS_FILE)
        seed_ctx = seed_dir / "contexts.json"
        if src_ctx.is_file() and not seed_ctx.is_file():
            seed_ctx.write_text(src_ctx.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"[agent-scope] contexts semeados em {seed_ctx}")
    return 0


def cmd_uninstall_hook(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or os.getcwd()))
    if repo is None:
        return 2
    out = run_git(repo, ["rev-parse", "--git-path", "hooks"])
    if not out:
        return 2
    target = Path(out.strip()) / "pre-commit"
    if not target.is_absolute():
        target = (repo / target).resolve()
    if target.is_file() and HOOK_MARKER in target.read_text(encoding="utf-8", errors="replace"):
        target.unlink()
        print(f"[agent-scope] pre-commit removido de {target}")
    else:
        print("[agent-scope] nenhum hook nosso instalado")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="session_scope", description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", help="caminho dentro do repositório (default: cwd)")
    common.add_argument("--session", help="id da sessão (default: $AGENT_SESSION ou nome do worktree)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("register", parents=[common], help="registra lease da sessão")
    p.add_argument("--context", action="append", help="contexto de contexts.json (repetível)")
    p.add_argument("--path", action="append", help="glob extra de escopo (repetível)")
    p.add_argument("--worktree", help="worktree do lease (default: atual)")
    p.add_argument("--agent", help="devin|cursor|claude|human|...")
    p.add_argument("--ttl", type=float, help="horas até expirar (0 = sem expiração)")
    p.add_argument("--note", help="nota da tarefa")
    p.add_argument("--allow-restricted", action="store_true", help="permite contextos restritos")
    p.add_argument("--amend", action="store_true",
                   help="altera lease ativo existente da MESMA sessão (escopo/TTL)")
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("release", parents=[common], help="encerra lease de uma sessão")
    p.set_defaults(func=cmd_release)

    p = sub.add_parser("expire", parents=[common], help="remove leases vencidos")
    p.set_defaults(func=cmd_expire)

    p = sub.add_parser("status", parents=[common], help="lista leases")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("check", parents=[common], help="classifica arquivos do worktree contra o lease")
    p.add_argument("--staged", action="store_true", help="só arquivos staged (default: sujos)")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("pre-commit", parents=[common], help="modo hook do git")
    p.set_defaults(func=cmd_pre_commit)

    p = sub.add_parser("audit", parents=[common], help="audita todos os worktrees (sentinela)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--diff", help="também auditar arquivos de <base>...HEAD por worktree")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("install-hook", parents=[common], help="instala pre-commit no git comum")
    p.add_argument("--force", action="store_true", help="sobrescreve hook estrangeiro (com backup)")
    p.set_defaults(func=cmd_install_hook)

    p = sub.add_parser("uninstall-hook", parents=[common], help="remove nosso pre-commit")
    p.set_defaults(func=cmd_uninstall_hook)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
