from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.inspecoes_processo.inspecoes_processo_historico_response import (
    InspecoesProcessoHistoricoItemResponse,
)


@dataclass
class InspecoesProcessoHistoricoDetalheItemResponse:
    inspecao_id: str = ""
    ensaio_id: str = ""
    filial: str = ""
    unidade: str = ""
    ordem_producao: str = ""
    codigo_produto: str = ""
    descricao_produto: str = ""
    revisao_produto: str = ""
    roteiro: str = ""
    operacao: str = ""
    recurso: str = ""
    ferramenta: str = ""
    centro_trabalho: str = ""
    descricao_operacao: str = ""
    laboratorio: str = ""
    codigo_ensaio: str = ""
    nome_ensaio: str = ""
    especificacao_textual: str | None = None
    valor_nominal: str | None = None
    limite_inferior_especificacao: str | None = None
    limite_superior_especificacao: str | None = None
    limite_inferior_controle: str | None = None
    limite_superior_controle: str | None = None
    regra_min_max: str | None = None
    unidade_especificacao: str | None = None
    especificacao_esperada: str | None = None
    medicao_textual: str | None = None
    medicao_numerica_a: float | None = None
    medicao_numerica_n: float | None = None
    medicao_numerica: str | None = None
    modo_medicao_numerica: str | None = None
    fonte_medicao: str | None = None
    resultado_codigo: str = ""
    resultado: str = ""
    data_medicao: str | None = None
    hora_medicao: str | None = None
    matricula_ensaiador: str = ""
    nome_ensaiador: str = ""
    chave_medicao: str | None = None
    qpr_recno: int | None = None

    def to_dict(self) -> dict:
        return {
            "inspecao_id": self.inspecao_id,
            "ensaio_id": self.ensaio_id,
            "filial": self.filial,
            "unidade": self.unidade,
            "ordem_producao": self.ordem_producao,
            "codigo_produto": self.codigo_produto,
            "descricao_produto": self.descricao_produto,
            "revisao_produto": self.revisao_produto,
            "roteiro": self.roteiro,
            "operacao": self.operacao,
            "recurso": self.recurso,
            "ferramenta": self.ferramenta,
            "centro_trabalho": self.centro_trabalho,
            "descricao_operacao": self.descricao_operacao,
            "laboratorio": self.laboratorio,
            "codigo_ensaio": self.codigo_ensaio,
            "nome_ensaio": self.nome_ensaio,
            "especificacao_textual": self.especificacao_textual,
            "valor_nominal": self.valor_nominal,
            "limite_inferior_especificacao": self.limite_inferior_especificacao,
            "limite_superior_especificacao": self.limite_superior_especificacao,
            "limite_inferior_controle": self.limite_inferior_controle,
            "limite_superior_controle": self.limite_superior_controle,
            "regra_min_max": self.regra_min_max,
            "unidade_especificacao": self.unidade_especificacao,
            "especificacao_esperada": self.especificacao_esperada,
            "medicao_textual": self.medicao_textual,
            "medicao_numerica_a": self.medicao_numerica_a,
            "medicao_numerica_n": self.medicao_numerica_n,
            "medicao_numerica": self.medicao_numerica,
            "modo_medicao_numerica": self.modo_medicao_numerica,
            "fonte_medicao": self.fonte_medicao,
            "resultado_codigo": self.resultado_codigo,
            "resultado": self.resultado,
            "data_medicao": self.data_medicao,
            "hora_medicao": self.hora_medicao,
            "matricula_ensaiador": self.matricula_ensaiador,
            "nome_ensaiador": self.nome_ensaiador,
            "chave_medicao": self.chave_medicao,
            "qpr_recno": self.qpr_recno,
        }


@dataclass
class InspecoesProcessoHistoricoDetalheResponse:
    cabecalho: InspecoesProcessoHistoricoItemResponse
    items: list[InspecoesProcessoHistoricoDetalheItemResponse]
    page: int
    page_size: int
    has_next: bool

    def to_dict(self) -> dict:
        return {
            "cabecalho": self.cabecalho.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "page": self.page,
            "page_size": self.page_size,
            "has_next": self.has_next,
        }
