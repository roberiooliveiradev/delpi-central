from __future__ import annotations

from typing import Any


def command_row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "deviceId": str(row["device_id"]),
        "commandKey": row["command_key"],
        "issuedBy": row["issued_by"],
        "success": row["success"],
        "errorMessage": row.get("error_message"),
        "requestPayload": row.get("request_payload") or {},
        "responsePayload": row.get("response_payload") or {},
        "createdAt": row.get("created_at"),
    }
