from __future__ import annotations


class ProductionControlError(Exception):
    """Erro de domínio do Portal PCP."""


class BranchAccessDenied(ProductionControlError):
    """Usuário autenticado sem permissão da filial pedida."""


class InvalidBranch(ProductionControlError):
    """Código de filial fora do domínio 01/02."""


class DelpiGatewayError(ProductionControlError):
    """Falha ao consultar a api-delpi."""


class SnapshotNotFound(ProductionControlError):
    """Snapshot da carga máquina ausente para o escopo pedido."""


class DrawingNotFound(ProductionControlError):
    """PDF do desenho indisponível ou PA fora da fila publicada."""
