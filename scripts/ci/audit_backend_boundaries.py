#!/usr/bin/env python3
"""Gate diff-aware de boundaries entre APIs Python da Minha DELPI.

Regra: código de uma API não importa diretamente o package interno exclusivo de outra
API irmã. Integração entre bounded contexts deve ocorrer por contrato HTTP/evento,
client compartilhado/gerado ou port explícito — nunca por `from sibling_app...`.

A descoberta é estrutural, sem lista manual:
- API roots: diretórios top-level `*-api` e `api-delpi`;
- package roots: packages Python imediatos (ou `src/<package>`) com `__init__.py`;
- package com o mesmo nome em mais de uma API é ambíguo e não vira gate automático.

O scanner é diff-aware: apenas imports introduzidos/alterados no arquivo atual podem
falhar, enquanto dívida histórica não torna o repositório inteiro vermelho.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_ROOTS = {"node_modules", ".git", ".venv", "venv"}
SKIP_PACKAGE_DIRS = {
    "tests",
    "test",
    "docs",
    "migrations",
    "scripts",
    "fixtures",
    "alembic",
    "build",
    "dist",
}
SKIP_SOURCE_PARTS = {"tests", "test", "fixtures", "docs", ".cursor", "scripts", "migrations"}


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
class ImportRef:
    package: str
    line: int


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
    candidate = (explicit or os.getenv("BACKEND_BOUNDARIES_BASE_SHA") or "").strip()
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
    diff = git("diff", "--unified=0", "--no-color", f"{base}..HEAD", "--", ".")
    files: dict[str, set[int]] = {}
    current: str | None = None
    new_line: int | None = None
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

    return {path: lines for path, lines in files.items() if lines}


def discover_api_roots(root: Path = ROOT) -> list[Path]:
    result: list[Path] = []
    if not root.exists():
        return result
    for child in root.iterdir():
        if not child.is_dir() or child.name in SKIP_ROOTS:
            continue
        if child.name == "api-delpi" or child.name.endswith("-api"):
            result.append(child)
    return sorted(result, key=lambda item: item.name)


def _python_package_dirs(api_root: Path) -> set[Path]:
    candidates: set[Path] = set()
    for child in api_root.iterdir():
        if child.is_dir() and child.name not in SKIP_PACKAGE_DIRS and (child / "__init__.py").exists():
            candidates.add(child)

    src = api_root / "src"
    if src.is_dir():
        for child in src.iterdir():
            if child.is_dir() and child.name not in SKIP_PACKAGE_DIRS and (child / "__init__.py").exists():
                candidates.add(child)
    return candidates


def discover_unique_package_owners(root: Path = ROOT) -> dict[str, str]:
    owners: dict[str, set[str]] = defaultdict(set)
    for api_root in discover_api_roots(root):
        for package_dir in _python_package_dirs(api_root):
            owners[package_dir.name].add(api_root.name)
    return {
        package: next(iter(api_owners))
        for package, api_owners in owners.items()
        if len(api_owners) == 1
    }


def source_api_root(path: str, root: Path = ROOT) -> str | None:
    parts = Path(path).parts
    if not parts:
        return None
    first = parts[0]
    candidate = root / first
    if not candidate.is_dir():
        return None
    return first if first == "api-delpi" or first.endswith("-api") else None


def is_production_python(path: str, root: Path = ROOT) -> bool:
    candidate = Path(path)
    if candidate.suffix.lower() != ".py":
        return False
    if source_api_root(path, root) is None:
        return False
    return not any(part in SKIP_SOURCE_PARTS for part in candidate.parts[1:])


def imports_from_source(source: str) -> list[ImportRef]:
    tree = ast.parse(source)
    refs: list[ImportRef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                package = alias.name.split(".", 1)[0]
                if package:
                    refs.append(ImportRef(package, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module:
                continue
            package = node.module.split(".", 1)[0]
            if package:
                refs.append(ImportRef(package, node.lineno))
    return refs


def scan_source(
    path: str,
    source: str,
    changed_lines: set[int],
    package_owners: dict[str, str],
    root: Path = ROOT,
) -> list[Violation]:
    if not is_production_python(path, root):
        return []
    current_owner = source_api_root(path, root)
    if current_owner is None:
        return []
    try:
        refs = imports_from_source(source)
    except SyntaxError as exc:
        return [Violation("BACKEND_BOUNDARY_PARSE_ERROR", path, exc.lineno or 0, str(exc))]

    findings: list[Violation] = []
    for ref in refs:
        if ref.line not in changed_lines:
            continue
        target_owner = package_owners.get(ref.package)
        if not target_owner or target_owner == current_owner:
            continue
        findings.append(
            Violation(
                "BACKEND_SIBLING_API_IMPORT",
                path,
                ref.line,
                f"{current_owner} importou package interno '{ref.package}' pertencente a {target_owner}; "
                "integre por contrato HTTP/evento, client compartilhado ou port explícito",
            )
        )
    return findings


def collect(base: str) -> list[Violation]:
    package_owners = discover_unique_package_owners(ROOT)
    findings: list[Violation] = []
    for path, lines in changed_line_numbers(base).items():
        if not is_production_python(path, ROOT):
            continue
        source_path = ROOT / path
        if not source_path.exists():
            continue
        try:
            source = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings.extend(scan_source(path, source, lines, package_owners, ROOT))
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

    print("Backend bounded-context guardrails")
    print(f"- base: {base}")
    print(f"- unique package owners: {len(discover_unique_package_owners(ROOT))}")
    print(f"- findings: {len(findings)}")
    for finding in findings:
        print(f"- {finding.format()}")

    if findings and args.check:
        print("FALHOU: import direto entre APIs irmãs detectado", file=sys.stderr)
        return 1

    print("OK: nenhum novo import direto entre APIs irmãs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
