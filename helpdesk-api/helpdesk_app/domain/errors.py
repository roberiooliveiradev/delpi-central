class HelpdeskError(Exception):
    code = "helpdesk_error"
    status_code = 400
    details: dict = {}


class PortalForbidden(HelpdeskError):
    code = "forbidden"
    status_code = 403


class LinkRequired(HelpdeskError):
    code = "glpi_link_required"
    status_code = 409


class InvalidOAuthState(HelpdeskError):
    code = "invalid_oauth_state"
    status_code = 400


class MissingIdempotencyKey(HelpdeskError):
    code = "idempotency_key_required"
    status_code = 400


class IdempotencyInFlight(HelpdeskError):
    """A prior execution under this key may have persisted its write.

    Fail closed: never re-execute blindly. The caller must reconcile
    through an authoritative read before retrying (a new key means a
    new intent — reusing it would risk duplication either way).
    """

    code = "idempotency_in_flight"
    status_code = 409

    def __init__(
        self,
        message: str,
        *,
        claimed_at=None,
        intent: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.details = {
            "claimed_at": claimed_at.isoformat() if claimed_at else None,
            "intent": intent,
        }


class GlpiUnauthorized(HelpdeskError):
    code = "glpi_link_required"
    status_code = 409


class GlpiForbidden(HelpdeskError):
    code = "glpi_forbidden"
    status_code = 403


class GlpiNotFound(HelpdeskError):
    code = "not_found"
    status_code = 404


class GlpiUnavailable(HelpdeskError):
    code = "glpi_unavailable"
    status_code = 502


class GlpiValidation(HelpdeskError):
    code = "validation_error"
    status_code = 422


class GlpiFeatureDisabled(HelpdeskError):
    code = "glpi_feature_disabled"
    status_code = 503


class InstitutionalReadDenied(HelpdeskError):
    code = "institutional_read_denied"
    status_code = 403


class InstitutionalCredentialInvalid(HelpdeskError):
    code = "institutional_credential_invalid"
    status_code = 401


class InstitutionalReaderUnavailable(HelpdeskError):
    code = "institutional_reader_unavailable"
    status_code = 503
