from flask import Flask

from app.composition.root_composer import create_application


def create_app() -> Flask:
    return create_application()
