class MesError(Exception):
    pass


class InvalidBranch(MesError):
    pass


class BranchAccessDenied(MesError):
    pass


class HumanPrincipalRequired(MesError):
    pass


class MesSourceUnavailable(MesError):
    pass


class MesSourceUnauthorized(MesError):
    pass


class MesSourceNotFound(MesError):
    pass


class MesSourceValidationError(MesError):
    pass


class MesSourceInvalidResponse(MesError):
    pass
