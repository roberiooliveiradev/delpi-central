from __future__ import annotations


class FinancialError(Exception):
    """Erro de domínio do Portal Financeiro."""


class BranchAccessDenied(FinancialError):
    """Usuário autenticado sem permissão da filial pedida."""


class InvalidBranch(FinancialError):
    """Código de filial fora do domínio 01/02."""


class InvalidPeriod(FinancialError):
    """Intervalo de datas inválido ou incompleto."""


class DelpiGatewayError(FinancialError):
    """Falha ao consultar a api-delpi."""


class StrategicIndicatorsGatewayError(FinancialError):
    """Falha ao consultar o strategic-indicators-api."""
