from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesProcessoPorEnsaiadorItemResponse:
    filial: str
    unidade: str = ""
    matricula_ensaiador: str = ""
    nome_ensaiador: str = ""
    login_ensaiador: str | None = None
    qtde_ops: int = 0
    qtde_ensaios: int = 0
    qtde_ensaios_aprovados: int = 0
    qtde_ensaios_reprovados: int = 0
    qtde_ensaios_tolerancia: int = 0
    qtde_ops_aprovadas: int = 0
    qtde_ops_reprovadas: int = 0
    qtde_produtos: int = 0
    qtde_operacoes: int = 0
    qtde_ensaios_distintos: int = 0
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
            "matricula_ensaiador": self.matricula_ensaiador,
            "nome_ensaiador": self.nome_ensaiador,
            "login_ensaiador": self.login_ensaiador,
            "qtde_ops": self.qtde_ops,
            "qtde_ensaios": self.qtde_ensaios,
            "qtde_ensaios_aprovados": self.qtde_ensaios_aprovados,
            "qtde_ensaios_reprovados": self.qtde_ensaios_reprovados,
            "qtde_ensaios_tolerancia": self.qtde_ensaios_tolerancia,
            "qtde_ops_aprovadas": self.qtde_ops_aprovadas,
            "qtde_ops_reprovadas": self.qtde_ops_reprovadas,
            "qtde_produtos": self.qtde_produtos,
            "qtde_operacoes": self.qtde_operacoes,
            "qtde_ensaios_distintos": self.qtde_ensaios_distintos,
            "primeira_data_medicao": self.primeira_data_medicao,
            "ultima_data_medicao": self.ultima_data_medicao,
            "percentual_ops_aprovadas": self.percentual_ops_aprovadas,
            "percentual_ops_reprovadas": self.percentual_ops_reprovadas,
            "percentual_ensaios_aprovados": self.percentual_ensaios_aprovados,
            "percentual_ensaios_reprovados": self.percentual_ensaios_reprovados,
        }
