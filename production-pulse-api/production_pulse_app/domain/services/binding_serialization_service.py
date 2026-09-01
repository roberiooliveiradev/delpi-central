from __future__ import annotations

from typing import Any

from production_pulse_app.core.serialize import json_safe


def binding_row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    return json_safe(
        {
            "id": str(row["id"]),
            "deviceId": str(row["device_id"]),
            "anchorType": row["anchor_type"],
            "placementLabel": row["placement_label"],
            "placementKey": row["placement_key"],
            "workCenterCode": row.get("work_center_code"),
            "workCenterName": row.get("work_center_name"),
            "machineCode": row.get("machine_code"),
            "machineLabel": row.get("machine_label"),
            "equipmentLabel": row.get("equipment_label"),
            "areaLabel": row.get("area_label"),
            "resourceCode": row.get("resource_code"),
            "toolCode": row.get("tool_code"),
            "notes": row.get("notes"),
            "effectiveFrom": row.get("effective_from"),
            "effectiveTo": row.get("effective_to"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
        }
    )
