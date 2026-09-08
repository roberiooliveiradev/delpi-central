#!/usr/bin/env python3
"""Gate diff-aware de autorização para writes FastAPI da Minha DELPI.

Escopo deliberadamente conservador:
- somente APIs FastAPI top-level `api-delpi` ou `<app>-api`;
- somente POST/PUT/PATCH/DELETE novos ou alterados;
- GET/HEAD/OPTIONS ficam fora até a classificação de leitura estar madura.

Um write passa quando existe evidência estrutural de pelo menos um destes modelos:
1. decorator de acesso canônico (`require_*`, `policy`);
2. autorização no application/use case, com contexto de usuário efetivamente entregue;
3. guarda de acesso explícita dentro do handler;
4. rota pública cujo prefixo/exato está realmente liberado no auth_middleware do app.

O objetivo não é provar toda a autorização por análise estática. O objetivo é impedir
que novos writes sensíveis nasçam sem qualquer evidência de ownership de acesso.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRITE_METHODS = {"post", "put", "patch", "delete"}
HTTP_METHODS = WRITE_METHODS | {"get", "head", "options", "trace"}
ACCESS_DECORATORS = {
    "require_auth",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_superadmin",
    "policy",
}
USER_RESOLVER_CALLS = {
    "get_current_user",
    "resolve_user",
    "resolve_current_user",
    "current_user",
}
GUARD_NAME_TOKENS = (
    "permission",
    "authorize",
    "authorization",
    "access",
    "require_",
    "assert_",
)
SKIP_SOURCE_PARTS = {"tests", "test", "fixtures", "docs", ".cursor", "scripts"}


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    line: int
    message: str

    def format(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"[{self.rule}] {where} — {self.message}"


@dataclass(frozen=True)
class RouteContract:
    method: str
    path: str
    line: int
    end_line: int
    function: ast.FunctionDef | ast.AsyncFunctionDef


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} falhou")
    return result.stdout


def resolve_base(explicit: str | None) -> str:
    candidate = (explicit or os.getenv("FASTAPI_AUTHZ_BASE_SHA") or "").strip()
    if not candidate or set(candidate) == {"0"}:
        candidate = git("rev-parse", "HEAD^", check=False).strip()
    if not candidate:
        raise RuntimeError("não foi possível resolver commit base; informe --base")
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{candidate}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"commit base não disponível no checkout: {candidate}")
    return candidate


def changed_line_numbers(base: str) -> dict[str, set[int]]:
    """Mapeia hunks do diff para linhas do arquivo novo, incluindo hunks só de remoção."""
    diff = git("diff", "--unified=0", "--no-color", f"{base}..HEAD", "--", ".")
    files: dict[str, set[int]] = {}
    current: str | None = None
    hunk_re = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            current = raw[6:]
            files.setdefault(current, set())
            continue
        if raw.startswith("+++ /dev/null"):
            current = None
            continue
        if current is None or not raw.startswith("@@"):
            continue
        match = hunk_re.search(raw)
        if not match:
            continue
        start = int(match.group(1))
        count = int(match.group(2)) if match.group(2) is not None else 1
        if count == 0:
            files[current].add(max(1, start))
        else:
            files[current].update(range(start, start + count))

    return {path: lines for path, lines in files.items() if lines}


def is_fastapi_api_source(path: str) -> bool:
    candidate = Path(path)
    if candidate.suffix.lower() != ".py" or not candidate.parts:
        return False
    root = candidate.parts[0]
    if root != "api-delpi" and not root.endswith("-api"):
        return False
    return not any(part in SKIP_SOURCE_PARTS for part in candidate.parts[1:])


def api_root(path: str) -> str | None:
    if not is_fastapi_api_source(path):
        return None
    return Path(path).parts[0]


def _literal_string(node: ast.AST | None, *, allow_empty: bool = False) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        value = node.value.strip()
        if value or allow_empty:
            return value
    return None


def _callee_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _extract_strings(node: ast.AST) -> set[str]:
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, str)
        and child.value.startswith("/")
    }


def router_prefixes(tree: ast.AST) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Call) or _callee_name(value.func) != "APIRouter":
            continue
        prefix = ""
        for keyword in value.keywords:
            if keyword.arg == "prefix":
                prefix = _literal_string(keyword.value) or ""
                break
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets.extend(node.targets)
        elif node.target is not None:
            targets.append(node.target)
        for target in targets:
            if isinstance(target, ast.Name):
                result[target.id] = prefix.rstrip("/")
    return result


def _route_receiver_and_method(decorator: ast.AST) -> tuple[str | None, str | None, ast.Call | None]:
    if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
        return None, None, None
    method = decorator.func.attr.lower()
    if method not in HTTP_METHODS:
        return None, None, None
    receiver = decorator.func.value.id if isinstance(decorator.func.value, ast.Name) else None
    return receiver, method, decorator


def route_contracts(source: str) -> list[RouteContract]:
    tree = ast.parse(source)
    prefixes = router_prefixes(tree)
    result: list[RouteContract] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            receiver, method, call = _route_receiver_and_method(decorator)
            if method is None or call is None or not call.args:
                continue
            local_path = _literal_string(call.args[0], allow_empty=True)
            if local_path is None or (local_path != "" and not local_path.startswith("/")):
                continue
            prefix = prefixes.get(receiver or "", "")
            if local_path in {"", "/"}:
                full_path = prefix or "/"
            else:
                full_path = f"{prefix}/{local_path.lstrip('/')}" if prefix else local_path
            full_path = "/" + full_path.strip("/") if full_path != "/" else "/"
            start = min(
                [getattr(item, "lineno", getattr(node, "lineno", 0)) for item in node.decorator_list]
                or [getattr(node, "lineno", 0)]
            )
            result.append(
                RouteContract(
                    method=method,
                    path=full_path,
                    line=start,
                    end_line=getattr(node, "end_lineno", getattr(node, "lineno", start)),
                    function=node,
                )
            )
    return result


def route_touched(route: RouteContract, changed_lines: set[int]) -> bool:
    return any(route.line <= line <= max(route.line, route.end_line) for line in changed_lines)


def _access_decorator_names(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names: set[str] = set()
    for decorator in function.decorator_list:
        _receiver, method, _call = _route_receiver_and_method(decorator)
        if method is not None:
            continue
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = _callee_name(target)
        if name:
            names.add(name)
    return names


def has_access_decorator(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return bool(_access_decorator_names(function) & ACCESS_DECORATORS)


def _is_request_state_user(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "user"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "state"
        and isinstance(node.value.value, ast.Name)
    )


def _resolver_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and (_callee_name(node.func) or "") in USER_RESOLVER_CALLS


def _user_aliases(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    aliases: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if value is None or not (_is_request_state_user(value) or _resolver_call(value)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                aliases.add(target.id)
    return aliases


def _contains_user_context(node: ast.AST, aliases: set[str]) -> bool:
    for child in ast.walk(node):
        if _is_request_state_user(child):
            return True
        if isinstance(child, ast.Name) and child.id in aliases:
            return True
        if _resolver_call(child):
            return True
    return False


def has_application_user_handoff(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    aliases = _user_aliases(function)
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        called = (_callee_name(node.func) or "").lower()
        if called in USER_RESOLVER_CALLS:
            continue
        arguments = [*node.args, *(kw.value for kw in node.keywords)]
        if any(_contains_user_context(argument, aliases) for argument in arguments):
            return True
    return False


def has_explicit_guard_call(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        name = (_callee_name(node.func) or "").lower()
        if not name:
            continue
        if name in {"has_permission", "has_any_permission", "has_all_permissions"}:
            return True
        if any(token in name for token in GUARD_NAME_TOKENS):
            return True
    return False


def extract_public_contract(source: str) -> tuple[set[str], set[str], bool]:
    """Retorna (prefixos, exatos, libera_todo_/public/)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set(), set(), False

    prefixes: set[str] = set()
    exacts: set[str] = {"/health"}
    generic_public = False

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [target.id for target in targets if isinstance(target, ast.Name)]
            value = node.value
            if value is None:
                continue
            for name in names:
                upper = name.upper()
                if "PUBLIC" not in upper:
                    continue
                strings = _extract_strings(value)
                if "PREFIX" in upper:
                    prefixes.update(strings)
                elif "EXACT" in upper:
                    exacts.update(strings)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and "public" in node.name.lower():
            for child in ast.walk(node):
                if not isinstance(child, ast.Call) or not isinstance(child.func, ast.Attribute):
                    continue
                if child.func.attr != "startswith" or not child.args:
                    continue
                value = _literal_string(child.args[0])
                if value:
                    prefixes.add(value)
                    if value.rstrip("/") == "/public":
                        generic_public = True

    if any(prefix.rstrip("/") == "/public" for prefix in prefixes):
        generic_public = True
    return prefixes, exacts, generic_public


