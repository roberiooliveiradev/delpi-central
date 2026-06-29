from __future__ import annotations

import json
import re
from typing import Any

FIVE_WHYS_TRACK_FIELDS = ("occurrence_whys", "detection_whys")

LEGACY_OCCURRENCE_FIELDS = tuple(f"why_{index}" for index in range(1, 6))
LEGACY_DETECTION_FIELDS = tuple(f"detection_why_{index}" for index in range(1, 6))

WhyStep = dict[str, str]


def split_legacy_why_text(text: str) -> WhyStep:
    cleaned = text.strip()
    if not cleaned:
        return {"question": "", "answer": ""}
    question_index = cleaned.find("?")
    if question_index >= 0:
        return {
            "question": cleaned[: question_index + 1].strip(),
            "answer": cleaned[question_index + 1 :].strip(),
        }
    if re.match(r"^por\s*que\b", cleaned, re.IGNORECASE):
        return {"question": cleaned, "answer": ""}
    return {"question": "", "answer": cleaned}


def normalize_whys_step(item: Any) -> WhyStep | None:
    if item is None:
        return None
    if isinstance(item, dict):
        question = str(item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip()
        if not question and not answer:
            return None
        return {"question": question, "answer": answer}
    if isinstance(item, str):
        step = split_legacy_why_text(item)
        if not step["question"] and not step["answer"]:
            return None
        return step
    raise ValueError("Porquê inválido; informe texto ou objeto com question e answer.")


def normalize_whys_track(value: Any) -> list[WhyStep]:
    if value is None:
        return []
    if isinstance(value, list):
        items: list[WhyStep] = []
        for item in value:
            step = normalize_whys_step(item)
            if step is not None:
                items.append(step)
        return items
    if isinstance(value, str):
        if not value.strip():
            return []
        if "\n" in value:
            items = []
            for line in value.splitlines():
                step = normalize_whys_step(line.strip().lstrip("-•").strip())
                if step is not None:
                    items.append(step)
            return items
        step = normalize_whys_step(value.strip())
        return [step] if step is not None else []
    raise ValueError("Porquê inválido; informe lista de passos.")


def normalize_whys_list(value: Any) -> list[str]:
    """Compatibilidade legada — retorna cada passo como texto único."""
    return [format_why_step_text(step) for step in normalize_whys_track(value)]


def format_why_step_text(step: WhyStep) -> str:
    question = step.get("question", "").strip()
    answer = step.get("answer", "").strip()
    if question and answer:
        return f"{question} {answer}".strip()
    return question or answer


def format_why_step_cell(step: Any) -> str | None:
    normalized = normalize_whys_step(step)
    if normalized is None:
        return None
    question = normalized["question"]
    answer = normalized["answer"]
    if question and answer:
        return f"{question}\n{answer}"
    return question or answer or None


def _legacy_track_values(fields: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    items: list[str] = []
    for key in keys:
        raw = fields.get(key)
        if raw is None:
            continue
        cleaned = str(raw).strip()
        if cleaned:
            items.append(cleaned)
    return items


def normalize_five_whys_payload(fields: dict[str, Any]) -> dict[str, Any]:
    result = dict(fields)

    occurrence = result.get("occurrence_whys")
    if occurrence is None:
        occurrence = _legacy_track_values(result, LEGACY_OCCURRENCE_FIELDS)
    result["occurrence_whys"] = normalize_whys_track(occurrence)

    detection = result.get("detection_whys")
    if detection is None:
        detection = _legacy_track_values(result, LEGACY_DETECTION_FIELDS)
    result["detection_whys"] = normalize_whys_track(detection)

    root_cause = result.get("root_cause")
    if root_cause is not None:
        result["root_cause"] = str(root_cause).strip() or None

    for key in (*LEGACY_OCCURRENCE_FIELDS, *LEGACY_DETECTION_FIELDS):
        result.pop(key, None)

    return result


def five_whys_json(fields: dict[str, Any]) -> dict[str, str]:
    normalized = normalize_five_whys_payload(fields)
    return {
        "occurrence_whys": json.dumps(normalized.get("occurrence_whys") or [], ensure_ascii=False),
        "detection_whys": json.dumps(normalized.get("detection_whys") or [], ensure_ascii=False),
    }


def serialize_five_whys_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    if result.get("id") is not None:
        result["id"] = str(result["id"])
    if result.get("plan_id") is not None:
        result["plan_id"] = str(result["plan_id"])
    for key, value in list(result.items()):
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    result["occurrence_whys"] = normalize_whys_track(result.get("occurrence_whys"))
    result["detection_whys"] = normalize_whys_track(result.get("detection_whys"))
    root_cause = result.get("root_cause")
    if root_cause is not None:
        result["root_cause"] = str(root_cause).strip() or None
    for key in (*LEGACY_OCCURRENCE_FIELDS, *LEGACY_DETECTION_FIELDS):
        result.pop(key, None)
    return result


def five_whys_track_lines(value: Any, *, track_label: str) -> list[str]:
    items = normalize_whys_track(value)
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        question = item.get("question", "").strip()
        answer = item.get("answer", "").strip()
        if question and answer:
            lines.append(f"{track_label} — Por quê {index}: {question} {answer}")
        elif question:
            lines.append(f"{track_label} — Por quê {index}: {question}")
        elif answer:
            lines.append(f"{track_label} — Por quê {index}: {answer}")
    return lines
