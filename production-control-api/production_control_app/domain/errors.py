from __future__ import annotations


class ProductionControlError(Exception):
    """Erro de domínio do Portal PCP."""


class BranchAccessDenied(ProductionControlError):
    """Usuário autenticado sem permissão da filial pedida."""


class InvalidBranch(ProductionControlError):
    """Código de filial fora do domínio 01/02."""


class DelpiGatewayError(ProductionControlError):
    """Falha ao consultar a api-delpi."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class InvalidProductCode(ProductionControlError):
    """Código de PA fora do contrato da consulta (mínimo 8 dígitos)."""


class DetectorNotFound(ProductionControlError):
    """Detector fora do catálogo da Análise de problemas."""


class SnapshotNotFound(ProductionControlError):
    """Snapshot da carga máquina ausente para o escopo pedido."""


class DrawingNotFound(ProductionControlError):
    """PDF do desenho ausente para o PA (fonte acessível, documento não encontrado)."""


class DrawingSourceUnavailable(ProductionControlError):
    """Fonte canônica de desenhos (api-delpi / biblioteca) indisponível."""


class Product3DModelNotFound(ProductionControlError):
    """Modelo 3D ausente ou produto fora da fila publicada."""


class Product3DModelInvalid(ProductionControlError):
    """Arquivo ou código de produto inválido para o modelo 3D."""


class PublicAccessDenied(ProductionControlError):
    """Token do link público inválido ou desativado."""


class BenchSessionRequired(ProductionControlError):
    """Sessão de bancada ausente, expirada ou inválida."""


class BenchSessionConflict(ProductionControlError):
    """Já existe sessão ativa conflitante no posto."""


class ProductionRunConflict(ProductionControlError):
    """Já existe run ativo no posto ou transição inválida."""


class ProductionRunNotFound(ProductionControlError):
    """Run inexistente ou fora do escopo do posto."""


class PulseDeviceUnavailable(ProductionControlError):
    """Nenhum device Pulse elegível / snapshot indisponível para o posto."""


class PulseGatewayError(ProductionControlError):
    """Falha ao consultar o production-pulse-api."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class InvalidMesEvent(ProductionControlError):
    """Evento MES inválido: estado, origem, timestamps ou confirmação incoerentes."""


class MesStateConflict(ProductionControlError):
    """Já existe evento de estado aberto no posto."""


class DowntimeConflict(ProductionControlError):
    """Já existe parada aberta no posto."""


class DowntimeNotFound(ProductionControlError):
    """Parada inexistente ou já encerrada para a operação pedida."""


class DowntimeClassificationRequired(ProductionRunConflict):
    """Resume/Stop bloqueado: parada MES aberta ainda sem motivo classificado."""


class DowntimeReasonNotFound(ProductionControlError):
    """Motivo de parada inexistente no catálogo."""


class DowntimeReasonConflict(ProductionControlError):
    """Code duplicado ou operação proibida sobre motivo protegido."""


class InvalidDowntimeReason(ProductionControlError):
    """Dados administrativos do motivo fora do contrato do catálogo."""


class OperatorNotFound(ProductionControlError):
    """Matrícula inexistente no diretório de colaboradores (Portal RH 404)."""


class OperatorDirectoryUnavailable(ProductionControlError):
    """Diretório de colaboradores indisponível (timeout/rede/5xx/config)."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OperatorDirectoryUnauthorized(OperatorDirectoryUnavailable):
    """Credencial S2S do diretório rejeitada pelo Portal RH (401/403)."""


class OperatorDirectoryContractError(ProductionControlError):
    """Resposta 200 do Portal RH fora do contrato de colaborador."""


class OperatorInactive(ProductionControlError):
    """Matrícula existe, mas o colaborador está inativo no cadastro (C3)."""


class InvalidOperatorRegistration(ProductionControlError):
    """Matrícula fora do contrato textual (vazia ou > 30 caracteres)."""


class InvalidOperatorFeedbackType(ProductionControlError):
    """Tipo de feedback fora do catálogo suportado pelo domínio."""


class InvalidOperatorFeedbackReason(ProductionControlError):
    """Motivo de feedback fora do catálogo suportado pelo domínio."""


class OperatorFeedbackConflict(ProductionControlError):
    """Já existe impedimento ativo igual para a mesma OP/operação."""


class OperatorFeedbackNotFound(ProductionControlError):
    """Feedback inexistente para o identificador informado."""


class OperatorFeedbackStateError(ProductionControlError):
    """Transição de lifecycle inválida (ex.: reconhecer um resolvido)."""
