# shared/delpi_auth/decorators.py

from functools import wraps
from .policy_registry import PolicyRegistry
from .policy_engine import PolicyEngine


def register_policy(name=None):

    def decorator(fn):

        policy_name = name or fn.__name__

        PolicyRegistry.register(policy_name, fn)

        return fn

    return decorator


def policy(name, context_getter):

    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            context = context_getter()

            user = getattr(context, "user", None)

            PolicyEngine.evaluate(name, user=user, **kwargs)

            return fn(*args, **kwargs)

        return wrapper

    return decorator