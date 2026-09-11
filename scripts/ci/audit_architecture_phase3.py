#!/usr/bin/env python3
"""Gate incremental da Fase 3 para novas regressões arquiteturais.

O gate é diff-aware: legado existente não derruba o CI, mas novas violações
introduzidas no diff falham. Regras cobertas:

- CHAT_ROUTE_HARDCODE: endpoint/provider específico no motor genérico do chat;
- LEGACY_REGISTRY_GROWTH: crescimento técnico do operational_route_registry manual;
- HTTP_TIMEOUT_REQUIRED: novo client/call HTTP Python sem timeout explícito;
- UNSAFE_WRITE_RETRY: retry configurado para métodos de escrita sem exceção explícita;
- SECRET_IN_LOG: segredo/credencial enviado para logger/print/console;
- SECRET_LITERAL: segredo literal óbvio em código/config de produção.
- SEMANTIC_* (E11.S1): substitutos de path/domain/strategy/routeSegment/catalog/credenciais;
  use `--check-semantic-debt` para full-tree (vermelho até cleanup Onda J).

Uso CI:
  python scripts/ci/audit_architecture_phase3.py --check --base <sha>
  python scripts/ci/audit_architecture_phase3.py --check-semantic-debt

Exceções são temporárias e explícitas em scripts/ci/architecture_phase3_exceptions.json.
O fingerprint exibido pelo gate deve ser copiado para uma exceção com owner,
reason e reviewBy. Não há wildcard.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
EXCEPTIONS_PATH = ROOT / "scripts" / "ci" / "architecture_phase3_exceptions.json"
REGISTRY_REL = "minha-delpi-ai-api/app/content/pt-BR/assistant/operational_route_registry.json"

CHAT_ROUTING_PREFIXES = (
    "minha-delpi-ai-api/app/application/services/external_actions/",
    "minha-delpi-ai-api/app/domain/services/external_actions/",
)
CHAT_ROUTING_EXTRA_FILES = {
    "minha-delpi-ai-api/app/application/use_cases/execute_external_action_use_case.py",
}

PRODUCTION_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".yml", ".yaml", ".json", ".toml", ".sh"
}
SKIP_SECRET_PARTS = ("/tests/", "/test/", "/fixtures/", "/docs/", "/.cursor/")

PATH_LITERAL_RE = re.compile(r"[\"']/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_{}.-]+)*[\"']")
PROVIDER_LITERAL_RE = re.compile(r"[\"']api[_-]delpi(?:\.|[\"'])", re.IGNORECASE)
OPERATION_ID_LITERAL_RE = re.compile(
    r"[\"'](?:get|post|put|patch|delete)_[a-z0-9_]{5,}[\"']", re.IGNORECASE
)
SELECTOR_CONTEXT_RE = re.compile(
    r"\b(path|operation_?id|action_?id|provider_?key|candidate|score|priority|boost|route)\b",
    re.IGNORECASE,
)

SECRET_ASSIGN_RE = re.compile(
    r"(?i)\b(api[_-]?key|client[_-]?secret|password|passwd|access[_-]?token|refresh[_-]?token)\b"
    r"\s*[=:]\s*[\"']([^\"']{8,})[\"']"
)
EMBEDDED_CREDENTIAL_URL_RE = re.compile(r"https?://[^\s/:@]+:[^\s/@]+@", re.IGNORECASE)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
JS_LOG_SECRET_RE = re.compile(
    r"console\.(?:log|info|warn|error)\([^\n]*(?:token|api[_-]?key|password|secret|authorization|cookie)",
    re.IGNORECASE,
)
PLACEHOLDER_TOKENS = ("example", "placeholder", "change-me", "changeme", "dummy", "xxxx", "${", "{{")
SENSITIVE_ID_RE = re.compile(
    r"(?:^|_)(?:access_token|refresh_token|token|api_key|apikey|password|passwd|secret|authorization|cookie|credential)(?:$|_)",
    re.IGNORECASE,
)
SAFE_SENSITIVE_SUFFIXES = (
    "_type", "_count", "_present", "_configured", "_expires", "_expiry", "_hash", "_id",
    "_len", "_length", "_usage", "_name",
)

HTTP_DIRECT_CALLS = {
    "requests.get", "requests.post", "requests.put", "requests.patch", "requests.delete", "requests.request",
    "httpx.get", "httpx.post", "httpx.put", "httpx.patch", "httpx.delete", "httpx.request",
    "httpx.Client", "httpx.AsyncClient", "aiohttp.ClientSession",
}
HTTPX_BARE_CONSTRUCTORS = {"Client", "AsyncClient"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

REGISTRY_LIST_FIELDS = {
    "pathMarkers", "operationIdMarkers", "excludePathMarkers",
}
REGISTRY_SCALAR_FIELDS = {
    "routeSegment", "pathSuffix", "pathExactEnd", "method",
}

# E11.S1 — semantic substitutes (JSON↔Python). Full-tree debt via --check-semantic-debt;
# diff-aware audit() also blocks *new* introductions of the same concepts.
SEMANTIC_DEBT_SKIP_PARTS = (
    "/docs/",
    "/evidence/",
    "/.cursor/",
    "/tests/",
    "/test/",
    "/fixtures/",
    "/__pycache__/",
    "/scripts/ci/",
    "/node_modules/",
    "/.venv/",
)
SEMANTIC_CONTENT_LATERAL_KEYS_RE = re.compile(
    r'"(pathMarkers|pathToken|pathContains|pathRules|excludePathMarkers|operationIdMarkers)"\s*:'
)
SEMANTIC_DOMAIN_RULES_RE = re.compile(r"\b_DOMAIN_RULES\s*[:=]")
SEMANTIC_PATH_STRATEGY_CLASS_RE = re.compile(r"\bclass\s+ParameterStrategyInferenceService\b")
SEMANTIC_PATH_STRATEGY_BRANCH_RE = re.compile(
    r'(?:in\s+lowered|in\s+path|path\.contains|/products/|/system/|"by-supplier|'
    r'"exclusive-raw|"department-|"sale-orders|"safety-stock)'
)
SEMANTIC_ROUTE_SEGMENT_CLASS_RE = re.compile(r"\bclass\s+RouteSegmentInferenceService\b")
SEMANTIC_ROUTE_SEGMENT_PATH_TAIL_RE = re.compile(
    r"\bcontinuity_keys_from_path\b|\bpath_for_operation_id\b|_operation_id_to_path\b"
)
SEMANTIC_SMOKE_CRED_DEFAULT_RE = re.compile(
    r"""(?:os\.environ\.get|getenv)\(\s*['\"]SMOKE_(?:USER|PASSWORD)['\"]\s*,\s*['\"][^'\"]+['\"]"""
)
# Legitimate technical use of action path for HTTP — must NOT trip semantic debt alone.
SEMANTIC_HTTP_PATH_NEGATIVE_RE = re.compile(
    r"""(?:action|payload|selected)\s*(?:\.\s*get\(\s*['\"]path['\"]|\[['\"]path['\"])"""
)


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    line: int
    message: str

    @property
    def fingerprint(self) -> str:
        payload = f"{self.rule}|{self.path}|{normalize(self.message)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def normalize(value: str) -> str:
    return " ".join(str(value).strip().split())


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} falhou")
    return result.stdout


