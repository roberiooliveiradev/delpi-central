class AuthenticationError(Exception):
    def __init__(self, message: str = "Unauthorized"):
        self.message = message
        super().__init__(message)


class AuthorizationError(Exception):
    def __init__(self, message: str = "Forbidden"):
        self.message = message
        super().__init__(message)


class CoreApiUnavailableError(Exception):
    def __init__(self, message: str = "Authorization service unavailable"):
        self.message = message
        super().__init__(message)


class EnrichmentError(Exception):
    """Base for supplier enrichment domain failures."""


class EnrichmentIdentityMismatchError(EnrichmentError):
    """External registry identity does not match the canonical supplier."""

    def __init__(self, message: str = "External registry identity mismatch"):
        super().__init__(message)


class EnrichmentUnsupportedDocumentError(EnrichmentError):
    """CNPJ enrichment is unavailable for CPF / non-legal entities."""

    def __init__(self, message: str = "Enrichment unsupported for this document type"):
        super().__init__(message)
