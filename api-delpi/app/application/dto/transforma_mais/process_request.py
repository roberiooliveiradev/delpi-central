# app/application/dto/transforma_mais/process_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessRequest:
    id: Optional[str]
    name_process: Optional[str]
    sector_name: Optional[str]
    status: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]