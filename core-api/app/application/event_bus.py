# app/application/event_bus.py

from app.application.event_handlers.admin_audit_event_handler import (
    AdminAuditEventHandler,
)
from app.application.event_handlers.rbac_event_handler import RbacEventHandler
from app.application.event_handlers.rbac_notification_event_handler import (
    RbacNotificationEventHandler,
)
from app.infrastructure.socket.socket_event_dispatcher import SocketIOEventDispatcher


class EventBus:

    def __init__(self, uow):
        self.uow = uow
        self.socket_dispatcher = SocketIOEventDispatcher()
        self.rbac_handler = RbacEventHandler(uow)
        self.rbac_notification_handler = RbacNotificationEventHandler(uow)
        self.audit_handler = AdminAuditEventHandler(uow)

    def publish(self, events):

        for event in events:

            # 1️⃣ Domain side effects (IAM, cache)
            self.rbac_handler.handle(event)

            # 2️⃣ Notificação de acesso a apps (após IAM sync)
            self.rbac_notification_handler.handle(event)

            # 3️⃣ Auditoria persistente (plugins/apps)
            self.audit_handler.handle(event)

            # 4️⃣ Infra side effects (socket)
            self.socket_dispatcher.dispatch(event)

        self._flush_pending_side_effects()

    def _flush_pending_side_effects(self) -> None:
        """
        Handlers podem criar registros e coletar eventos após o commit da request
        (ex.: notificação automática de acesso RBAC). Persiste e emite socket.
        """
        pending = list(getattr(self.uow, "_events", []))
        if not pending:
            return

        self.uow._events.clear()

        try:
            if self.uow.session.new or self.uow.session.dirty:
                self.uow.session.commit()
        except Exception as e:
            print("Erro ao persistir efeitos pós-evento:", e)
            self.uow.session.rollback()
            return

        for event in pending:
            self.socket_dispatcher.dispatch(event)