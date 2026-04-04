# shared/delpi_auth/decorators.py
from functools import wraps
import inspect

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
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                context = context_getter()
                user = getattr(context, "user", None)

                PolicyEngine.evaluate(name, user=user, **kwargs)

                return await fn(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            context = context_getter()
            user = getattr(context, "user", None)

            PolicyEngine.evaluate(name, user=user, **kwargs)

            return fn(*args, **kwargs)

        return sync_wrapper

    return decorator