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
