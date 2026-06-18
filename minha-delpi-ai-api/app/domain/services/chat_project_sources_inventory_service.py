"""Snapshot de inventário de fontes do projeto — lastProjectSourcesInventory."""

from __future__ import annotations

from typing import Any


class ChatProjectSourcesInventoryService:
    SNAPSHOT_KEY = "lastProjectSourcesInventory"

    @classmethod
    def serialize_source(cls, source: Any, *, ordinal: int) -> dict[str, Any]:
        metadata = source.metadata if isinstance(getattr(source, "metadata", None), dict) else {}

        title = str(
            getattr(source, "original_filename", None)
            or getattr(source, "title", None)
            or "Arquivo"
        ).strip()
        chunk_count = int(getattr(source, "chunk_count", None) or 0)
        indexed = bool(getattr(source, "indexed", None) or chunk_count > 0)

        return {
            "projectSourceId": str(getattr(source, "id", "") or "").strip(),
            "title": title,
            "ordinal": int(ordinal),
            "indexed": indexed,
            "chunkCount": chunk_count,
            "sourceType": str(getattr(source, "source_type", "") or "").strip(),
            "contentType": str(getattr(source, "content_type", "") or "").strip() or None,
            "sizeBytes": metadata.get("sizeBytes"),
        }

    @classmethod
    def serialize_sources(cls, sources: list[Any]) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []

        for index, source in enumerate(sources or [], start=1):
            entry = cls.serialize_source(source, ordinal=index)
            project_source_id = str(entry.get("projectSourceId") or "").strip()

            if project_source_id:
                serialized.append(entry)

        return serialized

    @classmethod
    def apply_to_snapshot(
        cls,
        snapshot: dict | None,
        inventory: list[dict[str, Any]] | None,
    ) -> dict:
        result = dict(snapshot or {})

        if inventory:
            result[cls.SNAPSHOT_KEY] = list(inventory)
        else:
            result.pop(cls.SNAPSHOT_KEY, None)

        return result

    @classmethod
    def read_inventory(
        cls,
        memory_snapshot: dict | None = None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        if isinstance(memory_snapshot, dict):
            items = memory_snapshot.get(cls.SNAPSHOT_KEY)

            if isinstance(items, list) and items:
                return [item for item in items if isinstance(item, dict)]

        return cls.read_from_previous_messages(previous_messages)

    @classmethod
    def read_from_previous_messages(
        cls,
        previous_messages: list[Any] | None,
    ) -> list[dict[str, Any]]:
        if not previous_messages:
            return []

        for item in reversed(previous_messages[-16:]):
            role = cls._message_role(item)

            if role != "assistant":
                continue

            metadata = cls._message_metadata(item)
            snapshot = metadata.get("contextSnapshot")

            if not isinstance(snapshot, dict):
                continue

            items = snapshot.get(cls.SNAPSHOT_KEY)

            if isinstance(items, list) and items:
                return [entry for entry in items if isinstance(entry, dict)]

        return []

    @staticmethod
    def _message_metadata(item: Any) -> dict:
        if isinstance(item, dict):
            metadata = item.get("metadata")

            if isinstance(metadata, dict):
                return metadata

            return item

        metadata = getattr(item, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}

    @staticmethod
    def _message_role(item: Any) -> str:
        if isinstance(item, dict):
            metadata = item.get("metadata")

            if isinstance(metadata, dict):
                role = item.get("role") or metadata.get("role") or metadata.get("messageRole")

                if role:
                    return str(role).strip().lower()

            return str(item.get("role") or "").strip().lower()

        return str(getattr(item, "role", "") or "").strip().lower()
