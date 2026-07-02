from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DespesasCentroCustoFiltrosResponse:
    periodo: dict[str, str]
    filiais: list[dict[str, str]] = field(default_factory=list)
    centros_custo: list[dict[str, str]] = field(default_factory=list)
    fornecedores: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "filiais": self.filiais,
            "centros_custo": self.centros_custo,
            "fornecedores": self.fornecedores,
        }
