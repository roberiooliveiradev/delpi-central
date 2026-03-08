# app/interfaces/http/security/policy_engine.py
from flask import g

from app.interfaces.http.utils.errors import unauthorized, forbidden


class PolicyEngine:
    """
    Motor de avaliação de policies.

    Mantém um registry interno de policies e executa validações
    baseadas no usuário atual (g.current_user).
    """

    _registry: dict[str, callable] = {}

    # ---------------------------------------------------------
    # Registro
    # ---------------------------------------------------------
    @classmethod
    def register(cls, name: str, fn: callable):
        cls._registry[name] = fn

    @classmethod
    def get(cls, name: str):
        return cls._registry.get(name)

    @classmethod
    def list_policies(cls):
        return list(cls._registry.keys())

    # ---------------------------------------------------------
    # Avaliação
    # ---------------------------------------------------------
    @classmethod
    def evaluate(cls, name: str, **context):

        user = getattr(g, "current_user", None)

        if not user:
            return unauthorized()

        # bypass superadmin
        if getattr(user, "is_superadmin", False):
            return True

        policy_fn = cls.get(name)

        if not policy_fn:
            raise RuntimeError(f"Policy '{name}' not registered")

        allowed = policy_fn(user=user, **context)

        if not allowed:
            return forbidden("Permission denied")

        return True