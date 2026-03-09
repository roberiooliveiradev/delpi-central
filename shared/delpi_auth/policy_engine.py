# shared/delpi_auth/policy_engine.py

from .policy_registry import PolicyRegistry


class PolicyEngine:

    @staticmethod
    def evaluate(name, user=None, **context):

        if not user:
            raise Exception("Unauthorized")

        if getattr(user, "is_superadmin", False):
            return True

        policy = PolicyRegistry.get(name)

        if not policy:
            raise RuntimeError(f"Policy '{name}' not registered")

        allowed = policy(user=user, **context)

        if not allowed:
            raise Exception("Forbidden")

        return True