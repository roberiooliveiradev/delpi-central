from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InadimplenciaMensalItem:
    mes: str
    ano_mes: str
    total_titulos: int
    titulos_em_dia: int
    titulos_atraso: int
    valor_total: float
    valor_em_dia: float
    valor_atraso: float
    percentual_em_dia_qtd: float
    percentual_em_dia_valor: float

    def to_dict(self) -> dict:
        return {
            "mes": self.mes,
            "ano_mes": self.ano_mes,
            "total_titulos": self.total_titulos,
            "titulos_em_dia": self.titulos_em_dia,
            "titulos_atraso": self.titulos_atraso,
            "valor_total": self.valor_total,
            "valor_em_dia": self.valor_em_dia,
            "valor_atraso": self.valor_atraso,
            "percentual_em_dia_qtd": self.percentual_em_dia_qtd,
            "percentual_em_dia_valor": self.percentual_em_dia_valor,
        }


@dataclass
class InadimplenciaMensalResponse:
    periodo: dict[str, str]
    items: list[InadimplenciaMensalItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "items": [item.to_dict() for item in self.items],
        }
