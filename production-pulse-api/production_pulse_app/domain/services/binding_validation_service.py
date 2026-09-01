from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any
from uuid import UUID

ANCHOR_TYPES = frozenset({"work_center", "machine", "equipment", "area", "standalone"})


class BindingValidationError(ValueError):
    pass


@dataclass(frozen=True)
class NormalizedBindingInput:
    anchor_type: str
    work_center_code: str | None
    work_center_name: str | None
    machine_code: str | None
    machine_label: str | None
    equipment_label: str | None
    area_label: str | None
    resource_code: str | None
    tool_code: str | None
    notes: str | None


def _pick(payload: dict[str, Any], snake: str, camel: str) -> Any:
    if snake in payload:
        return payload[snake]
    if camel in payload:
        return payload[camel]
    return None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_binding_input(payload: dict[str, Any]) -> NormalizedBindingInput:
    anchor_type = _optional_text(_pick(payload, "anchor_type", "anchorType"))
    if anchor_type not in ANCHOR_TYPES:
        raise BindingValidationError(
            "anchor_type inválido. Use work_center, machine, equipment, area ou standalone."
        )

    work_center_code = _optional_text(_pick(payload, "work_center_code", "workCenterCode"))
    work_center_name = _optional_text(_pick(payload, "work_center_name", "workCenterName"))
    machine_code = _optional_text(_pick(payload, "machine_code", "machineCode"))
    machine_label = _optional_text(_pick(payload, "machine_label", "machineLabel"))
    equipment_label = _optional_text(_pick(payload, "equipment_label", "equipmentLabel"))
    area_label = _optional_text(_pick(payload, "area_label", "areaLabel"))
    resource_code = _optional_text(_pick(payload, "resource_code", "resourceCode"))
    tool_code = _optional_text(_pick(payload, "tool_code", "toolCode"))
    notes = _optional_text(payload.get("notes"))

    if anchor_type == "work_center":
        if not work_center_code:
            raise BindingValidationError("work_center_code é obrigatório para anchor_type=work_center.")
    elif anchor_type == "machine":
        if not machine_label:
            raise BindingValidationError("machine_label é obrigatório para anchor_type=machine.")
    elif anchor_type == "equipment":
        if not equipment_label:
            raise BindingValidationError("equipment_label é obrigatório para anchor_type=equipment.")
    elif anchor_type == "area":
        if not area_label:
            raise BindingValidationError("area_label é obrigatório para anchor_type=area.")
    elif anchor_type == "standalone":
        forbidden = [
            work_center_code,
            work_center_name,
            machine_code,
            machine_label,
            equipment_label,
            area_label,
        ]
        if any(forbidden):
            raise BindingValidationError(
                "anchor_type=standalone não aceita campos de CT, máquina, equipamento ou área."
            )

    return NormalizedBindingInput(
        anchor_type=anchor_type,
        work_center_code=work_center_code,
        work_center_name=work_center_name,
        machine_code=machine_code,
        machine_label=machine_label,
        equipment_label=equipment_label,
        area_label=area_label,
        resource_code=resource_code,
        tool_code=tool_code,
        notes=notes,
    )


def slugify_label(text: str, *, max_len: int = 80) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    if not slug:
        slug = "item"
    return slug[:max_len].strip("-") or "item"


def compose_placement_label(
    binding: NormalizedBindingInput,
    *,
    device_name: str,
) -> str:
    if binding.anchor_type == "work_center":
        name_part = binding.work_center_name or binding.work_center_code or ""
        return f"{binding.work_center_code} · {name_part}".strip(" ·")
    if binding.anchor_type == "machine":
        label = binding.machine_label or ""
        if binding.work_center_code:
            suffix = binding.work_center_name or binding.work_center_code
            return f"{label} ({suffix})"
        return label
    if binding.anchor_type == "equipment":
        return binding.equipment_label or ""
    if binding.anchor_type == "area":
        return binding.area_label or ""
    return device_name


def compose_placement_key_base(
    binding: NormalizedBindingInput,
    *,
    branch: str,
    device_id: UUID,
) -> str:
    if binding.anchor_type == "work_center":
        return f"wc:{branch}:{binding.work_center_code}"
    if binding.anchor_type == "machine":
        return f"m:{branch}:{slugify_label(binding.machine_label or '')}"
    if binding.anchor_type == "equipment":
        return f"e:{branch}:{slugify_label(binding.equipment_label or '')}"
    if binding.anchor_type == "area":
        return f"a:{branch}:{slugify_label(binding.area_label or '')}"
    return f"s:{device_id}"
