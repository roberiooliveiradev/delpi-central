class AuthenticationError(Exception):
    code = "unauthorized"
    message = "Authentication required"


class InvalidTokenError(AuthenticationError):
    code = "invalid_token"
    message = "Invalid token"


class InvalidClaimsError(AuthenticationError):
    code = "invalid_claims"
    message = "Token missing required claims"
