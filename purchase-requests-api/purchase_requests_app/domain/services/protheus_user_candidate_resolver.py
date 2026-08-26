"""Resolve duplicate SYS_USR rows that share the same USR_EMAIL."""

from __future__ import annotations

from typing import Any


def _normalize_token(value: str) -> str:
    return " ".join((value or "").strip().upper().split())


def pick_protheus_user_candidate(
    candidates: list[dict[str, Any]],
    *,
    portal_user_name: str | None = None,
) -> dict[str, Any] | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    portal_name = _normalize_token(portal_user_name or "")
    if portal_name:
        for candidate in candidates:
            protheus_name = _normalize_token(str(candidate.get("name") or ""))
            protheus_code = _normalize_token(str(candidate.get("code") or "").replace(".", " "))
            if portal_name == protheus_name:
                return candidate
            if portal_name in protheus_name or protheus_name in portal_name:
                return candidate
            portal_tokens = portal_name.split()
            if len(portal_tokens) >= 2 and all(
                token in protheus_name or token in protheus_code for token in portal_tokens
            ):
                return candidate

    return None
