from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MiniApplicatorTool:
    id: int
    codigo: str
    descricao: str
    grupo: str = ""
    bloqueado: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "descricao": self.descricao,
            "grupo": self.grupo,
            "bloqueado": self.bloqueado,
        }
