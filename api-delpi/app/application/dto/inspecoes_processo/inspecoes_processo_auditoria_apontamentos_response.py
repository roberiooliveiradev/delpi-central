from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesProcessoAuditoriaApontamentoItemResponse:
    filial: str
    cod_operador: str = ""
    login_operador: str = ""
    nome_operador: str = ""
    op: str = ""
    produto: str = ""
    descricao_produto: str = ""
    revisao_produto: str = ""
    operacao: str = ""
    centro_trabalho: str = ""
    data_producao: str | None = None
    hora_inicio: str | None = None
    hora_final: str | None = None
    qtd_apontamentos: int = 0
    operador_inspecionou: bool = False
    tem_inspecao_na_op_operacao: bool = False
    tem_inspecao_amarrada: bool = False
    tem_inspecao_executada: bool = False

    def to_dict(self) -> dict:
        return {
            "filial": self.filial,
            "cod_operador": self.cod_operador,
            "login_operador": self.login_operador,
            "nome_operador": self.nome_operador,
            "op": self.op,
            "produto": self.produto,
            "descricao_produto": self.descricao_produto,
            "revisao_produto": self.revisao_produto,
            "operacao": self.operacao,
            "centro_trabalho": self.centro_trabalho,
            "data_producao": self.data_producao,
            "hora_inicio": self.hora_inicio,
            "hora_final": self.hora_final,
            "qtd_apontamentos": self.qtd_apontamentos,
            "operador_inspecionou": self.operador_inspecionou,
            "tem_inspecao_na_op_operacao": self.tem_inspecao_na_op_operacao,
            "tem_inspecao_amarrada": self.tem_inspecao_amarrada,
            "tem_inspecao_executada": self.tem_inspecao_executada,
        }


@dataclass
class InspecoesProcessoAuditoriaApontamentosSummaryResponse:
    operadores_pendentes: int = 0
    apontamentos_pendentes: int = 0
    ops_operacoes_pendentes: int = 0
    apontamentos_com_inspecao: int = 0
    apontamentos_total: int = 0

    def to_dict(self) -> dict:
        return {
            "operadores_pendentes": self.operadores_pendentes,
            "apontamentos_pendentes": self.apontamentos_pendentes,
            "ops_operacoes_pendentes": self.ops_operacoes_pendentes,
            "apontamentos_com_inspecao": self.apontamentos_com_inspecao,
            "apontamentos_total": self.apontamentos_total,
        }


@dataclass
class InspecoesProcessoAuditoriaApontamentosResponse:
    summary: InspecoesProcessoAuditoriaApontamentosSummaryResponse
    items: list[InspecoesProcessoAuditoriaApontamentoItemResponse]
    page: int
    page_size: int
    has_next: bool
    data: str

    def to_dict(self) -> dict:
        return {
            "summary": self.summary.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "page": self.page,
            "page_size": self.page_size,
            "has_next": self.has_next,
            "data": self.data,
        }
