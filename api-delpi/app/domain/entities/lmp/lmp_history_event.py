from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class LMPHistoryEvent:
    revision: str
    process_code: str
    stage_code: str
    process_description: Optional[str] = None
    stage_description: Optional[str] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    limit_date: Optional[str] = None
    limit_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    history_flag: Optional[str] = None
    is_engineering: bool = False
    next_revision: Optional[str] = None
    next_process_code: Optional[str] = None
    next_stage_code: Optional[str] = None
    next_start_date: Optional[str] = None
    previous_revision: Optional[str] = None
    previous_process_code: Optional[str] = None
    previous_stage_code: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
