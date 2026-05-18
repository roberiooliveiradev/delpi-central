def normalize_tags(value) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        items = value
    else:
        items = str(value).split(",")

    normalized = []

    for item in items:
        tag = str(item).strip().lower()

        if tag and tag not in normalized:
            normalized.append(tag)

    return normalized


def build_global_curatorial_metadata(
    *,
    category: str | None = None,
    tags: list[str] | str | None = None,
    namespace: str | None = None,
    domain: str | None = None,
    priority: int | float | str | None = None,
    quality_score: int | float | str | None = None,
    extra: dict | None = None,
) -> dict:
    metadata = {
        "scope": "global",
        "category": _clean_text(category),
        "tags": normalize_tags(tags),
        "namespace": _clean_text(namespace),
        "domain": _clean_text(domain),
        "priority": _normalize_priority(priority),
        "qualityScore": _normalize_quality_score(quality_score),
    }

    if extra:
        metadata.update(extra)

    return {key: value for key, value in metadata.items() if value is not None and value != []}


def enrich_document_payload(metadata: dict | None) -> dict:
    meta = metadata or {}

    return {
        "category": meta.get("category"),
        "tags": normalize_tags(meta.get("tags")),
        "namespace": meta.get("namespace"),
        "domain": meta.get("domain"),
        "priority": meta.get("priority"),
        "qualityScore": meta.get("qualityScore"),
    }


def merge_curatorial_metadata(
    current: dict | None,
    *,
    category: str | None = None,
    tags: list[str] | str | None = None,
    namespace: str | None = None,
    domain: str | None = None,
    priority: int | float | str | None = None,
    quality_score: int | float | str | None = None,
) -> dict:
    merged = dict(current or {})

    if category is not None:
        merged["category"] = _clean_text(category)

    if tags is not None:
        merged["tags"] = normalize_tags(tags)

    if namespace is not None:
        merged["namespace"] = _clean_text(namespace)

    if domain is not None:
        merged["domain"] = _clean_text(domain)

    if priority is not None:
        merged["priority"] = _normalize_priority(priority)

    if quality_score is not None:
        merged["qualityScore"] = _normalize_quality_score(quality_score)

    return merged


def _clean_text(value) -> str | None:
    normalized = str(value or "").strip()

    return normalized or None


def _normalize_priority(value) -> int | None:
    if value is None or value == "":
        return None

    try:
        priority = int(value)
    except (TypeError, ValueError):
        return None

    return max(1, min(priority, 5))


def _normalize_quality_score(value) -> int | None:
    if value is None or value == "":
        return None

    try:
        score = int(value)
    except (TypeError, ValueError):
        return None

    return max(0, min(score, 100))
