# app/domain/ports/shared_quality/sequential_code_generator.py
from __future__ import annotations

from abc import ABC, abstractmethod


class SequentialCodeGeneratorPort(ABC):
    @abstractmethod
    def next_code(self, sequence_key: str) -> str:
        raise NotImplementedError