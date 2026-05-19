# app/tests/test_notification_dispatch_scheduler.py

from app.create_app import create_app
from app.infrastructure.schedulers import notification_dispatch_scheduler as scheduler_module


def test_scheduler_not_started_for_testing_app():
    scheduler_module._scheduler_started = False

    create_app("testing")

    assert scheduler_module._scheduler_started is False
