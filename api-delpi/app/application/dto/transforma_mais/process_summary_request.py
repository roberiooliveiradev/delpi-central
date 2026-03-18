# app/application/dto/transforma_mais/process_summary_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessSummaryRequest:
    start_date: Optional[str]
    end_date: Optional[str]