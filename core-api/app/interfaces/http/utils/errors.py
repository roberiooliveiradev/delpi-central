# app/interfaces/http/utils/errors.py

from __future__ import annotations

from typing import Any
from flask import jsonify


def api_error(
    code: str,
    message: str,
    *,
    status: int = 400,
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    """
    Padrão único de erro:
    {
      "errors": [
        { "code": "...", "message": "...", "path": "..." }
      ],
      ...extra
    }
    """
    payload: dict[str, Any] = {
        "errors": [
            {
                "code": code,
                "message": message,
                "path": path,
            }
        ]
    }
    if extra:
        payload.update(extra)
    return jsonify(payload), status


# Compat: alguns controllers antigos chamavam "error_response"
# e outros usam "api_error". Mantemos ambos.
def error_response(
    code: str,
    message: str,
    *,
    status: int = 400,
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    return api_error(code, message, status=status, path=path, extra=extra)


# =========================
# Conveniências
# =========================

def unauthorized(
    message: str = "Unauthorized",
    *,
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    return api_error("unauthorized", message, status=401, path=path, extra=extra)


def forbidden(
    message: str = "Forbidden",
    *,
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    return api_error("forbidden", message, status=403, path=path, extra=extra)


def not_found(
    message: str = "Not found",
    *,
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    return api_error("not_found", message, status=404, path=path, extra=extra)


def bad_request(
    message: str = "Bad request",
    *,
    code: str = "validation_error",
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    return api_error(code, message, status=400, path=path, extra=extra)


def unprocessable(
    message: str = "Unprocessable entity",
    *,
    code: str = "unprocessable_entity",
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    # útil pra validação semântica (422)
    return api_error(code, message, status=422, path=path, extra=extra)


def conflict(
    message: str = "Conflict",
    *,
    code: str = "conflict",
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    return api_error(code, message, status=409, path=path, extra=extra)


def server_error(
    message: str = "Internal server error",
    *,
    code: str = "internal_error",
    path: str = "_global",
    extra: dict[str, Any] | None = None,
):
    return api_error(code, message, status=500, path=path, extra=extra)