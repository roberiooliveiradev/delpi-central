from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesEntradaRejeitadaEnsaiadorItemResponse:
    branch: str
    inspector_registration: str
    inspector_name: str
    inspector_login: str
    rejected_inspections: int

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "inspector_registration": self.inspector_registration,
            "inspector_name": self.inspector_name,
            "inspector_login": self.inspector_login,
            "rejected_inspections": self.rejected_inspections,
        }


@dataclass
class InspecoesEntradaRejeitadasEnsaiadorResponse:
    branch: str
    items: list[InspecoesEntradaRejeitadaEnsaiadorItemResponse]
    total_inspectors: int
    total_rejected: int

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "items": [item.to_dict() for item in self.items],
            "total_inspectors": self.total_inspectors,
            "total_rejected": self.total_rejected,
        }
