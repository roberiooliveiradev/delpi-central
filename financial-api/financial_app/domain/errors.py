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


class InvalidReceivedInvoiceQuery(FinancialError):
    """Filtro ou identificador de NF-e fora do contrato do Portal Financeiro."""


class QuestorNotConfigured(FinancialError):
    """Token ou base do Questor Zen ausentes. Os demais módulos seguem no ar."""


class QuestorAuthenticationError(FinancialError):
    """O Questor Zen recusou ou não concluiu a sessão por token."""


class QuestorUnavailable(FinancialError):
    """Timeout ou indisponibilidade transitória do Questor Zen."""


class QuestorInvalidResponse(FinancialError):
    """Corpo inesperado do Questor Zen, sem detalhe do provider."""


class QuestorDocumentNotFound(FinancialError):
    """DANFE inexistente quando o provider deixa isso inequívoco."""


class NfeExportConfigurationError(FinancialError):
    """Configuração do exporter de XML NF-e inválida. Nenhum arquivo é gravado."""


class NfeXmlRejected(InvalidReceivedInvoiceQuery):
    """XML de NF-e recusado por identidade fiscal, sem incluir o documento no erro."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
