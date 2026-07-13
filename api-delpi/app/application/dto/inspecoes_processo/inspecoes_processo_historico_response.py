from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesProcessoHistoricoItemResponse:
    filial: str
    unidade: str = ""
    ordem_producao: str = ""
    codigo_produto: str = ""
    descricao_produto: str = ""
    revisao_produto: str = ""
    quantidade_op: float = 0.0
    chave_cabecalho_inspecao: str = ""
    origem_inspecao: str = ""
    qtde_ensaios: int = 0
    qtde_ensaios_aprovados: int = 0
    qtde_ensaios_reprovados: int = 0
    qtde_ensaios_tolerancia: int = 0
    qtde_operacoes: int = 0
    qtde_ensaiadores: int = 0
    resultado_inspecao_codigo: str = ""
    resultado_inspecao: str = ""
    primeira_data_medicao: str | None = None
    ultima_data_medicao: str | None = None
    ultima_hora_medicao: str | None = None
    matricula_ultimo_ensaiador: str = ""
    nome_ultimo_ensaiador: str = ""

    def to_dict(self) -> dict:
        return {
            "filial": self.filial,
            "unidade": self.unidade,
            "ordem_producao": self.ordem_producao,
            "codigo_produto": self.codigo_produto,
            "descricao_produto": self.descricao_produto,
            "revisao_produto": self.revisao_produto,
            "quantidade_op": self.quantidade_op,
            "chave_cabecalho_inspecao": self.chave_cabecalho_inspecao,
            "origem_inspecao": self.origem_inspecao,
            "qtde_ensaios": self.qtde_ensaios,
            "qtde_ensaios_aprovados": self.qtde_ensaios_aprovados,
            "qtde_ensaios_reprovados": self.qtde_ensaios_reprovados,
            "qtde_ensaios_tolerancia": self.qtde_ensaios_tolerancia,
            "qtde_operacoes": self.qtde_operacoes,
            "qtde_ensaiadores": self.qtde_ensaiadores,
            "resultado_inspecao_codigo": self.resultado_inspecao_codigo,
            "resultado_inspecao": self.resultado_inspecao,
            "primeira_data_medicao": self.primeira_data_medicao,
            "ultima_data_medicao": self.ultima_data_medicao,
            "ultima_hora_medicao": self.ultima_hora_medicao,
            "matricula_ultimo_ensaiador": self.matricula_ultimo_ensaiador,
            "nome_ultimo_ensaiador": self.nome_ultimo_ensaiador,
        }


@dataclass
class InspecoesProcessoHistoricoResponse:
    items: list[InspecoesProcessoHistoricoItemResponse]
    page: int
    page_size: int
    has_next: bool

    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "page": self.page,
            "page_size": self.page_size,
            "has_next": self.has_next,
        }
