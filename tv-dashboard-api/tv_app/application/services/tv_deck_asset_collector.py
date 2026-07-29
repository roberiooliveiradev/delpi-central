"""Coleta recursiva de assetId e dataBinding em JSON do deck TV."""

from __future__ import annotations

from typing import Any


def collect_asset_ids(*roots: Any) -> set[str]:
    """Retorna todos os valores string de chaves `assetId` em estruturas aninhadas."""
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            raw = node.get("assetId")
            if isinstance(raw, str):
                cleaned = raw.strip()
                if cleaned:
                    found.add(cleaned)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for root in roots:
        walk(root)
    return found


def rewrite_asset_ids(node: Any, id_map: dict[str, str]) -> Any:
    """Copia profunda reescrevendo assetId conforme mapa source→destino."""
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            if key == "assetId" and isinstance(value, str):
                mapped = id_map.get(value.strip())
                out[key] = mapped if mapped else value
            else:
                out[key] = rewrite_asset_ids(value, id_map)
        return out
    if isinstance(node, list):
        return [rewrite_asset_ids(item, id_map) for item in node]
    return node


def collect_data_bindings(
    slides: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extrai dataBinding de blocos (e nativos flat) para índice de auditoria."""
    items: list[dict[str, Any]] = []

    def walk_block(
        block: dict[str, Any],
        *,
        slide_source_id: str | None,
    ) -> None:
        binding = block.get("dataBinding")
        if isinstance(binding, dict):
            operation_id = str(binding.get("operationId") or "").strip()
            if operation_id:
                params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
                items.append(
                    {
                        "operationId": operation_id,
                        "params": dict(params),
                        "slideSourceId": slide_source_id,
                        "blockId": str(block.get("id") or "").strip() or None,
                        "blockType": str(block.get("type") or "").strip() or None,
                    }
                )
        for value in block.values():
            if isinstance(value, dict):
                walk_block(value, slide_source_id=slide_source_id)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        walk_block(item, slide_source_id=slide_source_id)

    for slide in slides:
        if not isinstance(slide, dict):
            continue
        source_id = str(slide.get("sourceId") or slide.get("id") or "").strip() or None
        native = slide.get("nativeConfig")
        if not isinstance(native, dict):
            continue
        # Binding flat em telas nativas (ex.: operationId no root — raro).
        root_binding = native.get("dataBinding")
        if isinstance(root_binding, dict):
            walk_block(
                {"id": None, "type": slide.get("nativeScreenKey"), "dataBinding": root_binding},
                slide_source_id=source_id,
            )
        blocks = native.get("blocks")
        if isinstance(blocks, list):
            for block in blocks:
                if isinstance(block, dict):
                    walk_block(block, slide_source_id=source_id)
    return items
