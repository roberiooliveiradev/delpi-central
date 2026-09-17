from flask import Flask

from app.composition.root_composer import create_application


def create_app(*, testing: bool = False) -> Flask:
    return create_application(testing=testing)
