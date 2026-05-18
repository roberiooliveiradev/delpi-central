from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import Response
from fastapi.responses import JSONResponse

from si_app.shared.json_encoding import to_json_safe

logger = logging.getLogger("strategic_indicators.http")

READ_CACHE_MAX_AGE_SECONDS = 300


def run_logged_read_route(
    *,
    route: str,
    competence: str | None,
    department_id: str | None,
    branch: str | None,
    months: int | None,
    handler: Callable[[], dict | list],
) -> Response:
    started = time.perf_counter()
    try:
        payload = handler()
        partial_success = False
        if isinstance(payload, dict):
            partial_success = bool(payload.get("partial_success"))

        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            (
                "%s ok competence=%s department_id=%s branch=%s months=%s "
                "partial_success=%s duration_ms=%.0f"
            ),
            route,
            competence,
            department_id,
            branch,
            months,
            partial_success,
            duration_ms,
        )
        return json_read_response(
            payload=payload,
            competence=competence,
            department_id=department_id,
            branch=branch,
            months=months,
        )
    except Exception:
        logger.exception(
            (
                "%s failed competence=%s department_id=%s branch=%s months=%s "
                "duration_ms=%.0f"
            ),
            route,
            competence,
            department_id,
            branch,
            months,
            (time.perf_counter() - started) * 1000,
        )
        raise


def json_read_response(
    *,
    payload: Any,
    competence: str | None,
    department_id: str | None,
    branch: str | None,
    months: int | None,
) -> JSONResponse:
    safe_payload = to_json_safe(payload)
    body = json.dumps(safe_payload, sort_keys=True)
    etag_source = "|".join(
        [
            competence or "",
            department_id or "",
            branch or "",
            str(months or ""),
            body,
        ]
    )
    etag = hashlib.md5(etag_source.encode("utf-8")).hexdigest()

    return JSONResponse(
        content=safe_payload,
        headers={
            "Cache-Control": f"private, max-age={READ_CACHE_MAX_AGE_SECONDS}",
            "ETag": f'"{etag}"',
        },
    )
