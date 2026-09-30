from delpi_mes_app.core.responses import fail
from delpi_mes_app.domain.errors import (
    BranchAccessDenied,
    HumanPrincipalRequired,
    InvalidBranch,
    MesSourceConflict,
    MesSourceInvalidResponse,
    MesSourceNotFound,
    MesSourceUnauthorized,
    MesSourceUnavailable,
    MesSourceValidationError,
)


def fail_from_exception(exc: Exception):
    if isinstance(exc, MesSourceNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, MesSourceConflict):
        return fail(str(exc), 409)
    if isinstance(exc, (InvalidBranch, MesSourceValidationError, ValueError)):
        return fail(str(exc), 422)
    if isinstance(exc, (BranchAccessDenied, HumanPrincipalRequired, PermissionError)):
        return fail(str(exc), 403)
    if isinstance(exc, MesSourceUnauthorized):
        return fail("Integração MES indisponível por falha de autorização.", 503)
    if isinstance(exc, MesSourceUnavailable):
        return fail(str(exc), 503)
    if isinstance(exc, MesSourceInvalidResponse):
        return fail(str(exc), 502)
    raise exc
