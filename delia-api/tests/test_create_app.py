from app.create_app import create_app


def test_application_can_be_instantiated():
    app = create_app(testing=True)
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["DEBUG"] is False
    assert app.config["SERVICE_NAME"] == "delia-api"


def test_testing_factory_does_not_enable_debug():
    app = create_app(testing=True)
    assert app.debug is False
    assert app.config["DEBUG"] is False
