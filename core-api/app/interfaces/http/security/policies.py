# app/interfaces/http/security/policies.py

"""
Policies da aplicação.

Aqui ficam regras de autorização mais complexas que
não devem ficar dentro dos controllers.
"""

from app.interfaces.http.security.decorators import register_policy


# ==========================================================
# RBAC MANAGEMENT
# ==========================================================

@register_policy()
def can_manage_rbac(user, **_):
    """
    Permite administrar RBAC (roles, groups, permissions).
    """
    return "rbac.manage" in getattr(user, "permissions", [])


# ==========================================================
# USER MANAGEMENT
# ==========================================================

@register_policy()
def can_manage_users(user, **_):
    """
    Permite administrar usuários.
    """
    return "users.manage" in getattr(user, "permissions", [])


@register_policy()
def can_delete_user(user, user_id=None, **_):
    """
    Policy para deletar usuário.

    Regras:
    - precisa de users.manage
    - não pode deletar a si mesmo
    """

    permissions = getattr(user, "permissions", [])

    if "users.manage" not in permissions:
        return False

    if user_id and str(user.id) == str(user_id):
        return False

    return True


# ==========================================================
# GROUP MANAGEMENT
# ==========================================================

@register_policy()
def can_manage_groups(user, **_):
    """
    Permite administrar grupos.
    """
    return "groups.manage" in getattr(user, "permissions", [])


# ==========================================================
# ROLE MANAGEMENT
# ==========================================================

@register_policy()
def can_manage_roles(user, **_):
    """
    Permite administrar roles.
    """
    return "roles.manage" in getattr(user, "permissions", [])