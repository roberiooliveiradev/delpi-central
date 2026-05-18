# app/domain/notifications/notification_constants.py

ALLOWED_NOTIFICATION_TYPES = frozenset({"info", "success", "warning", "error"})

ALLOWED_NOTIFICATION_CATEGORIES = frozenset({
    "system",
    "welcome",
    "birthday",
    "company_event",
    "announcement",
    "custom",
})

ALLOWED_PRESENTATION_MODES = frozenset({"text", "html", "template"})

ALLOWED_ACTION_TYPES = frozenset({"none", "portal_route", "external_url"})

CATEGORY_DEFAULT_ICONS = {
    "system": "bell",
    "welcome": "sparkles",
    "birthday": "cake",
    "company_event": "calendar",
    "announcement": "megaphone",
    "custom": "bell",
}
