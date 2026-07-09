import pytest

from app.composition.root_composer import create_application
from app.infrastructure.config.settings import Settings


def test_sqlalchemy_engine_uses_pool_pre_ping(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(Settings, "DATABASE_URL", "sqlite:///:memory:")

    app = create_application()

    options = app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {}

    assert options.get("pool_pre_ping") is True
    assert int(options.get("pool_recycle") or 0) > 0
