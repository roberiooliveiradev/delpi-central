"""Porta de elegibilidade de cliente TOTVS (SA1) para o domínio de Carteiras.

Elegível = existe em SA1, não excluído logicamente e não bloqueado
(`A1_MSBLQL <> '1'`). Fornecedores (SA2) com mesmo código/loja não são
clientes: a existência precisa ser resolvida na SA1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class CustomerEligibility:
    exists: bool
    active: bool


class CustomerEligibilityPort(ABC):
    @abstractmethod
    def lookup(
        self,
        customers: Sequence[tuple[str, str]],
    ) -> Mapping[tuple[str, str], CustomerEligibility]:
        """Resolve elegibilidade por par (código, loja) já normalizado."""
        raise NotImplementedError
