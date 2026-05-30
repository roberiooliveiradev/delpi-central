from __future__ import annotations

_LOWERCASE_PARTICLES = {"de", "da", "do", "das", "dos", "e"}


def format_person_name(value: str | None, *, default: str = "Usuário") -> str:
    if value is None:
        return default

    trimmed = value.strip()
    if not trimmed:
        return default

    tokens = trimmed.split()
    formatted_tokens: list[str] = []

    for index, token in enumerate(tokens):
        lower = token.lower()
        if index > 0 and lower in _LOWERCASE_PARTICLES:
            formatted_tokens.append(lower)
            continue

        hyphen_parts = token.split("-")
        formatted_tokens.append(
            "-".join(
                part[:1].upper() + part[1:].lower() if part else part
                for part in hyphen_parts
            ),
        )

    return " ".join(formatted_tokens)
