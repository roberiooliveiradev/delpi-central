# app/domain/notifications/notification_preference_policy.py


def normalize_preference_categories(
    raw: list[str] | None,
    *,
    mutable_categories: frozenset[str],
) -> list[str]:
    if not raw:
        return []

    seen: set[str] = set()
    normalized: list[str] = []

    for item in raw:
        category = (item or "").strip().lower()
        if not category or category in seen:
            continue
        if category not in mutable_categories:
            continue
        seen.add(category)
        normalized.append(category)

    return sorted(normalized)


def normalize_muted_categories(
    raw: list[str] | None,
    *,
    mutable_categories: frozenset[str],
) -> list[str]:
    return normalize_preference_categories(raw, mutable_categories=mutable_categories)


def reconcile_mute_and_important(
    muted_categories: list[str],
    important_categories: list[str],
) -> tuple[list[str], list[str]]:
    """Importante prevalece: remove categorias importantes da lista de mute."""
    important = set(important_categories)
    muted = sorted(set(muted_categories) - important)
    return muted, sorted(important)


def reconcile_mute_important_and_email(
    muted_categories: list[str],
    important_categories: list[str],
    email_categories: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """
    Mute remove important e email.
    Important remove mute (prevalece sobre silêncio).
    Email remove mute quando ativado; important não precisa estar em email_categories.
    """
    muted, important = reconcile_mute_and_important(muted_categories, important_categories)
    muted_set = set(muted)
    important_set = set(important)
    email = sorted((set(email_categories) - muted_set) | set())
    # Silêncio remove e-mail opt-in; importante não precisa duplicar no array email
    email = sorted(set(email) - muted_set - important_set)
    return muted, sorted(important_set), email


def is_email_channel_enabled(
    category: str,
    *,
    muted_categories: list[str],
    important_categories: list[str],
    email_categories: list[str],
) -> bool:
    normalized = (category or "").strip().lower()
    if not normalized or normalized in muted_categories:
        return False
    return normalized in important_categories or normalized in email_categories
