from __future__ import annotations

import atexit
import signal
import sys

from app.create_app import create_app
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging import configure_logging

settings = Settings()
logger = configure_logging(settings.service_name, settings.log_level)
app = create_app()

_shutdown_logged = False


def _log_shutdown() -> None:
    """Emit once when the standalone process is terminating normally."""
    global _shutdown_logged
    if _shutdown_logged:
        return
    _shutdown_logged = True
    logger.info(
        "delia_api_stopped service=%s version=%s env=%s",
        settings.service_name,
        settings.service_version,
        settings.environment,
    )
    for handler in logger.handlers:
        handler.flush()
    sys.stdout.flush()


def _handle_termination_signal(signum: int, _frame) -> None:
    _log_shutdown()
    # Prefer clean exit so callers observe PROCESS_TERMINATED with exit 0.
    raise SystemExit(0)


def _install_shutdown_visibility() -> None:
    signal.signal(signal.SIGTERM, _handle_termination_signal)
    signal.signal(signal.SIGINT, _handle_termination_signal)
    atexit.register(_log_shutdown)


def run() -> None:
    """Process entry used by ``python -m app.main`` and runtime smoke."""
    _install_shutdown_visibility()
    try:
        app.run(
            host=settings.host,
            port=settings.port,
            debug=settings.debug,
            threaded=True,
            use_reloader=False,
        )
    except KeyboardInterrupt:
        _log_shutdown()
        raise SystemExit(0) from None
    finally:
        _log_shutdown()


if __name__ == "__main__":
    run()
