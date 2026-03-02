# app/application/event_bus.py

from app.application.event_handlers.rbac_event_handler import RbacEventHandler
from app.infrastructure.socket.socket_event_dispatcher import SocketIOEventDispatcher


class EventBus:

    def __init__(self, uow):
        self.uow = uow
        self.socket_dispatcher = SocketIOEventDispatcher()
        self.rbac_handler = RbacEventHandler(uow)

    def publish(self, events):

        for event in events:

            # 1️⃣ Domain side effects (IAM, cache)
            self.rbac_handler.handle(event)

            # 2️⃣ Infra side effects (socket)
            self.socket_dispatcher.dispatch(event)