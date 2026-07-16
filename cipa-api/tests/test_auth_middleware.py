from types import SimpleNamespace

from cipa_app.middleware.auth_middleware import _is_public, _strip_root_path


class _FakeScope(dict):
    pass


class _FakeUrl:
    def __init__(self, path: str):
        self.path = path


class _FakeRequest:
    def __init__(self, path: str, root_path: str = "/apps/cipa-api"):
        self.url = _FakeUrl(path)
        self.scope = {"root_path": root_path}


def test_strip_root_path():
    request = _FakeRequest("/apps/cipa-api/health")
    assert _strip_root_path(request) == "/health"


def test_health_is_public_with_root_path():
    request = _FakeRequest("/apps/cipa-api/health")
    assert _is_public(_strip_root_path(request)) is True


def test_access_is_not_public():
    request = _FakeRequest("/apps/cipa-api/access")
    assert _is_public(_strip_root_path(request)) is False
