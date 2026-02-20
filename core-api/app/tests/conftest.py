import pytest
from app.create_app import create_app
from app.extensions.db import db


# ==========================================================
# APP
# ==========================================================

@pytest.fixture(scope="function")
def app():

    app = create_app("testing")

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ==========================================================
# SESSION
# ==========================================================

@pytest.fixture(scope="function")
def db_session(app):
    with app.app_context():
        yield db.session