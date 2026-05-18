# app/domain/notifications/notification_preference_policy.py

from app.domain.notifications.notification_constants import ALLOWED_NOTIFICATION_CATEGORIES

# Categorias que o usuário não pode silenciar (avisos críticos da plataforma).
IMMUTABLE_NOTIFICATION_CATEGORIES = frozenset({"system"})

MUTABLE_NOTIFICATION_CATEGORIES = frozenset(
    ALLOWED_NOTIFICATION_CATEGORIES - IMMUTABLE_NOTIFICATION_CATEGORIES
)


def normalize_muted_categories(raw: list[str] | None) -> list[str]:
    if not raw:
        return []

    seen: set[str] = set()
    normalized: list[str] = []

    for item in raw:
        category = (item or "").strip().lower()
        if not category or category in seen:
            continue
        if category not in MUTABLE_NOTIFICATION_CATEGORIES:
            continue
        seen.add(category)
        normalized.append(category)

    return sorted(normalized)
