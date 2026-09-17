import inspect
import sys

from app.application import health as health_module
from app.create_app import create_app


FORBIDDEN_MODULE_FRAGMENTS = (
    "minha_delpi_ai",
    "minha-delpi-ai",
    "minha_delpi_chat",
    "minha-delpi-chat",
    "minha_delpi_copilot",
    "minha-delpi-copilot",
)


def test_create_app_does_not_import_chat_runtime():
    create_app(testing=True)
    offenders = [
        name
        for name in sys.modules
        if any(fragment in name for fragment in FORBIDDEN_MODULE_FRAGMENTS)
    ]
    assert offenders == []


def test_application_health_module_does_not_depend_on_flask():
    source = inspect.getsource(health_module)
    assert "flask" not in source.lower()
    assert "sqlalchemy" not in source.lower()
