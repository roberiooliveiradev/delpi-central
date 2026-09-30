from __future__ import annotations

import uuid
from datetime import datetime, timezone

from bpmn_modeler.application.ports import ClockPort, IdGeneratorPort


class SystemClock(ClockPort):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class UuidGenerator(IdGeneratorPort):
    def new_model_id(self) -> str:
        return str(uuid.uuid4())

    def new_revision_id(self) -> str:
        return str(uuid.uuid4())

    def new_bpmn_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"
