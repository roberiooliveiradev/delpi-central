import csv
import io
import json
from typing import Iterable


class AuditCsvExporterService:
    HEADERS = (
        "id",
        "createdAt",
        "traceId",
        "action",
        "context",
        "userId",
        "promptHash",
        "toolCalls",
        "metadata",
    )

    def export_rows(self, items: Iterable[dict]) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.HEADERS, extrasaction="ignore")
        writer.writeheader()

        for item in items:
            writer.writerow(self._serialize_row(item))

        return buffer.getvalue()

    def _serialize_row(self, item: dict) -> dict:
        return {
            "id": item.get("id"),
            "createdAt": item.get("createdAt"),
            "traceId": item.get("traceId") or "",
            "action": item.get("action") or "",
            "context": item.get("context") or "",
            "userId": item.get("userId") or "",
            "promptHash": item.get("promptHash") or "",
            "toolCalls": self._json_cell(item.get("toolCalls")),
            "metadata": self._json_cell(item.get("metadata")),
        }

    @staticmethod
    def _json_cell(value) -> str:
        if value is None:
            return ""

        return json.dumps(value, ensure_ascii=False)
