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
    Mute, importante e e-mail são canais distintos.
    - Importante e e-mail removem silêncio da mesma categoria.
    - Silêncio restante remove importante e e-mail.
    - Importante não liga nem desliga e-mail (estrela ≠ envelope).
    """
    muted, important = reconcile_mute_and_important(muted_categories, important_categories)
    muted_set = set(muted)
    important_set = set(important)
    email_set = {c for c in email_categories if c}

    muted_set -= important_set
    muted_set -= email_set
    email_set -= muted_set
    important_set -= muted_set

    return sorted(muted_set), sorted(important_set), sorted(email_set)


def is_email_channel_enabled(
    category: str,
    *,
    muted_categories: list[str],
    important_categories: list[str],
    email_categories: list[str],
) -> bool:
    """E-mail só via emailCategories — importante não implica canal e-mail."""
    _ = important_categories
    normalized = (category or "").strip().lower()
    if not normalized or normalized in muted_categories:
        return False
    return normalized in email_categories
