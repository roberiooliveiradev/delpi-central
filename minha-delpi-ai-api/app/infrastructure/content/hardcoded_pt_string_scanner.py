"""Varredura de strings PT hardcoded em caminhos protegidos (Fase 5)."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

PROTECTED_RELATIVE_PATHS: tuple[str, ...] = (
    "app/domain/services/external_actions/presenters",
    "app/domain/services/external_actions/external_action_result_presenter.py",
    "app/application/services/external_actions",
    "app/application/services/chat_turn/chat_turn_preparation_content_service.py",
    "app/application/services/chat_tool_context_content_service.py",
    "app/application/services/chat_canvas_content_service.py",
)

PT_INDICATOR = re.compile(
    r"[áàâãéêíóôõúç]"
    r"|\b(não|nao|você|voce|consulta|produto|estoque|dados|erro|mensagem|resposta|"
    r"título|titulo|visualização|visualizacao|indicador|foram|quando|obrigatório|"
    r"obrigatorio|pergunta|resultado|encontrado|registro|filial|armazém|armazem|"
    r"lista|detalhamento|relatório|relatorio|expedição|expedicao|situação|situacao)\b",
    re.IGNORECASE,
)

TECHNICAL_STRING = re.compile(
    r"(\\[\\()?\(\?:|\[\.\*\]|\^\(|\{[a-z_]+\}|%s|%d|"
    r"^[A-Z0-9_./\-]+$|^[a-z_]+(?:\.[a-z_]+)+$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class HardcodedPtFinding:
    file: str
    line: int
    text: str

    @property
    def fingerprint(self) -> str:
        digest = hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]
        return f"{self.file}:{self.line}:{digest}"


def _collect_docstring_nodes(tree: ast.AST) -> set[int]:
    doc_nodes: set[int] = set()

    def _first_expr_constant(body: list[ast.stmt]) -> ast.Constant | None:
        if not body:
            return None

        first = body[0]

        if not isinstance(first, ast.Expr):
            return None

        value = first.value

        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value

        return None

    if isinstance(tree, ast.Module):
        node = _first_expr_constant(tree.body)

        if node is not None:
            doc_nodes.add(id(node))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = _first_expr_constant(node.body)

            if doc is not None:
                doc_nodes.add(id(doc))

    return doc_nodes


def _is_protected_file(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()

    for protected in PROTECTED_RELATIVE_PATHS:
        if protected.endswith(".py"):
            if rel == protected:
                return True
            continue

        prefix = protected.rstrip("/") + "/"
        if rel.startswith(prefix):
            return True

    return False


def _should_flag_string(text: str) -> bool:
    normalized = text.strip()

    if len(normalized) < 12:
        return False

    if not PT_INDICATOR.search(normalized):
        return False

    if TECHNICAL_STRING.search(normalized):
        return False

    if normalized.startswith(("http://", "https://", "/apps/", "/api/")):
        return False

    return True


def scan_protected_paths() -> list[HardcodedPtFinding]:
    findings: list[HardcodedPtFinding] = []

    for protected in PROTECTED_RELATIVE_PATHS:
        path = ROOT / protected

        if path.is_file():
            candidates = [path]
        else:
            candidates = sorted(path.rglob("*.py"))

        for file_path in candidates:
            if not _is_protected_file(file_path):
                continue

            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
            doc_nodes = _collect_docstring_nodes(tree)
            rel = file_path.relative_to(ROOT).as_posix()

            for node in ast.walk(tree):
                if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                    continue

                if id(node) in doc_nodes:
                    continue

                if not _should_flag_string(node.value):
                    continue

                findings.append(
                    HardcodedPtFinding(
                        file=rel,
                        line=int(node.lineno),
                        text=node.value.strip(),
                    )
                )

    findings.sort(key=lambda item: (item.file, item.line, item.text))
    return findings


def load_baseline(path: Path) -> set[str]:
    if not path.is_file():
        return set()

    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("allowedFingerprints") or [])


def save_baseline(path: Path, findings: list[HardcodedPtFinding]) -> None:
    payload = {
        "allowedFingerprints": sorted({item.fingerprint for item in findings}),
        "samples": [
            {
                "fingerprint": item.fingerprint,
                "file": item.file,
                "line": item.line,
                "text": item.text[:120],
            }
            for item in findings
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def diff_against_baseline(
    findings: list[HardcodedPtFinding],
    baseline: set[str],
) -> tuple[list[HardcodedPtFinding], list[str]]:
    current = {item.fingerprint for item in findings}
    new_items = [item for item in findings if item.fingerprint not in baseline]
    removed = sorted(baseline - current)
    return new_items, removed
