from __future__ import annotations

from dataclasses import dataclass, field

from app.application.dto.financeiro_inadimplencia.clientes_response import (
    InadimplenciaPagination,
)


@dataclass
class InadimplenciaTituloItem:
    filial: str
    prefixo: str
    numero: str
    parcela: str
    tipo: str
    cliente_codigo: str
    loja: str
    nome_cliente: str
    nome_reduzido: str
    data_emissao: str
    data_vencimento_real: str
    data_baixa: str
    valor_titulo: float
    pago_em_dia: bool
    dias_atraso: int
    faixa_atraso: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "filial": self.filial,
            "prefixo": self.prefixo,
            "numero": self.numero,
            "parcela": self.parcela,
            "tipo": self.tipo,
            "cliente_codigo": self.cliente_codigo,
            "loja": self.loja,
            "nome_cliente": self.nome_cliente,
            "nome_reduzido": self.nome_reduzido,
            "data_emissao": self.data_emissao,
            "data_vencimento_real": self.data_vencimento_real,
            "data_baixa": self.data_baixa,
            "valor_titulo": self.valor_titulo,
            "pago_em_dia": self.pago_em_dia,
            "dias_atraso": self.dias_atraso,
            "faixa_atraso": self.faixa_atraso,
        }


@dataclass
class InadimplenciaTitulosResponse:
    periodo: dict[str, str]
    pagination: InadimplenciaPagination
    sort: dict[str, str]
    items: list[InadimplenciaTituloItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "pagination": self.pagination.to_dict(),
            "sort": self.sort,
            "items": [item.to_dict() for item in self.items],
        }
