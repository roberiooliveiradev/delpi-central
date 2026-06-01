from app.composition.root_composer import create_application


def test_sqlalchemy_engine_uses_pool_pre_ping():
    app = create_application()

    options = app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {}

    assert options.get("pool_pre_ping") is True
    assert int(options.get("pool_recycle") or 0) > 0
