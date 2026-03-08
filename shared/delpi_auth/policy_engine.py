from .policy_registry import PolicyRegistry


def evaluate_policy(name: str, user: dict, **kwargs):

    policy = PolicyRegistry.get(name)

    if not policy:
        raise Exception(f"Policy '{name}' not registered")

    return policy(user=user, **kwargs)