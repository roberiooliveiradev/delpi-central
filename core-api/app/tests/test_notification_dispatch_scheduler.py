# app/tests/test_notification_dispatch_scheduler.py

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.infrastructure.schedulers import notification_dispatch_scheduler as scheduler_module


def test_scheduler_not_started_for_testing_app():
    scheduler_module._scheduler_started = False

    with patch(
        "app.infrastructure.schedulers.notification_dispatch_scheduler.socketio"
    ) as socketio_mock:
        create_app("testing")

    socketio_mock.start_background_task.assert_not_called()
    assert scheduler_module._scheduler_started is False


def test_scheduler_uses_socketio_background_task():
    scheduler_module._scheduler_started = False

    with patch(
        "app.infrastructure.schedulers.notification_dispatch_scheduler.socketio"
    ) as socketio_mock:
        create_app()

    socketio_mock.start_background_task.assert_called_once()
    assert scheduler_module._scheduler_started is True
