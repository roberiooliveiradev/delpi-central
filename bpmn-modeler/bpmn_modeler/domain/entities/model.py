from __future__ import annotations

from dataclasses import dataclass

from .working_copy import WorkingCopy


@dataclass(slots=True)
class Model:
    """Logical identity of a BPMN model and its current working copy."""

    id: str
    working_copy: WorkingCopy

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("model id must not be empty")
