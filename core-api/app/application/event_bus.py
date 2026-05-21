# app/application/event_bus.py

from app.application.event_handlers.admin_audit_event_handler import (
    AdminAuditEventHandler,
)
from app.application.event_handlers.rbac_event_handler import RbacEventHandler
from app.infrastructure.socket.socket_event_dispatcher import SocketIOEventDispatcher


class EventBus:

    def __init__(self, uow):
        self.uow = uow
        self.socket_dispatcher = SocketIOEventDispatcher()
        self.rbac_handler = RbacEventHandler(uow)
        self.audit_handler = AdminAuditEventHandler(uow)

    def publish(self, events):

        for event in events:

            # 1️⃣ Domain side effects (IAM, cache)
            self.rbac_handler.handle(event)

            # 2️⃣ Auditoria persistente (plugins/apps)
            self.audit_handler.handle(event)

            # 3️⃣ Infra side effects (socket)
            self.socket_dispatcher.dispatch(event)

        try:
            if self.uow.session.new or self.uow.session.dirty:
                self.uow.session.commit()
        except Exception as e:
            print("Erro ao persistir auditoria pós-commit:", e)
            self.uow.session.rollback()