def discover_public_contract(root_name: str) -> tuple[set[str], set[str], bool]:
    root = ROOT / root_name
    if not root.exists():
        return set(), {"/health"}, False
    prefixes: set[str] = set()
    exacts: set[str] = {"/health"}
    generic_public = False
    for path in root.rglob("auth_middleware.py"):
        try:
            found_prefixes, found_exacts, found_generic = extract_public_contract(
                path.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeDecodeError):
            continue
        prefixes.update(found_prefixes)
        exacts.update(found_exacts)
        generic_public = generic_public or found_generic
    return prefixes, exacts, generic_public


def public_contract_allows(
    route_path: str,
    prefixes: set[str],
    exacts: set[str],
    generic_public: bool,
) -> bool:
    normalized = route_path.rstrip("/") or "/"
    if normalized in {item.rstrip("/") or "/" for item in exacts}:
        return True
    if generic_public and (normalized == "/public" or normalized.startswith("/public/")):
        return True
    for prefix in prefixes:
        normalized_prefix = prefix.rstrip("/")
        if normalized == normalized_prefix or normalized.startswith(normalized_prefix + "/"):
            return True
    return False


def scan_fastapi_authz_source(
    path: str,
    source: str,
    changed_lines: set[int],
    public_prefixes: set[str] | None = None,
    public_exacts: set[str] | None = None,
    generic_public: bool = False,
) -> list[Violation]:
    if not is_fastapi_api_source(path):
        return []
    try:
        routes = route_contracts(source)
    except SyntaxError as exc:
        return [Violation("FASTAPI_AUTHZ_PARSE_ERROR", path, exc.lineno or 0, str(exc))]

    prefixes = public_prefixes or set()
    exacts = public_exacts or {"/health"}
    findings: list[Violation] = []

    for route in routes:
        if route.method not in WRITE_METHODS or not route_touched(route, changed_lines):
            continue

        looks_public = route.path == "/public" or route.path.startswith("/public/")
        is_public = public_contract_allows(route.path, prefixes, exacts, generic_public)
        if looks_public and not is_public:
            findings.append(
                Violation(
                    "FASTAPI_PUBLIC_ROUTE_AUTH_DRIFT",
                    path,
                    route.line,
                    f"{route.method.upper()} {route.path} parece pública, mas não está liberada pelo auth_middleware do bounded context",
                )
            )
            continue
        if is_public:
            continue

        if has_access_decorator(route.function):
            continue
        if has_explicit_guard_call(route.function):
            continue
        if has_application_user_handoff(route.function):
            continue

        findings.append(
            Violation(
                "FASTAPI_WRITE_AUTHZ_EVIDENCE_REQUIRED",
                path,
                route.line,
                f"{route.method.upper()} {route.path} novo/alterado não apresenta evidência de autorização: "
                "use decorator canônico, guarda explícita ou entregue o contexto do usuário ao application/use case",
            )
        )
    return findings


def collect(base: str) -> list[Violation]:
    findings: list[Violation] = []
    contracts: dict[str, tuple[set[str], set[str], bool]] = {}
    for path, lines in changed_line_numbers(base).items():
        if not is_fastapi_api_source(path):
            continue
        source_path = ROOT / path
        if not source_path.exists():
            continue
        root_name = api_root(path)
        if root_name is None:
            continue
        contract = contracts.setdefault(root_name, discover_public_contract(root_name))
        try:
            source = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings.extend(
            scan_fastapi_authz_source(
                path,
                source,
                lines,
                public_prefixes=contract[0],
                public_exacts=contract[1],
                generic_public=contract[2],
            )
        )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        base = resolve_base(args.base)
        findings = collect(base)
    except RuntimeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2

    print("FastAPI AuthZ guardrails")
    print(f"- base: {base}")
    print(f"- findings: {len(findings)}")
    for finding in findings:
        print(f"- {finding.format()}")

    if findings and args.check:
        print("FALHOU: write FastAPI sem ownership de autorização detectado", file=sys.stderr)
        return 1

    print("OK: nenhum novo write FastAPI sem evidência de autorização")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
