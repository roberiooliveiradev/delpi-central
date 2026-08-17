# app/domain/notifications/notification_constants.py

ALLOWED_NOTIFICATION_TYPES = frozenset({"info", "success", "warning", "error"})

# Portuguese (and common) aliases accepted on ingest; persisted value is always EN.
NOTIFICATION_TYPE_ALIASES: dict[str, str] = {
    "aviso": "info",
    "informacao": "info",
    "informação": "info",
    "atencao": "warning",
    "atenção": "warning",
    "alerta": "error",
    "erro": "error",
    "sucesso": "success",
}

ALLOWED_PRESENTATION_MODES = frozenset({"text", "html", "template"})

ALLOWED_ACTION_TYPES = frozenset({"none", "portal_route", "external_url"})


def normalize_notification_type(
    value: str | None,
    *,
    default: str = "info",
) -> str | None:
    """
    Normalize notification severity to a canonical EN type.

    Returns None when the value (after alias mapping) is not allowed.
    """
    raw = (value or default or "info").strip().lower()
    if not raw:
        raw = default
    canonical = NOTIFICATION_TYPE_ALIASES.get(raw, raw)
    if canonical not in ALLOWED_NOTIFICATION_TYPES:
        return None
    return canonical
