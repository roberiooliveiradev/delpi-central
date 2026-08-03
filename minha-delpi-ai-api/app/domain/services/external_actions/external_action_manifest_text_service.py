"""Manifesto canônico de action OpenAPI — lexical, embed e ranker (fonte única)."""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionManifestTextService:
    """Monta texto de retrieval a partir de method/path/summary + params/enums + entity/shape/fields.

    Params e retornos entram só como boost textual — nunca como filtro exclusivo.
    """

    @classmethod
    def build(cls, action: dict | None) -> str:
        if not isinstance(action, dict):
            return ""

        settings = cls._settings()
        parts: list[str] = []

        method = str(action.get("method") or "").upper().strip()
        if method:
            parts.append(method)

        path = str(action.get("path") or "").strip()
        if path:
            parts.append(path)

        summary = str(action.get("summary") or "").strip()
        if summary:
            parts.append(summary)

        description = str(action.get("description") or "").strip()
        if description:
            parts.append(description)

        operation_id = str(
            action.get("operationId") or action.get("operation_id") or ""
        ).strip()
        if operation_id:
            parts.append(operation_id)

        tags = action.get("tags") or []
        if isinstance(tags, list):
            tag_text = ", ".join(str(item).strip() for item in tags if str(item).strip())
        else:
            tag_text = str(tags).strip()
        if tag_text:
            parts.append(tag_text)

        when_to_use = str(
            action.get("whenToUse") or action.get("when_to_use") or ""
        ).strip()
        if when_to_use:
            parts.append(f"{settings['whenToUseLabel']}: {when_to_use}")

        param_parts = cls._parameter_parts(action, settings)
        if param_parts:
            parts.append(f"{settings['paramsLabel']}: {' ; '.join(param_parts)}")

        return_parts = cls._return_parts(action, settings)
        if return_parts:
            parts.append(f"{settings['returnsLabel']}: {' ; '.join(return_parts)}")

        text = " | ".join(part for part in parts if part)
        max_chars = int(settings["maxChars"])
        return text[:max_chars] if max_chars > 0 else text

    @classmethod
    def _settings(cls) -> dict[str, Any]:
        node = ExternalActionResponseContentService.get_node(
            "actionSelection",
            "manifestText",
        )
        if not isinstance(node, dict):
            node = {}

        def _int(key: str, default: int) -> int:
            raw = node.get(key, default)
            try:
                return int(raw)
            except (TypeError, ValueError):
                return default

        def _label(key: str, default: str) -> str:
            value = str(node.get(key) or default).strip()
            return value or default

        return {
            "maxChars": _int("maxChars", 4000),
            "maxParameters": _int("maxParameters", 24),
            "maxEnumValues": _int("maxEnumValues", 16),
            "maxFieldNames": _int("maxFieldNames", 24),
            "paramsLabel": _label("paramsLabel", "params"),
            "enumsLabel": _label("enumsLabel", "enums"),
            "returnsLabel": _label("returnsLabel", "returns"),
            "entityLabel": _label("entityLabel", "entity"),
            "shapeLabel": _label("shapeLabel", "shape"),
            "fieldsLabel": _label("fieldsLabel", "fields"),
            "whenToUseLabel": _label("whenToUseLabel", "whenToUse"),
        }

    @classmethod
    def _parameter_parts(cls, action: dict, settings: dict[str, Any]) -> list[str]:
        schema = action.get("parametersSchema")
        if schema is None:
            schema = action.get("parameters_schema")
        if not isinstance(schema, list):
            return []

        parts: list[str] = []
        max_params = int(settings["maxParameters"])
        max_enums = int(settings["maxEnumValues"])
        enums_label = str(settings["enumsLabel"])

        for param in schema:
            if len(parts) >= max_params:
                break
            if not isinstance(param, dict):
                continue

            name = str(param.get("name") or "").strip()
            if not name:
                continue

            chunks = [name]
            description = str(param.get("description") or "").strip()
            if description:
                chunks.append(description)

            schema_node = param.get("schema") if isinstance(param.get("schema"), dict) else {}
            enum_values = schema_node.get("enum") if isinstance(schema_node, dict) else None
            if isinstance(enum_values, list) and enum_values:
                rendered = [
                    str(item).strip()
                    for item in enum_values[:max_enums]
                    if str(item).strip()
                ]
                if rendered:
                    chunks.append(f"{enums_label}={'|'.join(rendered)}")

            parts.append(" ".join(chunks))

        return parts

    @classmethod
    def _return_parts(cls, action: dict, settings: dict[str, Any]) -> list[str]:
        parts: list[str] = []
        delpi = action.get("delpiMetadata")
        if delpi is None:
            delpi = action.get("delpi_metadata")
        if not isinstance(delpi, dict):
            delpi = {}

        entity = str(delpi.get("entity") or "").strip()
        if entity:
            parts.append(f"{settings['entityLabel']}={entity}")

        shape = str(delpi.get("shape") or "").strip()
        if shape:
            parts.append(f"{settings['shapeLabel']}={shape}")

        field_names = cls._field_names(action, delpi, int(settings["maxFieldNames"]))
        if field_names:
            parts.append(f"{settings['fieldsLabel']}={','.join(field_names)}")

        return parts

    @classmethod
    def _field_names(
        cls,
        action: dict,
        delpi: dict,
        max_fields: int,
    ) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()

        def _add(raw: Any) -> None:
            if len(names) >= max_fields:
                return
            token = str(raw or "").strip()
            if not token:
                return
            key = token.lower()
            if key in seen:
                return
            seen.add(key)
            names.append(token)

        presentation = delpi.get("presentation")
        if isinstance(presentation, dict):
            for key in ("fields", "fieldNames", "columns"):
                value = presentation.get(key)
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            _add(item.get("name") or item.get("key") or item.get("label"))
                        else:
                            _add(item)

        response = action.get("responseSchema")
        if response is None:
            response = action.get("response_schema")
        if isinstance(response, dict):
            for status_key in ("200", "201"):
                ok = response.get(status_key)
                if not isinstance(ok, dict):
                    continue
                cls._collect_fields_from_response(ok, _add)
                if len(names) >= max_fields:
                    break

        return names

    @classmethod
    def _collect_fields_from_response(cls, response_ok: dict, add) -> None:
        content = response_ok.get("content")
        if not isinstance(content, dict):
            return

        json_content = content.get("application/json")
        if not isinstance(json_content, dict):
            return

        example = json_content.get("example")
        if isinstance(example, dict):
            meta = example.get("meta")
            if isinstance(meta, dict):
                fields = meta.get("fields")
                if isinstance(fields, list):
                    for item in fields:
                        if isinstance(item, dict):
                            add(item.get("name") or item.get("key") or item.get("label"))
                        else:
                            add(item)

            data = example.get("data")
            if isinstance(data, dict):
                for key in data.keys():
                    add(key)
