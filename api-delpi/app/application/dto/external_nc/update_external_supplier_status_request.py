# app/application/dto/external_nc/update_external_supplier_status_request.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class UpdateExternalSupplierStatusRequest:
    nonconformity_id: str
    supplier_status: str
    actor_user_id: str
    justification: Optional[str] = None