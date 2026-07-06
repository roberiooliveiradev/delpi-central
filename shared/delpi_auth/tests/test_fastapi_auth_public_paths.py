from delpi_auth.middleware.fastapi_auth import is_public_path


def test_root_health_paths_are_public():
    assert is_public_path("/health") is True
    assert is_public_path("/apps/api-delpi/health") is True


def test_nested_health_paths_are_not_public():
    assert is_public_path("/retrabalhos/health") is False
    assert is_public_path("/apps/api-delpi/retrabalhos/health") is False
