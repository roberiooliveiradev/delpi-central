#!/usr/bin/env python3
"""Auditoria incremental de contratos OpenAPI e rotas FastAPI.

Objetivos:
- OpenAPI versionado: operationId obrigatório e único.
- OpenAPI versionado: remoção de operação ou troca de operationId exige classificação
  BREAKING explícita e vinculada à versão-base do contrato.
- FastAPI: rota HTTP nova/alterada deve declarar operation_id literal e não pode
  introduzir duplicidade dentro do mesmo bounded context de API.

O scanner é diff-aware: dívida histórica não bloqueia o CI; regressões novas sim.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - coberto no CI pela instalação explícita
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
OPENAPI_SUFFIXES = {".json", ".yaml", ".yml"}
ALLOWED_CHANGE_CLASSES = {"ADDITIVE", "BEHAVIORAL", "DEPRECATED", "BREAKING"}
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
class OpenApiOperation:
    path: str
    method: str
    operation_id: str | None


@dataclass(frozen=True)
class FastApiRoute:
    path: str
    method: str
    operation_id: str | None
    line: int
    end_line: int


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
    candidate = (explicit or os.getenv("OPENAPI_CONTRACT_BASE_SHA") or "").strip()
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


def changed_paths(base: str) -> list[tuple[str, list[str]]]:
    raw = git("diff", "--name-status", "-M", f"{base}..HEAD", "--", ".")
    rows: list[tuple[str, list[str]]] = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            rows.append((parts[0], parts[1:]))
    return rows


def added_lines(base: str) -> dict[str, set[int]]:
    diff = git("diff", "--unified=0", "--no-color", f"{base}..HEAD", "--", ".")
    files: dict[str, set[int]] = {}
    current: str | None = None
    new_line: int | None = None

    import re

    hunk_re = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            current = raw[6:]
            files.setdefault(current, set())
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
            files[current].add(new_line)
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        else:
            new_line += 1
    return files


def read_at(ref: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout if result.returncode == 0 else None


def load_document(path: str, text: str) -> Any:
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML é obrigatório para auditar OpenAPI YAML")
        return yaml.safe_load(text)
    raise ValueError(f"formato não suportado: {path}")


def is_openapi_document(document: Any) -> bool:
    return isinstance(document, dict) and bool(document.get("openapi") or document.get("swagger")) and isinstance(
        document.get("paths"), dict
    )


def iter_openapi_operations(document: dict[str, Any]) -> Iterable[OpenApiOperation]:
    for path, path_item in (document.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_lower = str(method).lower()
            if method_lower not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id.strip():
                operation_id = None
            yield OpenApiOperation(str(path), method_lower, operation_id)


def contract_change_metadata(document: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    info = document.get("info") if isinstance(document.get("info"), dict) else {}
    change_class = info.get("x-delpi-contract-change") or document.get("x-delpi-contract-change")
    from_version = info.get("x-delpi-contract-change-from") or document.get("x-delpi-contract-change-from")
    reason = info.get("x-delpi-contract-change-reason") or document.get("x-delpi-contract-change-reason")
    version = info.get("version") if isinstance(info.get("version"), str) else None
    return (
        str(change_class).upper() if isinstance(change_class, str) and change_class.strip() else None,
        str(from_version).strip() if isinstance(from_version, str) and from_version.strip() else None,
        str(reason).strip() if isinstance(reason, str) and reason.strip() else None,
        version,
    )


def validate_openapi_document(
    path: str,
    current: dict[str, Any],
    base: dict[str, Any] | None = None,
) -> list[Violation]:
    findings: list[Violation] = []
    operations = list(iter_openapi_operations(current))

    by_id: dict[str, list[OpenApiOperation]] = {}
    for operation in operations:
        if operation.operation_id is None:
            findings.append(
                Violation(
                    "OPENAPI_OPERATION_ID_REQUIRED",
                    path,
                    0,
                    f"{operation.method.upper()} {operation.path} não declara operationId explícito",
                )
            )
            continue
        by_id.setdefault(operation.operation_id, []).append(operation)

    for operation_id, duplicates in sorted(by_id.items()):
        if len(duplicates) <= 1:
            continue
        locations = ", ".join(f"{item.method.upper()} {item.path}" for item in duplicates)
        findings.append(
            Violation(
                "OPENAPI_OPERATION_ID_DUPLICATE",
                path,
                0,
                f"operationId '{operation_id}' aparece em múltiplas operações: {locations}",
            )
        )

    change_class, from_version, reason, current_version = contract_change_metadata(current)
    if change_class and change_class not in ALLOWED_CHANGE_CLASSES:
        findings.append(
            Violation(
                "OPENAPI_CHANGE_CLASS_INVALID",
                path,
                0,
                f"x-delpi-contract-change inválido: {change_class}",
            )
        )

    if base is None:
        return findings

    base_operations = {(item.path, item.method): item for item in iter_openapi_operations(base)}
    current_operations = {(item.path, item.method): item for item in operations}
    breaking_reasons: list[str] = []

    for key, previous in sorted(base_operations.items()):
        current_operation = current_operations.get(key)
        if current_operation is None:
            breaking_reasons.append(f"operação removida: {previous.method.upper()} {previous.path}")
            continue
        if previous.operation_id and current_operation.operation_id != previous.operation_id:
            breaking_reasons.append(
                f"operationId alterado em {previous.method.upper()} {previous.path}: "
                f"{previous.operation_id} -> {current_operation.operation_id or '<ausente>'}"
            )

    if not breaking_reasons:
        return findings

    base_info = base.get("info") if isinstance(base.get("info"), dict) else {}
    base_version = base_info.get("version") if isinstance(base_info.get("version"), str) else None
    classified = (
        change_class == "BREAKING"
        and bool(reason)
        and bool(base_version)
        and from_version == base_version
        and bool(current_version)
        and current_version != base_version
    )
    if not classified:
        details = "; ".join(breaking_reasons)
        findings.append(
            Violation(
                "OPENAPI_BREAKING_UNCLASSIFIED",
                path,
                0,
                "mudança breaking detectada sem classificação vinculada à versão-base; "
                "defina info.x-delpi-contract-change=BREAKING, "
                "info.x-delpi-contract-change-from=<versão-base>, altere info.version e informe reason. "
                f"Detectado: {details}",
            )
        )
    return findings


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
        return node.value.strip()
    return None


def fastapi_routes_from_source(source: str) -> list[FastApiRoute]:
    tree = ast.parse(source)
    routes: list[FastApiRoute] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.lower()
            if method not in HTTP_METHODS or not decorator.args:
                continue
            route_path = _literal_string(decorator.args[0])
            if not route_path or not route_path.startswith("/"):
                continue
            operation_id: str | None = None
            for keyword in decorator.keywords:
                if keyword.arg == "operation_id":
                    operation_id = _literal_string(keyword.value)
                    break
            routes.append(
                FastApiRoute(
                    path=route_path,
                    method=method,
                    operation_id=operation_id,
                    line=getattr(decorator, "lineno", getattr(node, "lineno", 0)),
                    end_line=getattr(decorator, "end_lineno", getattr(decorator, "lineno", 0)),
                )
            )
    return routes


def is_production_api_source(path: str) -> bool:
    candidate = Path(path)
    if candidate.suffix.lower() != ".py":
        return False
    parts = candidate.parts
    if not parts:
        return False
    root = parts[0]
    if root != "api-delpi" and not root.endswith("-api"):
        return False
    return not any(part in SKIP_SOURCE_PARTS for part in parts[1:])


def route_touched(route: FastApiRoute, changed_line_numbers: set[int]) -> bool:
    return any(route.line <= line <= max(route.line, route.end_line) for line in changed_line_numbers)


def scan_changed_fastapi_file(path: str, source: str, changed_line_numbers: set[int]) -> list[Violation]:
    if not is_production_api_source(path):
        return []
    findings: list[Violation] = []
    try:
        routes = fastapi_routes_from_source(source)
    except SyntaxError as exc:
        return [Violation("FASTAPI_ROUTE_PARSE_ERROR", path, exc.lineno or 0, str(exc))]

    for route in routes:
        if not route_touched(route, changed_line_numbers):
            continue
        if route.operation_id is None:
            findings.append(
                Violation(
                    "FASTAPI_OPERATION_ID_REQUIRED",
                    path,
                    route.line,
                    f"{route.method.upper()} {route.path} nova/alterada deve declarar operation_id literal",
                )
            )
    return findings


def api_root_for_path(path: str) -> str | None:
    parts = Path(path).parts
    if not parts:
        return None
    root = parts[0]
    return root if root == "api-delpi" or root.endswith("-api") else None


def scan_fastapi_duplicates(changed_line_map: dict[str, set[int]]) -> list[Violation]:
    roots = {
        root
        for path, lines in changed_line_map.items()
        if lines and is_production_api_source(path) and (root := api_root_for_path(path))
    }
    findings: list[Violation] = []

    for root in sorted(roots):
        occurrences: dict[str, list[tuple[str, FastApiRoute, bool]]] = {}
        root_path = ROOT / root
        if not root_path.exists():
            continue
        for source_path in root_path.rglob("*.py"):
            rel = source_path.relative_to(ROOT).as_posix()
            if not is_production_api_source(rel):
                continue
            try:
                routes = fastapi_routes_from_source(source_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue
            changed_lines_for_file = changed_line_map.get(rel, set())
            for route in routes:
                if not route.operation_id:
                    continue
                occurrences.setdefault(route.operation_id, []).append(
                    (rel, route, route_touched(route, changed_lines_for_file))
                )

        for operation_id, items in sorted(occurrences.items()):
            if len(items) <= 1 or not any(changed for _, _, changed in items):
                continue
            locations = ", ".join(
                f"{file_path}:{route.line} {route.method.upper()} {route.path}"
                for file_path, route, _ in items
            )
            changed_path, changed_route, _ = next(item for item in items if item[2])
            findings.append(
                Violation(
                    "FASTAPI_OPERATION_ID_DUPLICATE",
                    changed_path,
                    changed_route.line,
                    f"operation_id '{operation_id}' duplicado no bounded context {root}: {locations}",
                )
            )
    return findings


def scan_versioned_openapi(base: str) -> list[Violation]:
    findings: list[Violation] = []
    for status, paths in changed_paths(base):
        kind = status[:1]
        if kind == "D":
            continue
        current_path = paths[-1]
        if Path(current_path).suffix.lower() not in OPENAPI_SUFFIXES:
            continue
        current_text = (ROOT / current_path).read_text(encoding="utf-8") if (ROOT / current_path).exists() else None
        if current_text is None:
            continue
        try:
            current = load_document(current_path, current_text)
        except (json.JSONDecodeError, RuntimeError, ValueError, yaml.YAMLError if yaml else Exception) as exc:
            # Arquivo JSON/YAML comum não deve falhar o gate OpenAPI.
            if "openapi" in current_text[:500].lower() or "swagger" in current_text[:500].lower():
                findings.append(Violation("OPENAPI_PARSE_ERROR", current_path, 0, str(exc)))
            continue
        if not is_openapi_document(current):
            continue

        base_document: dict[str, Any] | None = None
        previous_path = paths[0]
        if kind != "A":
            previous_text = read_at(base, previous_path)
            if previous_text:
                try:
                    previous = load_document(previous_path, previous_text)
                    if is_openapi_document(previous):
                        base_document = previous
                except Exception:
                    base_document = None
        findings.extend(validate_openapi_document(current_path, current, base_document))
    return findings


def collect(base: str) -> list[Violation]:
    findings = scan_versioned_openapi(base)
    changed_line_map = added_lines(base)
    for path, lines in changed_line_map.items():
        if not lines or not is_production_api_source(path):
            continue
        source_path = ROOT / path
        if not source_path.exists():
            continue
        try:
            source = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings.extend(scan_changed_fastapi_file(path, source, lines))
    findings.extend(scan_fastapi_duplicates(changed_line_map))
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

    print("OpenAPI contract guardrails")
    print(f"- base: {base}")
    print(f"- findings: {len(findings)}")
    for finding in findings:
        print(f"- {finding.format()}")

    if findings and args.check:
        print("FALHOU: regressões de contrato OpenAPI/FastAPI detectadas", file=sys.stderr)
        return 1

    print("OK: nenhuma nova regressão de contrato detectada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
