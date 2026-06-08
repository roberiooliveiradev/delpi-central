"""Helpers para decoradores de rota com examples OpenAPI."""

from __future__ import annotations

from typing import Any


def openapi_example_response(example: dict[str, Any]) -> dict[str, Any]:
    """Injeta example em 200/application/json (preservado por custom_openapi)."""
    return {
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "example": example,
                    }
                }
            }
        }
    }
