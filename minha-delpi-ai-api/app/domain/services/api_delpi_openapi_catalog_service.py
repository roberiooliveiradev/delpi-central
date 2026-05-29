"""Gera catálogo markdown a partir de schema OpenAPI (provider api-delpi)."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


def collect_openapi_operations(schema: dict) -> list[dict]:
    operations: list[dict] = []

    for path, path_item in sorted((schema.get("paths") or {}).items()):
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue

            tags = operation.get("tags") or ["default"]
            operations.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "operation_id": str(operation.get("operationId") or "").strip(),
                    "summary": str(operation.get("summary") or "").strip(),
                    "description": str(operation.get("description") or "").strip(),
                    "tag": str(tags[0] if tags else "default"),
                }
            )

    return operations


def build_openapi_catalog_markdown(
    schema: dict,
    *,
    provider_key: str = "api-delpi",
) -> str:
    operations = collect_openapi_operations(schema)
    by_tag: dict[str, list[dict]] = defaultdict(list)

    for item in operations:
        by_tag[item["tag"]].append(item)

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Catálogo OpenAPI — api-delpi (gerado automaticamente)",
        "",
        f"**Provider:** `{provider_key}` · **Rotas:** {len(operations)} · **Gerado em:** {generated_at}",
        "",
        "> Não edite manualmente. Regenerado por `scripts/sync_api_delpi_openapi.py`.",
        "",
    ]

    for tag in sorted(by_tag):
        lines.extend(
            [
                f"## {tag} ({len(by_tag[tag])})",
                "",
                "| Método | Path | operationId | Summary |",
                "|--------|------|-------------|---------|",
            ]
        )

        for item in by_tag[tag]:
            summary = item["summary"].replace("|", "\\|") or "—"
            operation_id = item["operation_id"] or "—"
            lines.append(
                f"| `{item['method']}` | `{item['path']}` | `{operation_id}` | {summary} |"
            )

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
