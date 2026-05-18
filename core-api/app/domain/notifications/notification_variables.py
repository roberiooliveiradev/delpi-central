# app/domain/notifications/notification_variables.py

from __future__ import annotations

RECIPIENT_VARIABLE_KEYS: frozenset[str] = frozenset(
    {
        "userName",
        "userFullName",
        "userEmail",
    }
)

ADMIN_VARIABLE_KEYS: frozenset[str] = frozenset(
    {
        "eventName",
        "eventDate",
        "location",
    }
)

ALL_KNOWN_VARIABLE_KEYS: frozenset[str] = RECIPIENT_VARIABLE_KEYS | ADMIN_VARIABLE_KEYS


def text_has_recipient_placeholders(*texts: str | None) -> bool:
    for raw in texts:
        if not raw:
            continue
        for key in RECIPIENT_VARIABLE_KEYS:
            if f"{{{key}}}" in raw:
                return True
    return False
