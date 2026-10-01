from flask import Flask

from app.composition.root_composer import create_application


def create_app(
    *,
    testing: bool = False,
    platform_access_provider=None,
    model_invocation_port=None,
    interaction_turn_handler=None,
) -> Flask:
    return create_application(
        testing=testing,
        platform_access_provider=platform_access_provider,
        model_invocation_port=model_invocation_port,
        interaction_turn_handler=interaction_turn_handler,
    )
