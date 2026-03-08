# app/interfaces/http/security/decorators.py

from functools import wraps

from app.interfaces.http.security.policy_engine import PolicyEngine


# ---------------------------------------------------------
# Registro automático de policy
# ---------------------------------------------------------
def register_policy(name: str | None = None):
    """
    Decorator para registrar automaticamente uma policy
    no PolicyEngine.
    """

    def decorator(fn):
        policy_name = name or fn.__name__

        PolicyEngine.register(policy_name, fn)

        return fn

    return decorator


# ---------------------------------------------------------
# Decorator usado nos controllers
# ---------------------------------------------------------
def policy(name: str):
    """
    Decorator usado em endpoints Flask para aplicar policy.
    """

    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            result = PolicyEngine.evaluate(name, **kwargs)

            if result is not True:
                return result

            return fn(*args, **kwargs)

        return wrapper

    return decorator