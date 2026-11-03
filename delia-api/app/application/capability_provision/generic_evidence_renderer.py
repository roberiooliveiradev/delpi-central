"""DELIA-C3-UNIFIED-EVIDENCE-PRESENTATION-01 generic evidence surface."""
from __future__ import annotations
from collections.abc import Mapping

PRESENTATION_COMPLETE = "complete"
PRESENTATION_PARTIAL_OWNER_PAGINATION = "partial_owner_pagination"
PRESENTATION_PARTIAL_PRESENTATION_LIMIT = "partial_presentation_limit"
PRESENTATION_INCOMPLETE_SOURCE = "incomplete_source"
PRESENTATION_UNKNOWN_COMPLETENESS = "unknown_completeness"

_PRESENTATION_NODE_BUDGET = 512
_PRESENTATION_MAX_DEPTH = 6
_PRESENTATION_MAX_VALUE_CHARS = 2000
_PRESENTATION_MAX_LABEL_CHARS = 80
_MD_STRUCTURAL = frozenset("*_" + chr(96) + "#>[]|\\-!")


def _md_escape(text: str) -> str:
    return "".join("\\" + ch if ch in _MD_STRUCTURAL else ch for ch in text)


def _render_label(key: object, field_labels: Mapping[str, str]) -> str:
    """Label for a field key: governed label when declared, else a
    humanized fallback — same contract the flat projection used."""
    raw = str(key)
    if raw in field_labels:
        return field_labels[raw]
    return _md_escape(raw.replace("_", " ").capitalize())[
        :_PRESENTATION_MAX_LABEL_CHARS
    ]


def _render_value(value: object) -> str | None:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "sim" if value else "nao"
    if isinstance(value, (int, float)):
        return str(value)
    text = _md_escape(str(value))
    return (
        text[:_PRESENTATION_MAX_VALUE_CHARS] + "…"
        if len(text) > _PRESENTATION_MAX_VALUE_CHARS
        else text
    )


def render_business_evidence(
    value: object,
    field_labels: Mapping[str, str],
    *,
    _budget: list[int] | None = None,
    _depth: int = 0,
) -> tuple[list[str], bool]:
    """Recursive generic Markdown for authorized evidence.

    Returns ``(lines, budget_exhausted)``; the caller reports
    PARTIAL_PRESENTATION_LIMIT when the budget flag rises so no drop
    is ever silent.
    """
    budget = _budget if _budget is not None else [0]

    def hit() -> bool:
        budget[0] += 1
        return budget[0] > _PRESENTATION_NODE_BUDGET

    exhausted = budget[0] > _PRESENTATION_NODE_BUDGET
    out: list[str] = []
    indent = "  " * _depth
    if isinstance(value, Mapping):
        for key, child in value.items():
            if hit():
                break
            if isinstance(child, (Mapping, list, tuple)):
                out.append(f"{indent}- {_render_label(key, field_labels)}:")
                if _depth + 1 < _PRESENTATION_MAX_DEPTH:
                    sub, e2 = render_business_evidence(
                        child, field_labels,
                        _budget=budget, _depth=_depth + 1,
                    )
                    out.extend(sub)
                    exhausted = exhausted or e2
                else:
                    out.append(f"{indent}  - (estrutura profunda omitida)")
            else:
                rendered = _render_value(child)
                if rendered is not None:
                    out.append(
                        f"{indent}- {_render_label(key, field_labels)}: {rendered}"
                    )
    elif isinstance(value, (list, tuple)):
        for item in value:
            if hit():
                break
            if isinstance(item, (Mapping, list, tuple)):
                if _depth + 1 < _PRESENTATION_MAX_DEPTH:
                    sub, e2 = render_business_evidence(
                        item, field_labels,
                        _budget=budget, _depth=_depth + 1,
                    )
                    if sub:
                        out.append(f"{indent}-")
                        out.extend(sub)
                    exhausted = exhausted or e2
                else:
                    out.append(f"{indent}- (estrutura profunda omitida)")
            else:
                rendered = _render_value(item)
                if rendered is not None:
                    out.append(f"{indent}- {rendered}")
    else:
        rendered = _render_value(value)
        if rendered is not None:
            out.append(f"{indent}- {rendered}")
    return out, exhausted
