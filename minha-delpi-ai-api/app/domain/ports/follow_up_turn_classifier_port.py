"""Port — classificação residual de follow-up (enum apenas, sem tool-pick)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class FollowUpTurnClassifierPort(ABC):
    """Classifica a mensagem em um label do catálogo `follow_up_turn.classifierLabels`."""

    @abstractmethod
    def classify(
        self,
        message: str,
        last_action_summary: dict[str, Any] | None = None,
    ) -> str | None:
        raise NotImplementedError
