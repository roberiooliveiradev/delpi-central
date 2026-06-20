from __future__ import annotations

import logging
from typing import Any

import requests

from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.languagetool")


class LanguageToolHttpGateway:
    """Cliente HTTP para LanguageTool self-hosted (/v2/check)."""

    def check(self, text: str, *, language: str) -> list[dict[str, Any]]:
        cleaned = str(text or "").strip()

        if not cleaned:
            return []

        base_url = str(Settings.CHAT_LANGUAGETOOL_BASE_URL or "").rstrip("/")
        timeout = float(Settings.CHAT_LANGUAGETOOL_TIMEOUT_SECONDS)

        if not base_url:
            return []

        endpoint = f"{base_url}/v2/check"

        try:
            response = requests.post(
                endpoint,
                data={
                    "text": cleaned,
                    "language": language,
                    "enabledOnly": "false",
                },
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, OSError, TimeoutError) as exc:
            logger.info("LanguageTool indisponível (%s): %s", endpoint, exc)
            return []
        except ValueError:
            logger.info("LanguageTool resposta inválida (%s)", endpoint)
            return []

        matches = payload.get("matches") if isinstance(payload, dict) else None

        if not isinstance(matches, list):
            return []

        issues: list[dict[str, Any]] = []

        for match in matches:
            if not isinstance(match, dict):
                continue

            rule = match.get("rule") if isinstance(match.get("rule"), dict) else {}
            category = rule.get("category") if isinstance(rule.get("category"), dict) else {}
            replacements_raw = match.get("replacements")

            replacements: list[str] = []

            if isinstance(replacements_raw, list):
                for item in replacements_raw:
                    if isinstance(item, dict):
                        value = str(item.get("value") or "").strip()

                        if value:
                            replacements.append(value)

            issues.append(
                {
                    "offset": int(match.get("offset", 0)),
                    "length": int(match.get("length", 0)),
                    "message": str(match.get("message") or match.get("shortMessage") or "").strip(),
                    "replacements": replacements,
                    "ruleId": str(rule.get("id") or "").strip(),
                    "category": str(category.get("id") or "").strip(),
                }
            )

        return issues
