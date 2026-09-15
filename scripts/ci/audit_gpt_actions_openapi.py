#!/usr/bin/env python3
"""Gate de compatibilidade GPT Builder em artefatos GPT Actions versionados.

Escopo: ``*/docs/gpt-actions/openapi-gpt-actions.json`` (full-tree).

Percorre schemas de CONSTRUÇÃO de request (requestBody + $ref resolvido).
Respostas ficam fora deste gate.

Objetos livre-forma só passam com ``x-delpi-gpt-opaque-object: true`` e
description não vazia. Mapas tipados usam ``additionalProperties`` schema.
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
OPAQUE_EXT = "x-delpi-gpt-opaque-object"


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


def _is_object_schema(schema: dict[str, Any]) -> bool:
    if schema.get("type") == "object":
        return True
    return any(key in schema for key in ("properties", "additionalProperties"))


def _has_meaningful_properties(schema: dict[str, Any]) -> bool:
    props = schema.get("properties")
    return isinstance(props, dict) and len(props) > 0


def _typed_additional_properties(schema: dict[str, Any]) -> dict[str, Any] | None:
    additional = schema.get("additionalProperties")
    return additional if isinstance(additional, dict) else None


def _is_explicit_opaque(schema: dict[str, Any]) -> bool:
    return schema.get(OPAQUE_EXT) is True


def _walk_request_schema(
    document: dict[str, Any],
    schema: Any,
    *,
    loc: str,
    findings: list[Violation],
    rel_path: str,
    seen: set[int],
) -> None:
    resolved = resolve_ref(document, schema)
    if not isinstance(resolved, dict):
        return
    marker = id(resolved)
    if marker in seen:
        return
    seen.add(marker)

    for key in ("oneOf", "anyOf", "allOf"):
        branches = resolved.get(key)
        if not isinstance(branches, list):
            continue
        if key == "oneOf" and not branches:
            findings.append(
                Violation(
                    "GPT_ACTION_UNTYPED_ONEOF_BRANCH",
                    rel_path,
                    0,
                    f"{loc} oneOf vazio",
                )
            )
        for index, branch in enumerate(branches):
            branch_loc = f"{loc}/{key}[{index}]"
            resolved_branch = resolve_ref(document, branch)
            if not isinstance(resolved_branch, dict) or (
                resolved_branch.get("type") == "object"
                and not _has_meaningful_properties(resolved_branch)
                and _typed_additional_properties(resolved_branch) is None
                and not _is_explicit_opaque(resolved_branch)
                and "$ref" not in resolved_branch
            ):
                findings.append(
                    Violation(
                        "GPT_ACTION_UNTYPED_ONEOF_BRANCH",
                        rel_path,
                        0,
                        f"{branch_loc} branch sem shape tipado",
                    )
                )
            _walk_request_schema(
                document,
                branch,
                loc=branch_loc,
                findings=findings,
                rel_path=rel_path,
                seen=seen,
            )

    if resolved.get("type") == "array":
        items = resolved.get("items")
        if items is None:
            findings.append(
                Violation(
                    "GPT_ACTION_UNTYPED_NESTED_ARRAY_ITEM",
                    rel_path,
                    0,
                    f"{loc} array sem items",
                )
            )
            return
        resolved_items = resolve_ref(document, items)
        if isinstance(resolved_items, dict) and _is_object_schema(resolved_items):
            if (
                not _has_meaningful_properties(resolved_items)
                and _typed_additional_properties(resolved_items) is None
                and not _is_explicit_opaque(resolved_items)
                and "$ref" not in resolved_items
            ):
                findings.append(
                    Violation(
                        "GPT_ACTION_UNTYPED_NESTED_ARRAY_ITEM",
                        rel_path,
                        0,
                        f"{loc} items object sem properties/mapa tipado",
                    )
                )
        _walk_request_schema(
            document,
            items,
            loc=f"{loc}/items",
            findings=findings,
            rel_path=rel_path,
            seen=seen,
        )
        return

    if not _is_object_schema(resolved) or "$ref" in resolved:
        return

    if _is_explicit_opaque(resolved):
        description = resolved.get("description")
        if not isinstance(description, str) or not description.strip():
            findings.append(
                Violation(
                    "GPT_ACTION_OPAQUE_OBJECT_NOT_EXPLICIT",
                    rel_path,
                    0,
                    f"{loc} marca opaca sem description",
                )
            )
        return

    additional = resolved.get("additionalProperties")
    typed_map = _typed_additional_properties(resolved)
    meaningful = _has_meaningful_properties(resolved)

    if additional is True and not meaningful:
        findings.append(
            Violation(
                "GPT_ACTION_OPAQUE_OBJECT_NOT_EXPLICIT",
                rel_path,
                0,
                f"{loc} properties:{{}} + additionalProperties:true sem {OPAQUE_EXT}",
            )
        )
        return

    if not meaningful and typed_map is None:
        findings.append(
            Violation(
                "GPT_ACTION_EMPTY_OBJECT_SCHEMA",
                rel_path,
                0,
                f"{loc} object sem properties nem additionalProperties tipado",
            )
        )
        return

    props = resolved.get("properties")
    if isinstance(props, dict):
        for key, prop in props.items():
            _walk_request_schema(
                document,
                prop,
                loc=f"{loc}.properties.{key}",
                findings=findings,
                rel_path=rel_path,
                seen=seen,
            )
    if typed_map is not None:
        _walk_request_schema(
            document,
            typed_map,
            loc=f"{loc}.additionalProperties",
            findings=findings,
            rel_path=rel_path,
            seen=seen,
        )


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

        _walk_request_schema(
            document,
            media.get("schema"),
            loc=label,
            findings=findings,
            rel_path=rel_path,
            seen=set(),
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
