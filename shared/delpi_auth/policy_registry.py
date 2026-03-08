class PolicyRegistry:

    _registry = {}

    @classmethod
    def register(cls, name: str, fn):
        cls._registry[name] = fn

    @classmethod
    def get(cls, name: str):
        return cls._registry.get(name)