from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesProcessoPorOperacaoItemResponse:
    filial: str
    unidade: str = ""
    codigo_produto: str = ""
    descricao_produto: str = ""
    revisao_produto: str = ""
    roteiro: str = ""
    operacao: str = ""
    recurso: str = ""
    ferramenta: str = ""
    centro_trabalho: str = ""
    descricao_operacao: str = ""
    qtde_ops: int = 0
    qtde_ensaios: int = 0
    qtde_ensaios_aprovados: int = 0
    qtde_ensaios_reprovados: int = 0
    qtde_ensaios_tolerancia: int = 0
    qtde_ops_aprovadas: int = 0
    qtde_ops_reprovadas: int = 0
    qtde_ops_tolerancia: int = 0
    qtde_ensaios_distintos: int = 0
    qtde_ensaiadores: int = 0
    primeira_data_medicao: str | None = None
    ultima_data_medicao: str | None = None
    percentual_ops_aprovadas: float = 0.0
    percentual_ops_reprovadas: float = 0.0
    percentual_ensaios_aprovados: float = 0.0
    percentual_ensaios_reprovados: float = 0.0

    def to_dict(self) -> dict:
        return {
            "filial": self.filial,
            "unidade": self.unidade,
            "codigo_produto": self.codigo_produto,
            "descricao_produto": self.descricao_produto,
            "revisao_produto": self.revisao_produto,
            "roteiro": self.roteiro,
            "operacao": self.operacao,
            "recurso": self.recurso,
            "ferramenta": self.ferramenta,
            "centro_trabalho": self.centro_trabalho,
            "descricao_operacao": self.descricao_operacao,
            "qtde_ops": self.qtde_ops,
            "qtde_ensaios": self.qtde_ensaios,
            "qtde_ensaios_aprovados": self.qtde_ensaios_aprovados,
            "qtde_ensaios_reprovados": self.qtde_ensaios_reprovados,
            "qtde_ensaios_tolerancia": self.qtde_ensaios_tolerancia,
            "qtde_ops_aprovadas": self.qtde_ops_aprovadas,
            "qtde_ops_reprovadas": self.qtde_ops_reprovadas,
            "qtde_ops_tolerancia": self.qtde_ops_tolerancia,
            "qtde_ensaios_distintos": self.qtde_ensaios_distintos,
            "qtde_ensaiadores": self.qtde_ensaiadores,
            "primeira_data_medicao": self.primeira_data_medicao,
            "ultima_data_medicao": self.ultima_data_medicao,
            "percentual_ops_aprovadas": self.percentual_ops_aprovadas,
            "percentual_ops_reprovadas": self.percentual_ops_reprovadas,
            "percentual_ensaios_aprovados": self.percentual_ensaios_aprovados,
            "percentual_ensaios_reprovados": self.percentual_ensaios_reprovados,
        }
