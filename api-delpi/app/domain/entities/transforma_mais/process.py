# app/entities/transforma_mais_process.py
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Process:
    id: str
    name_process: str
    filial_id: Optional[str] = None
    sector_name: Optional[str] = None
    daily_savings: Optional[float] = None
    payback_months: Optional[float] = None
    status: Optional[str] = None
    implementetion_date: Optional[str] = None
    processo_id: Optional[str] = None
    instancia_id: Optional[str] = None
    codigo_processo: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)