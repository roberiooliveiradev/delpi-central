"""Normalize/validate meeting-minute participants before persistence.

Canonical gate shared by Portal CRUD and TÉO/GPT Actions — prevents
name-only "internal" rows that cannot become signers (no user_id /
invite_email) and silent must_sign without identity.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.services.meeting_minute_write_fields import (
    normalize_optional_uuid,
)


def _optional_email(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_participants(raw: Any) -> list[dict[str, Any]]:
    """Return canonical participant rows or raise ValueError (fail closed).

    Rules:
    - display_name is required.
    - Internal (is_external=false) requires a Delpi user_id UUID.
    - must_sign=true requires user_id (internal) or invite_email (external).
    - Presence-only external guests may omit email when must_sign=false.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("participants deve ser uma lista.")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(
                f"participants[{index}] inválido: esperado objeto."
            )
        display_name = str(item.get("display_name") or "").strip()
        if not display_name:
            raise ValueError(
                f"participants[{index}]: informe display_name."
            )
        is_external = bool(item.get("is_external"))
        must_sign = bool(item.get("must_sign"))
        user_id = normalize_optional_uuid(
            item.get("user_id"), field=f"participants[{index}].user_id"
        )
        invite_email = _optional_email(item.get("invite_email"))
        role = str(item.get("role_in_meeting") or "other").strip() or "other"
        presence = str(item.get("presence") or "present").strip() or "present"

        if not is_external and user_id is None:
            raise ValueError(
                f"participants[{index}] ({display_name}): participante "
                "interno exige user_id (UUID Delpi). Não envie apenas o "
                "nome — resolva o usuário no diretório antes de gravar."
            )
        if must_sign and user_id is None and invite_email is None:
            raise ValueError(
                f"participants[{index}] ({display_name}): must_sign=true "
                "exige user_id (Delpi) ou invite_email (convidado externo)."
            )
        if must_sign and is_external and invite_email and "@" not in invite_email:
            raise ValueError(
                f"participants[{index}] ({display_name}): invite_email inválido."
            )

        row: dict[str, Any] = {
            "display_name": display_name,
            "role_in_meeting": role,
            "presence": presence,
            "is_external": is_external,
            "must_sign": must_sign,
            "sort_order": item.get("sort_order", index),
        }
        if user_id is not None:
            row["user_id"] = user_id
        if invite_email is not None:
            row["invite_email"] = invite_email
        normalized.append(row)
    return normalized


def derive_signers_from_participants(
    participants: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build signer rows from must_sign participants (fail closed)."""
    signers: list[dict[str, Any]] = []
    for index, item in enumerate(participants):
        if not item.get("must_sign"):
            continue
        display_name = str(item.get("display_name") or "").strip()
        user_id = item.get("user_id")
        invite_email = _optional_email(item.get("invite_email"))
        if not display_name or (not user_id and not invite_email):
            raise ValueError(
                "Cada signatário derivado de participants exige "
                "display_name e user_id ou invite_email."
            )
        signers.append(
            {
                "user_id": user_id,
                "invite_email": invite_email,
                "display_name": display_name,
                "sign_order": index + 1,
            }
        )
    return signers