def resolve_base(explicit: str | None) -> str:
    candidate = (explicit or os.getenv("PHASE3_BASE_SHA") or "").strip()
    if not candidate or set(candidate) == {"0"}:
        candidate = git("rev-parse", "HEAD^", check=False).strip()
    if not candidate:
        raise RuntimeError("não foi possível resolver commit base; informe --base")
    if subprocess.run(
        ["git", "cat-file", "-e", f"{candidate}^{{commit}}"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(f"commit base não disponível no checkout: {candidate}")
    return candidate


def added_lines(base: str) -> dict[str, dict[int, str]]:
    diff = git("diff", "--unified=0", "--no-color", f"{base}..HEAD", "--", ".")
    files: dict[str, dict[int, str]] = {}
    current: str | None = None
    new_line: int | None = None
    hunk_re = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            current = raw[6:]
            files.setdefault(current, {})
            new_line = None
            continue
        if raw.startswith("+++ /dev/null"):
            current = None
            new_line = None
            continue
        if raw.startswith("@@"):
            match = hunk_re.search(raw)
            new_line = int(match.group(1)) if match else None
            continue
        if current is None or new_line is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            files[current][new_line] = raw[1:]
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        else:
            new_line += 1

    return {path: lines for path, lines in files.items() if lines}


def is_chat_routing_file(path: str) -> bool:
    return path in CHAT_ROUTING_EXTRA_FILES or any(path.startswith(prefix) for prefix in CHAT_ROUTING_PREFIXES)


def scan_chat_route_hardcode(path: str, lines: dict[int, str]) -> list[Violation]:
    if not is_chat_routing_file(path):
        return []
    findings: list[Violation] = []
    for line_no, line in lines.items():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        reason = ""
        if PROVIDER_LITERAL_RE.search(line):
            reason = "provider api-delpi literal no motor genérico"
        elif PATH_LITERAL_RE.search(line):
            reason = "path literal de endpoint no motor genérico"
        elif OPERATION_ID_LITERAL_RE.search(line) and SELECTOR_CONTEXT_RE.search(line):
            reason = "operationId literal usado em seleção/ranking"
        elif re.search(r"\b(?:if|elif)\b", line) and SELECTOR_CONTEXT_RE.search(line) and re.search(r"[\"'][^\"']{3,}[\"']", line):
            reason = "condicional de seleção baseada em literal técnico"
        if reason:
            findings.append(Violation("CHAT_ROUTE_HARDCODE", path, line_no, f"{reason}: {normalize(line)}"))
    return findings


def load_json_from_git(ref: str, path: str) -> dict[str, Any] | None:
    raw = git("show", f"{ref}:{path}", check=False)
    if not raw.strip():
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def registry_technical_state(payload: dict[str, Any]) -> dict[str, dict[str, set[str]]]:
    state: dict[str, dict[str, set[str]]] = {}
    routes = payload.get("routes")
    if not isinstance(routes, list):
        return state
    for item in routes:
        if not isinstance(item, dict):
            continue
        route_id = str(item.get("id") or "").strip()
        if not route_id:
            continue
        values: dict[str, set[str]] = {}
        route_spec = item.get("route") if isinstance(item.get("route"), dict) else {}
        for field in REGISTRY_LIST_FIELDS:
            raw = route_spec.get(field)
            if isinstance(raw, list):
                values[field] = {str(v).strip() for v in raw if str(v).strip()}
        for field in REGISTRY_SCALAR_FIELDS:
            raw = item.get(field) if field == "routeSegment" else route_spec.get(field)
            if raw is not None and str(raw).strip():
                values[field] = {str(raw).strip()}
        parameters = item.get("parameters") if isinstance(item.get("parameters"), dict) else {}
        strategy = str(parameters.get("strategy") or "").strip()
        if strategy:
            values["parameterStrategy"] = {strategy}
        state[route_id] = values
    return state


def scan_registry_growth(base: str) -> list[Violation]:
    current_path = ROOT / REGISTRY_REL
    if not current_path.is_file():
        return []
    old_payload = load_json_from_git(base, REGISTRY_REL)
    if old_payload is None:
        return []
    try:
        current_payload = json.loads(current_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [Violation("LEGACY_REGISTRY_GROWTH", REGISTRY_REL, 0, f"registry JSON inválido: {exc}")]

    old_state = registry_technical_state(old_payload)
    new_state = registry_technical_state(current_payload)
    findings: list[Violation] = []

    for route_id in sorted(set(new_state) - set(old_state)):
        findings.append(Violation(
            "LEGACY_REGISTRY_GROWTH", REGISTRY_REL, 0,
            f"nova rota manual no registry legado: {route_id}; use OpenAPI + Action Catalog",
        ))

    for route_id in sorted(set(new_state) & set(old_state)):
        old_fields = old_state[route_id]
        new_fields = new_state[route_id]
        for field, new_values in sorted(new_fields.items()):
            additions = new_values - old_fields.get(field, set())
            if additions:
                findings.append(Violation(
                    "LEGACY_REGISTRY_GROWTH", REGISTRY_REL, 0,
                    f"{route_id}.{field} adicionou metadata técnica {sorted(additions)!r}; não duplicar OpenAPI no registry",
                ))
    return findings


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def timeout_is_explicit(call: ast.Call) -> bool:
    for kw in call.keywords:
        if kw.arg == "timeout":
            return not (isinstance(kw.value, ast.Constant) and kw.value.value is None)
    return False


def source_has_httpx_bare_import(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "httpx":
            for alias in node.names:
                local = alias.asname or alias.name
                if local == name and alias.name in HTTPX_BARE_CONSTRUCTORS:
                    return True
    return False


def node_touches_added(node: ast.AST, added: set[int]) -> bool:
    start = getattr(node, "lineno", 0) or 0
    end = getattr(node, "end_lineno", start) or start
    return any(line in added for line in range(start, end + 1))


def literal_methods(node: ast.AST) -> set[str]:
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return {str(v.value).upper() for v in node.elts if isinstance(v, ast.Constant) and isinstance(v.value, str)}
    if isinstance(node, ast.Constant) and node.value is None:
        return {"*"}
    return set()


def scan_python_http(path: str, added: set[int]) -> list[Violation]:
    file_path = ROOT / path
    if not file_path.is_file() or file_path.suffix != ".py" or not added:
        return []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    findings: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node_touches_added(node, added):
            continue
        name = dotted_name(node.func)
        is_http = name in HTTP_DIRECT_CALLS or (
            name in HTTPX_BARE_CONSTRUCTORS and source_has_httpx_bare_import(tree, name)
        )
        if is_http and not timeout_is_explicit(node):
            findings.append(Violation(
                "HTTP_TIMEOUT_REQUIRED", path, node.lineno,
                f"{name} sem timeout explícito (ou timeout=None)",
            ))

        if name.endswith("Retry") or name == "Retry":
            for kw in node.keywords:
                if kw.arg != "allowed_methods":
                    continue
                methods = literal_methods(kw.value)
                unsafe = WRITE_METHODS if "*" in methods else (methods & WRITE_METHODS)
                if unsafe:
                    findings.append(Violation(
                        "UNSAFE_WRITE_RETRY", path, node.lineno,
                        f"Retry permite métodos de escrita {sorted(unsafe)}; exigir idempotência/contrato explícito",
                    ))
    return findings


def sensitive_identifier(name: str) -> bool:
    lowered = name.lower()
    if lowered.endswith(SAFE_SENSITIVE_SUFFIXES):
        return False
    return bool(SENSITIVE_ID_RE.search(lowered))


def logging_call_has_secret(call: ast.Call, source: str) -> bool:
    name = dotted_name(call.func)
    is_log = name == "print" or name.rsplit(".", 1)[-1] in {"debug", "info", "warning", "warn", "error", "exception", "critical"}
    if not is_log:
        return False
    segment = ast.get_source_segment(source, call) or ""
    if re.search(r"\b(redact|mask|sanitize|scrub)\s*\(", segment, re.IGNORECASE):
        return False
    for node in ast.walk(call):
        if isinstance(node, ast.Name) and sensitive_identifier(node.id):
            return True
        if isinstance(node, ast.Attribute) and sensitive_identifier(node.attr):
            return True
    return False


def scan_python_secret_logs(path: str, added: set[int]) -> list[Violation]:
    file_path = ROOT / path
    if not file_path.is_file() or file_path.suffix != ".py" or not added:
        return []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []
    findings: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node_touches_added(node, added) and logging_call_has_secret(node, source):
            findings.append(Violation(
                "SECRET_IN_LOG", path, node.lineno,
                "logger/print recebe variável com nome sensível sem redaction explícita",
            ))
    return findings


def production_secret_scan_allowed(path: str) -> bool:
    normalized = f"/{path}"
    if any(part in normalized for part in SKIP_SECRET_PARTS):
        return False
    if path.startswith("scripts/ci/audit_architecture_phase3.py"):
        return False
    suffix = Path(path).suffix.lower()
    return suffix in PRODUCTION_EXTENSIONS or Path(path).name.startswith(".env")


def scan_secret_lines(path: str, lines: dict[int, str]) -> list[Violation]:
    if not production_secret_scan_allowed(path):
        return []
    findings: list[Violation] = []
    for line_no, line in lines.items():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        if EMBEDDED_CREDENTIAL_URL_RE.search(line):
            findings.append(Violation("SECRET_LITERAL", path, line_no, "URL contém credencial embutida"))
        if PRIVATE_KEY_RE.search(line):
            findings.append(Violation("SECRET_LITERAL", path, line_no, "chave privada literal adicionada"))
        match = SECRET_ASSIGN_RE.search(line)
        if match:
            value = match.group(2).lower()
            if not any(marker in value for marker in PLACEHOLDER_TOKENS):
                findings.append(Violation(
                    "SECRET_LITERAL", path, line_no,
                    f"valor literal para campo sensível {match.group(1)!r}",
                ))
        if Path(path).suffix.lower() in {".js", ".jsx", ".ts", ".tsx"} and JS_LOG_SECRET_RE.search(line):
            if not re.search(r"\b(redact|mask|sanitize|scrub)\s*\(", line, re.IGNORECASE):
                findings.append(Violation("SECRET_IN_LOG", path, line_no, "console log contém referência sensível sem redaction"))
    return findings


def load_exceptions() -> tuple[set[tuple[str, str, str]], list[str]]:
    if not EXCEPTIONS_PATH.is_file():
        return set(), []
    try:
        payload = json.loads(EXCEPTIONS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return set(), [f"exceptions JSON inválido: {exc}"]
    entries = payload.get("exceptions") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return set(), ["exceptions deve ser uma lista"]

    allowed: set[tuple[str, str, str]] = set()
    errors: list[str] = []
    today = dt.date.today()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"exceptions[{index}] inválida")
            continue
        rule = str(entry.get("rule") or "").strip()
        path = str(entry.get("path") or "").strip()
        fingerprint = str(entry.get("fingerprint") or "").strip()
        reason = str(entry.get("reason") or "").strip()
        owner = str(entry.get("owner") or "").strip()
        review_by = str(entry.get("reviewBy") or "").strip()
        if not rule or not path or not fingerprint:
            errors.append(f"exceptions[{index}] exige rule/path/fingerprint")
            continue
        if len(reason) < 20 or not owner:
            errors.append(f"exceptions[{index}] exige owner e reason >= 20 caracteres")
            continue
        try:
            review_date = dt.date.fromisoformat(review_by)
        except ValueError:
            errors.append(f"exceptions[{index}].reviewBy deve ser YYYY-MM-DD")
            continue
        if review_date < today:
            errors.append(f"exceptions[{index}] expirou em {review_by}")
            continue
        allowed.add((rule, path, fingerprint))
    return allowed, errors


def apply_exceptions(findings: Iterable[Violation], allowed: set[tuple[str, str, str]]) -> tuple[list[Violation], list[Violation]]:
    blocking: list[Violation] = []
    excepted: list[Violation] = []
    for finding in findings:
        key = (finding.rule, finding.path, finding.fingerprint)
        (excepted if key in allowed else blocking).append(finding)
    return blocking, excepted


def semantic_debt_path_allowed(path: str) -> bool:
    normalized = path.replace("\\", "/")
    padded = f"/{normalized}/"
    if any(part in padded for part in SEMANTIC_DEBT_SKIP_PARTS):
        # Keep content/assistant JSON in scope even under unusual layouts.
        if "/app/content/" in normalized and normalized.endswith(".json"):
            return True
        return False
    if not (
        normalized.startswith("minha-delpi-ai-api/app/")
        or normalized.startswith("minha-delpi-ai-api/scripts/")
    ):
        return False
    return True


def scan_semantic_substitute_lines(path: str, lines: dict[int, str]) -> list[Violation]:
    """Detect semantic substitutes of legacy path/endpoint authority.

    Does not flag generic reads of ``action.path`` for HTTP execution.
    """
    if not semantic_debt_path_allowed(path):
        return []
    findings: list[Violation] = []
    for line_no, line in lines.items():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        if SEMANTIC_HTTP_PATH_NEGATIVE_RE.search(line) and not (
            SEMANTIC_DOMAIN_RULES_RE.search(line)
            or SEMANTIC_CONTENT_LATERAL_KEYS_RE.search(line)
            or SEMANTIC_SMOKE_CRED_DEFAULT_RE.search(line)
        ):
            # Pure technical path read for execution/observability.
            continue
        if SEMANTIC_DOMAIN_RULES_RE.search(line):
            findings.append(Violation(
                "SEMANTIC_PATH_DOMAIN_MAP",
                path,
                line_no,
                f"path→domain map substitute (_DOMAIN_RULES): {normalize(line)}",
            ))
        if SEMANTIC_CONTENT_LATERAL_KEYS_RE.search(line):
            findings.append(Violation(
                "SEMANTIC_CONTENT_LATERAL_PATH_KEY",
                path,
                line_no,
                f"lateral path key reintroduced in content/runtime: {normalize(line)}",
            ))
        if SEMANTIC_PATH_STRATEGY_CLASS_RE.search(line):
            findings.append(Violation(
                "SEMANTIC_ENDPOINT_PARAMETER_STRATEGY",
                path,
                line_no,
                f"endpoint→parameterStrategy authority class: {normalize(line)}",
            ))
        if (
            path.endswith("parameter_strategy_inference_service.py")
            and SEMANTIC_PATH_STRATEGY_BRANCH_RE.search(line)
            and ("if " in line or "or " in line)
        ):
            findings.append(Violation(
                "SEMANTIC_ENDPOINT_PARAMETER_STRATEGY",
                path,
                line_no,
                f"path/operationId→strategy branch: {normalize(line)}",
            ))
        if SEMANTIC_ROUTE_SEGMENT_CLASS_RE.search(line):
            findings.append(Violation(
                "SEMANTIC_PATH_ROUTE_SEGMENT",
                path,
                line_no,
                f"path/operationId→routeSegment authority class: {normalize(line)}",
            ))
        if (
            path.endswith("route_segment_inference_service.py")
            and SEMANTIC_ROUTE_SEGMENT_PATH_TAIL_RE.search(line)
        ):
            findings.append(Violation(
                "SEMANTIC_PATH_ROUTE_SEGMENT",
                path,
                line_no,
                f"path-tail/operationId continuity coupling: {normalize(line)}",
            ))
        if SEMANTIC_SMOKE_CRED_DEFAULT_RE.search(line):
            findings.append(Violation(
                "SEMANTIC_SMOKE_CREDENTIAL_DEFAULT",
                path,
                line_no,
                f"smoke credential default literal: {normalize(line)}",
            ))
    return findings


def scan_registry_operation_id_catalog(path: str = REGISTRY_REL) -> list[Violation]:
    """Flag manual operationIds lists used as routing technical catalog."""
    file_path = ROOT / path
    if not file_path.is_file():
        return []
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [Violation("SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG", path, 0, f"registry JSON inválido: {exc}")]
    routes = payload.get("routes") if isinstance(payload, dict) else None
    if not isinstance(routes, list):
        return []
    findings: list[Violation] = []
    for item in routes:
        if not isinstance(item, dict):
            continue
        route_id = str(item.get("id") or "").strip() or "<unknown>"
        route_spec = item.get("route") if isinstance(item.get("route"), dict) else {}
        ids = route_spec.get("operationIds")
        if isinstance(ids, list) and any(str(x).strip() for x in ids):
            findings.append(Violation(
                "SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG",
                path,
                0,
                f"route {route_id} teaches actions via manual operationIds={ids!r}",
            ))
    return findings


def iter_semantic_debt_files() -> Iterable[Path]:
    roots = [
        ROOT / "minha-delpi-ai-api" / "app",
        ROOT / "minha-delpi-ai-api" / "scripts",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if not semantic_debt_path_allowed(rel):
                continue
            if path.suffix.lower() not in {".py", ".json", ".ts", ".tsx", ".js", ".sh"}:
                continue
            yield path


def scan_semantic_debt_workspace() -> list[Violation]:
    findings: list[Violation] = []
    for path in iter_semantic_debt_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = {i: line for i, line in enumerate(text.splitlines(), start=1)}
        findings.extend(scan_semantic_substitute_lines(rel, lines))
    findings.extend(scan_registry_operation_id_catalog())
    return findings


def audit(base: str) -> tuple[list[Violation], list[Violation], list[str]]:
    changes = added_lines(base)
    findings: list[Violation] = []
    for path, lines in sorted(changes.items()):
        findings.extend(scan_chat_route_hardcode(path, lines))
        findings.extend(scan_secret_lines(path, lines))
        findings.extend(scan_semantic_substitute_lines(path, lines))
        added = set(lines)
        findings.extend(scan_python_http(path, added))
        findings.extend(scan_python_secret_logs(path, added))
    if REGISTRY_REL in changes:
        findings.extend(scan_registry_growth(base))
        # New/changed registry with operationIds lists also trip semantic debt.
        findings.extend(scan_registry_operation_id_catalog())

    allowed, exception_errors = load_exceptions()
    blocking, excepted = apply_exceptions(findings, allowed)
    return blocking, excepted, exception_errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Commit base para comparação; fallback PHASE3_BASE_SHA/HEAD^")
    parser.add_argument("--check", action="store_true", help="Exit 1 em violação bloqueante")
    parser.add_argument(
        "--check-semantic-debt",
        action="store_true",
        help="E11.S1: scan full-tree de substitutos semânticos (esperado vermelho até cleanup)",
    )
    args = parser.parse_args()

    if args.check_semantic_debt:
        findings = scan_semantic_debt_workspace()
        print("Architecture Phase 3 — semantic substitute debt (full tree)")
        by_rule: dict[str, int] = {}
        for item in findings:
            by_rule[item.rule] = by_rule.get(item.rule, 0) + 1
            print(f"  [DEBT] {item.rule} {item.path}:{item.line} {item.message} fingerprint={item.fingerprint}")
        print(f"totals_by_rule={json.dumps(by_rule, sort_keys=True)}")
        print(f"total={len(findings)}")
        if findings:
            print("[FAIL] semantic substitute debt presente (gate vermelho no baseline até E11 cleanup).")
            return 1
        print("[OK] sem substitutos semânticos detectados.")
        return 0

    try:
        base = resolve_base(args.base)
        blocking, excepted, exception_errors = audit(base)
    except RuntimeError as exc:
        print(f"[FAIL] architecture phase3: {exc}", file=sys.stderr)
        return 2

    print(f"Architecture Phase 3 gate — base {base[:12]} → HEAD")
    for message in exception_errors:
        print(f"  [EXCEPTION-ERROR] {message}")
    for item in excepted:
        print(f"  [EXCEPTED] {item.rule} {item.path}:{item.line} {item.message} fingerprint={item.fingerprint}")
    for item in blocking:
        print(f"  [FAIL] {item.rule} {item.path}:{item.line} {item.message} fingerprint={item.fingerprint}")

    if not blocking and not exception_errors:
        print("[OK] Nenhuma nova regressão arquitetural da Fase 3.")
        return 0

    print("\nPara exceção temporária, registre fingerprint + owner + reason + reviewBy em architecture_phase3_exceptions.json.", file=sys.stderr)
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
