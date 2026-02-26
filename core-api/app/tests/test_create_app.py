# app/tests/test_create_app.py

import pytest
from app.create_app import create_app
from app.extensions.db import db


def test_create_app_testing_config():
    app = create_app("testing")

    assert app is not None
    assert app.config["TESTING"] is True


def test_create_app_registers_blueprints():
    app = create_app("testing")

    routes = [rule.rule for rule in app.url_map.iter_rules()]

    # endpoints principais
    assert "/health" in routes
    assert any("/dashboard" in r for r in routes)
    assert any("/notifications" in r for r in routes)


def test_db_initialized():
    app = create_app("testing")

    with app.app_context():
        # garante que o db está vinculado corretamente
        assert db.engine is not None