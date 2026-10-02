"""SEC-TV-001 — credential query params must not reach access-log sinks.

Covers the uvicorn emitters (`uvicorn.access` HTTP lines and
`uvicorn.error` WebSocket handshake lines) through
`SensitiveQueryParamsLogFilter`, which rewrites `record.msg`/`record.args`
before any handler formats the record.
"""

from __future__ import annotations

import logging

import pytest

from tv_app.infrastructure.log_sanitization import (
    REDACTED_QUERY_VALUE,
    SensitiveQueryParamsLogFilter,
    install_sensitive_query_params_log_filter,
)

SENTINEL = "SECRET_SENTINEL_DO_NOT_LOG"


def _emit_record(
    msg: str,
    args: tuple | dict | None,
    caplog: pytest.LogCaptureFixture,
    logger_name: str = "uvicorn.access",
) -> str:
    logger = logging.getLogger(logger_name)
    logger.addFilter(SensitiveQueryParamsLogFilter())
    with caplog.at_level(logging.INFO, logger=logger_name):
        logger.info(msg, *args)
    rendered = "\n".join(caplog.messages)
    caplog.clear()
    return rendered


def test_uvicorn_style_access_line_redacts_access_token(
    caplog: pytest.LogCaptureFixture,
):
    rendered = _emit_record(
        '%s - "%s %s HTTP/%s" %d',
        (
            "172.19.0.1:51000",
            "GET",
            f"/playlists/library-ws?access_token={SENTINEL}",
            "1.1",
            101,
        ),
        caplog,
    )
    assert SENTINEL not in rendered
    assert f"access_token={REDACTED_QUERY_VALUE}" in rendered
    assert "library-ws" in rendered


def test_websocket_handshake_line_redacts_token(
    caplog: pytest.LogCaptureFixture,
):
    rendered = _emit_record(
        '%s - "WebSocket %s" [accepted]',
        (
            "172.19.0.1:51000",
            f"/playlists/presentation-ws?access_token={SENTINEL}",
        ),
        caplog,
        logger_name="uvicorn.error",
    )
    assert SENTINEL not in rendered
    assert f"access_token={REDACTED_QUERY_VALUE}" in rendered


def test_token_in_middle_and_end_positions(
    caplog: pytest.LogCaptureFixture,
):
    cases = (
        (
            f"/media/9/file?v=1&access_token={SENTINEL}&download=1",
            ("v=1", "download=1"),
        ),
        (f"/media/9/file?access_token={SENTINEL}", ("/media/9/file",)),
        (f"/media/9/file?access_token={SENTINEL}&x=1", ("x=1",)),
    )
    for target, preserved in cases:
        rendered = _emit_record("%s", (target,), caplog)
        assert SENTINEL not in rendered
        assert REDACTED_QUERY_VALUE in rendered
        for fragment in preserved:
            assert fragment in rendered


def test_url_encoded_token_redacted(caplog: pytest.LogCaptureFixture):
    rendered = _emit_record(
        "%s", ("/ws?access_token=ZXlK%2B%3D%3D.sentinel%2Fpart",), caplog
    )
    assert "ZXlK%2B%3D%3D" not in rendered
    assert REDACTED_QUERY_VALUE in rendered


def test_all_canonical_sensitive_params_redacted(
    caplog: pytest.LogCaptureFixture,
):
    for param in (
        "access_token",
        "token",
        "refresh_token",
        "id_token",
        "authorization",
        "api_key",
        "client_secret",
        "password",
    ):
        rendered = _emit_record("%s", (f"/x?{param}={SENTINEL}",), caplog)
        assert SENTINEL not in rendered, param


def test_non_sensitive_query_params_preserved(
    caplog: pytest.LogCaptureFixture,
):
    rendered = _emit_record(
        "%s",
        ("/public/present/abc?branch=01&department_id=engineering",),
        caplog,
    )
    assert "branch=01" in rendered
    assert "department_id=engineering" in rendered


def test_missing_and_empty_token_do_not_break(
    caplog: pytest.LogCaptureFixture,
):
    rendered = _emit_record("%s", ("/ws?access_token=",), caplog)
    assert "access_token=" in rendered
    rendered = _emit_record("%s", ("/playlists/library-ws",), caplog)
    assert "library-ws" in rendered


def test_dict_args_are_scrubbed():
    log_filter = SensitiveQueryParamsLogFilter()
    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        "%(target)s",
        None,
        None,
    )
    record.args = {"target": f"/ws?access_token={SENTINEL}"}
    assert log_filter.filter(record) is True
    rendered = record.getMessage()
    assert SENTINEL not in rendered
    assert REDACTED_QUERY_VALUE in rendered


def test_non_string_args_untouched(caplog: pytest.LogCaptureFixture):
    rendered = _emit_record("%s %d", ("plain", 42), caplog)
    assert "plain 42" in rendered


def test_filter_propagates_true_and_record_remains_valid():
    log_filter = SensitiveQueryParamsLogFilter()
    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        '%s - "GET %s" %d',
        ("client", f"/ws?access_token={SENTINEL}", 200),
        None,
    )
    assert log_filter.filter(record) is True
    rendered = record.getMessage()
    assert SENTINEL not in rendered


def test_install_attaches_to_uvicorn_access_and_error():
    access_logger = logging.getLogger("uvicorn.access")
    error_logger = logging.getLogger("uvicorn.error")
    try:
        install_sensitive_query_params_log_filter()
        assert any(
            isinstance(f, SensitiveQueryParamsLogFilter)
            for f in access_logger.filters
        )
        assert any(
            isinstance(f, SensitiveQueryParamsLogFilter)
            for f in error_logger.filters
        )
    finally:
        for logger in (access_logger, error_logger):
            logger.filters = [
                f
                for f in logger.filters
                if not isinstance(f, SensitiveQueryParamsLogFilter)
            ]
