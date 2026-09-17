from flask import Flask

from app.composition.root_composer import create_application


def create_app(*, testing: bool = False, platform_access_provider=None) -> Flask:
    return create_application(
        testing=testing,
        platform_access_provider=platform_access_provider,
    )
