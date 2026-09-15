#!/usr/bin/env python3
"""Gate de compatibilidade GPT Builder em artefatos GPT Actions versionados.

Escopo: ``*/docs/gpt-actions/openapi-gpt-actions.json`` (full-tree).

Foca a classe de falha já observada (TÉO / VISTA): schema genérico
impossibilita o modelo de construir o tool call. Não percorre envelopes
de resposta nem bags nested com ``additionalProperties: true`` — esses
casos atuais gerariam falso positivo sem provar o incidente.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_NAME = "openapi-gpt-actions.json"
ARTIFACT_PARENT = "gpt-actions"
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
}
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
WRITE_METHODS = {"post", "put", "patch"}
SEMANTIC_OBJECT_KEYS = {
    "target",
    "context",
    "operation",
    "configuration",
    "payload",
    "filters",
}
SEMANTIC_ARRAY_KEYS = {"ops", "commands", "operations", "changes"}


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    line: int
    message: str

    def format(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"[{self.rule}] {where} — {self.message}"


def discover_artifacts(root: Path) -> list[Path]:
    found: list[Path] = []
    for api_root in root.iterdir():
        if not api_root.is_dir() or api_root.name in SKIP_DIR_NAMES:
            continue
        candidate = api_root / "docs" / ARTIFACT_PARENT / ARTIFACT_NAME
        if candidate.is_file():
            found.append(candidate)
    return sorted(found)


def load_document(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: documento OpenAPI deve ser objeto JSON")
    return payload


def resolve_ref(document: dict[str, Any], schema: Any) -> Any:
    if not isinstance(schema, dict):
        return schema
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return schema
    node: Any = document
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            return schema
        node = node[part]
    return node


def is_bare_object(schema: Any) -> bool:
    if not isinstance(schema, dict) or "$ref" in schema:
        return False
    return schema.get("type") == "object" and "properties" not in schema


def is_untyped_array_item(items: Any) -> bool:
    if not isinstance(items, dict):
        return True
    if "$ref" in items or "oneOf" in items or "anyOf" in items:
        return False
    if items.get("type") == "object" and "properties" not in items:
        return True
    return False


def json_media(operation: dict[str, Any]) -> dict[str, Any] | None:
    request_body = operation.get("requestBody")
    if not isinstance(request_body, dict):
        return None
    content = request_body.get("content")
    if not isinstance(content, dict):
        return {}
    media = content.get("application/json")
    return media if isinstance(media, dict) else {}


def is_fake_empty_body(media: dict[str, Any]) -> bool:
    schema = media.get("schema")
    if not isinstance(schema, dict) or "$ref" in schema:
        return False
    example = media.get("example")
    return (
        schema.get("type") == "object"
        and not schema.get("properties")
        and schema.get("additionalProperties") is False
        and example == {}
    )


def iter_operations(document: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    found: list[tuple[str, str, dict[str, Any]]] = []
    paths = document.get("paths")
    if not isinstance(paths, dict):
        return found
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            found.append((str(path), method.lower(), operation))
    return found


def validate_document(rel_path: str, document: dict[str, Any]) -> list[Violation]:
    findings: list[Violation] = []
    seen_ids: dict[str, str] = {}

    for path, method, operation in iter_operations(document):
        label = f"{rel_path} {method.upper()} {path}"
        operation_id = operation.get("operationId")
        if not isinstance(operation_id, str) or not operation_id.strip():
            findings.append(
                Violation(
                    "GPT_ACTION_OPERATION_ID_MISSING",
                    rel_path,
                    0,
                    f"{method.upper()} {path} sem operationId explícito",
                )
            )
        else:
            previous = seen_ids.get(operation_id)
            if previous:
                findings.append(
                    Violation(
                        "GPT_ACTION_OPERATION_ID_DUPLICATE",
                        rel_path,
                        0,
                        f"operationId {operation_id!r} duplicado ({previous} e {label})",
                    )
                )
            else:
                seen_ids[operation_id] = label

        media = json_media(operation)
        if media is None:
            continue
        if "schema" not in media:
            findings.append(
                Violation(
                    "GPT_ACTION_BODY_WITHOUT_SCHEMA",
                    rel_path,
                    0,
                    f"{label} declara requestBody sem schema JSON",
                )
            )
            continue

        if is_fake_empty_body(media):
            findings.append(
                Violation(
                    "GPT_ACTION_FAKE_EMPTY_BODY",
                    rel_path,
                    0,
                    f"{label} inventa requestBody vazio incompatível com o Builder",
                )
            )

        schema = resolve_ref(document, media.get("schema"))
        if is_bare_object(media.get("schema")) or is_bare_object(schema):
            findings.append(
                Violation(
                    "GPT_ACTION_OBJECT_WITHOUT_PROPERTIES",
                    rel_path,
                    0,
                    f"{label} usa type=object sem properties no requestBody",
                )
            )

        properties = schema.get("properties") if isinstance(schema, dict) else None
        if isinstance(properties, dict):
            for key, prop in properties.items():
                resolved = resolve_ref(document, prop)
                if key in SEMANTIC_OBJECT_KEYS and (
                    is_bare_object(prop) or is_bare_object(resolved)
                ):
                    findings.append(
                        Violation(
                            "GPT_ACTION_OBJECT_WITHOUT_PROPERTIES",
                            rel_path,
                            0,
                            f"{label} campo semântico {key!r} é object sem properties",
                        )
                    )
                items = None
                if isinstance(resolved, dict) and resolved.get("type") == "array":
                    items = resolved.get("items")
                elif isinstance(prop, dict) and prop.get("type") == "array":
                    items = prop.get("items")
                if key in SEMANTIC_ARRAY_KEYS and is_untyped_array_item(items):
                    findings.append(
                        Violation(
                            "GPT_ACTION_UNTYPED_ARRAY_ITEM",
                            rel_path,
                            0,
                            f"{label} array semântico {key!r} sem shape de item",
                        )
                    )

        if method in WRITE_METHODS:
            has_example = "example" in media or "examples" in media
            exempt = operation.get("x-delpi-gpt-example-exempt")
            if not has_example and not exempt:
                findings.append(
                    Violation(
                        "GPT_ACTION_BODY_WITHOUT_EXAMPLE",
                        rel_path,
                        0,
                        f"{label} write/PREPARE/ACT sem example tipado",
                    )
                )

    return findings


def audit_repository(root: Path) -> list[Violation]:
    findings: list[Violation] = []
    for artifact in discover_artifacts(root):
        rel = str(artifact.relative_to(root)).replace("\\", "/")
        try:
            document = load_document(artifact)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            findings.append(
                Violation(
                    "GPT_ACTION_BODY_WITHOUT_SCHEMA",
                    rel,
                    0,
                    f"artefato OpenAPI inválido: {exc}",
                )
            )
            continue
        findings.extend(validate_document(rel, document))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita OpenAPI GPT Actions versionado")
    parser.add_argument("--check", action="store_true", help="Falhar se houver violações")
    args = parser.parse_args()

    findings = audit_repository(ROOT)
    if not args.check:
        for item in findings:
            print(item.format())
        print(f"{len(findings)} finding(s)")
        return 0

    if findings:
        print(f"FALHOU: {len(findings)} violação(ões) GPT Actions OpenAPI", file=sys.stderr)
        for item in findings:
            print(f"- {item.format()}", file=sys.stderr)
        return 1

    print("OK: artefatos GPT Actions compatíveis com o Builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
