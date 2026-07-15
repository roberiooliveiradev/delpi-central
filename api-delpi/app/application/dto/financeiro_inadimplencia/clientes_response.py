from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InadimplenciaClienteItem:
    cliente_codigo: str
    loja: str
    nome_cliente: str
    nome_reduzido: str
    total_titulos: int
    titulos_em_dia: int
    titulos_atraso: int
    valor_total: float
    valor_atraso: float
    percentual_em_dia_qtd: float
    percentual_em_dia_valor: float

    def to_dict(self) -> dict:
        return {
            "cliente_codigo": self.cliente_codigo,
            "loja": self.loja,
            "nome_cliente": self.nome_cliente,
            "nome_reduzido": self.nome_reduzido,
            "total_titulos": self.total_titulos,
            "titulos_em_dia": self.titulos_em_dia,
            "titulos_atraso": self.titulos_atraso,
            "valor_total": self.valor_total,
            "valor_atraso": self.valor_atraso,
            "percentual_em_dia_qtd": self.percentual_em_dia_qtd,
            "percentual_em_dia_valor": self.percentual_em_dia_valor,
        }


@dataclass
class InadimplenciaPagination:
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }


@dataclass
class InadimplenciaClientesResponse:
    periodo: dict[str, str]
    pagination: InadimplenciaPagination
    sort: dict[str, str]
    items: list[InadimplenciaClienteItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "pagination": self.pagination.to_dict(),
            "sort": self.sort,
            "items": [item.to_dict() for item in self.items],
        }
