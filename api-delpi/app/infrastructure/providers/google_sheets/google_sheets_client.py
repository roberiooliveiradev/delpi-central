# app/infrastructure/providers/google_sheets/google_sheets_client.py

import csv
import io
from typing import List
from urllib.parse import quote

import requests


class GoogleSheetsClient:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def read_csv_rows(self, sheet_id: str, gid: str) -> List[dict]:
        if not sheet_id:
            raise ValueError("sheet_id is required")

        if not gid:
            raise ValueError("gid is required")

        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{quote(sheet_id)}/export?format=csv&gid={quote(str(gid))}"
        )

        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()

        content = response.content.decode("utf-8-sig", errors="ignore")
        reader = csv.DictReader(io.StringIO(content))

        return [self._normalize_row(row) for row in reader]

    def _normalize_row(self, row: dict) -> dict:
        normalized = {}

        for key, value in row.items():
            if key is None:
                continue

            normalized_key = self._normalize_key(key)
            normalized[normalized_key] = value.strip() if isinstance(value, str) else value

        return normalized

    def _normalize_key(self, value: str) -> str:
        return (
            str(value)
            .strip()
            .lower()
            .replace("ç", "c")
            .replace("ã", "a")
            .replace("á", "a")
            .replace("à", "a")
            .replace("â", "a")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("õ", "o")
            .replace("ú", "u")
            .replace("/", "_")
            .replace("-", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("%", "percent")
            .replace("$", "")
            .replace(" ", "_")
        )