from __future__ import annotations


def suggest_duplicate_versao_revisao(source_version: str, existing_versions: set[str]) -> str:
    version = (source_version or "").strip()
    if not version:
        return _fallback_copy_label("1.0.0", existing_versions)

    parts = version.split(".")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        next_patch = patch + 1
        while True:
            candidate = f"{major}.{minor}.{next_patch}"
            if candidate not in existing_versions:
                return candidate
            next_patch += 1

    return _fallback_copy_label(version, existing_versions)


def _fallback_copy_label(base: str, existing_versions: set[str]) -> str:
    suffix = 2
    while True:
        candidate = f"{base}-copia-{suffix}"
        if candidate not in existing_versions:
            return candidate
        suffix += 1
