from abc import ABC, abstractmethod
from typing import Sequence


class ProductSafetyStockRepositoryPort(ABC):

    @abstractmethod
    def fetch_safety_stock(
        self,
        code: str,
        branches: Sequence[str],
    ) -> dict | None:
        """Cadastro do produto + estoque de segurança SBZ por filial do escopo.

        Retorna ``None`` quando o produto não existe em SB1010. Quando existe,
        ``safety_stock_by_branch`` contém apenas filiais com registro SBZ ativo
        (valor pode ser zero — distinto de ausência de registro).
        """
        pass
