from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InadimplenciaResumoResponse:
    periodo: dict[str, str]
    totais: dict[str, float | int]
    indicadores: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "totais": self.totais,
            "indicadores": self.indicadores,
        }
