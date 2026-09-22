class HelpdeskError(Exception):
    code = "helpdesk_error"
    status_code = 400


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
