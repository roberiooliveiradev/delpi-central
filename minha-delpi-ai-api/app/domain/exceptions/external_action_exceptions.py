"""Erros de validação de actions externas (parâmetros/schema)."""


class ExternalActionValidationError(ValueError):
    """Falha de schema/parâmetros antes do HTTP — não é indisponibilidade de API."""

    def __init__(
        self,
        message: str,
        *,
        error_kind: str,
        missing_parameter: str | None = None,
        parameter_name: str | None = None,
    ):
        super().__init__(message)
        self.error_kind = error_kind
        self.missing_parameter = missing_parameter
        self.parameter_name = parameter_name or missing_parameter

    def to_metadata(self) -> dict:
        payload: dict = {
            "ok": False,
            "error": str(self),
            "errorKind": self.error_kind,
            "errorType": self.__class__.__name__,
            "statusCode": 0,
        }

        if self.missing_parameter:
            payload["missingParameter"] = self.missing_parameter

        if self.parameter_name and self.parameter_name != self.missing_parameter:
            payload["parameterName"] = self.parameter_name

        return payload
