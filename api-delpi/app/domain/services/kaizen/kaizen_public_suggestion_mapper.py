"""Mapeia sugestão pública (Forms/planilha) → campos de create_record Kaizen."""

from __future__ import annotations

from datetime import date
from typing import Any


def _clip(value: str, max_len: int) -> str:
    text = " ".join(value.split()).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def build_suggestion_record_fields(
    *,
    proposer_name: str,
    sector: str,
    employee_registration: str,
    work_center_or_location: str,
    problem_description: str,
    proposed_solution: str,
    branch_code: str = "01",
) -> dict[str, Any]:
    name = _clip(proposer_name, 200)
    location = _clip(work_center_or_location, 200)
    problem = _clip(problem_description, 4000)
    solution = _clip(proposed_solution, 4000)
    sector_clean = _clip(sector, 200)
    registration = _clip(employee_registration, 50)

    title_seed = f"{location}: {problem}" if location else problem
    title = _clip(title_seed, 500) or f"Sugestão Kaizen — {name}"

    notes_parts = []
    if registration:
        notes_parts.append(f"Cadastro: {registration}")
    notes_parts.append("Origem: formulário público de sugestão.")

    return {
        "branch_code": branch_code if branch_code in ("01", "02") else "01",
        "title": title,
        "accountable": name or None,
        "sector": sector_clean or None,
        "status": "recebido",
        "date_idea_received": date.today().isoformat(),
        "process_description": location or None,
        "problem_description": problem or None,
        "improvement_description": solution or None,
        "notes": " | ".join(notes_parts),
        "savings_type": "qualitativo",
        "participants": [{"name": name, "role": "responsavel"}] if name else [],
    }
