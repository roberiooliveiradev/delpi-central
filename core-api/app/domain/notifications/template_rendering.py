# app/domain/notifications/template_rendering.py

from __future__ import annotations

import re

class TemplateRenderError(ValueError):
    pass


_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def render_template_text(template: str, variables: dict[str, str]) -> str:
    if not template:
        return ""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise TemplateRenderError(f"template placeholder missing: {key}")
        return variables[key]

    return _PLACEHOLDER_RE.sub(replace, template)
