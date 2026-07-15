from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InadimplenciaFaixaAtrasoItem:
    codigo: str
    rotulo: str
    ordem: int
    quantidade: int
    valor: float
    percentual_quantidade: float
    percentual_valor: float

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "rotulo": self.rotulo,
            "ordem": self.ordem,
            "quantidade": self.quantidade,
            "valor": self.valor,
            "percentual_quantidade": self.percentual_quantidade,
            "percentual_valor": self.percentual_valor,
        }


@dataclass
class InadimplenciaFaixasAtrasoResponse:
    periodo: dict[str, str]
    items: list[InadimplenciaFaixaAtrasoItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "items": [item.to_dict() for item in self.items],
        }
