# app/domain/notifications/notification_preference_policy.py


def normalize_muted_categories(
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
