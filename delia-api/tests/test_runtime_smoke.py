"""C1-T1R1 — real-process HTTP /health smoke + shutdown visibility.

Flask test_client is not sufficient. This suite starts the standalone entrypoint
(`python -m app.main`), hits GET /health over real TCP/HTTP, then terminates.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = [sys.executable, "-m", "app.main"]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_health(port: int, *, timeout_s: float = 15.0) -> tuple[int, dict]:
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                body = json.loads(response.read().decode("utf-8"))
                return int(response.status), body
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as exc:
            last_error = exc
            time.sleep(0.1)
    raise AssertionError(f"health listener not reachable on {port}: {last_error}")


def test_real_process_health_http_and_shutdown_visibility():
    port = _free_port()
    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": str(API_ROOT),
            "DELIA_API_HOST": "127.0.0.1",
            "DELIA_API_PORT": str(port),
            "DELIA_DEBUG": "false",
            "LOG_LEVEL": "INFO",
            "SERVICE_NAME": "delia-api",
            "SERVICE_VERSION": "0.0.1",
            "DELIA_ENV": "testing",
        }
    )

    proc = subprocess.Popen(
        ENTRYPOINT,
        cwd=str(API_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        status, body = _wait_health(port)
        assert status == 200
        assert body == {
            "status": "available",
            "service": "delia-api",
            "version": "0.0.1",
        }

        proc.send_signal(signal.SIGTERM)
        try:
            stdout, _ = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, _ = proc.communicate(timeout=5)
            raise AssertionError("process did not terminate after SIGTERM") from None

        assert proc.returncode is not None
        # 0 = clean SystemExit; 143/-15 = SIGTERM after stop log (werkzeug edge)
        assert proc.returncode in {0, 143, -signal.SIGTERM}, (
            f"unexpected exit={proc.returncode} output={stdout!r}"
        )

        assert "delia_api_started" in stdout, stdout
        assert "delia_api_stopped" in stdout, stdout
        assert "service=delia-api" in stdout
        assert "Authorization" not in stdout
        assert "token" not in stdout.lower()
        # Body must be JSON liveness, not an unrelated front-end HTML proxy hit.
        assert body["status"] == "available"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)


def test_shutdown_visibility_helper_is_idempotent(monkeypatch):
    """Local unit guard: stop log emits once (no LifecycleManager)."""
    import app.main as main_mod

    records: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())

    handler = _Capture()
    main_mod.logger.addHandler(handler)
    try:
        monkeypatch.setattr(main_mod, "_shutdown_logged", False)
        main_mod._log_shutdown()
        main_mod._log_shutdown()
    finally:
        main_mod.logger.removeHandler(handler)

    assert sum(1 for message in records if "delia_api_stopped" in message) == 1
