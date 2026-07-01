# app/domain/notifications/notification_constants.py

ALLOWED_NOTIFICATION_TYPES = frozenset({"info", "success", "warning", "error"})

ALLOWED_PRESENTATION_MODES = frozenset({"text", "html", "template"})

ALLOWED_ACTION_TYPES = frozenset({"none", "portal_route", "external_url"})
