# shared/delpi_auth/policy_registry.py

class PolicyRegistry:

    _registry = {}

    @classmethod
    def register(cls, name, fn):
        cls._registry[name] = fn

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)

    @classmethod
    def list(cls):
        return list(cls._registry.keys())