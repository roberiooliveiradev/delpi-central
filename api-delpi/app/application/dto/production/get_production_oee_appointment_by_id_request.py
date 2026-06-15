from dataclasses import dataclass
from typing import Optional


@dataclass
class GetProductionOeeAppointmentByIdRequest:
    appointment_id: int
    branch: Optional[str] = None
