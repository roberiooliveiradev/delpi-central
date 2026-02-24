from app.extensions.socket import socketio


def emit_admin_event(entity: str, action: str, payload: dict | None = None):
    """
    Evento padrão para atualizações administrativas em tempo real.

    entity: apps | routes | rbac | plugins
    action: create | update | delete | bulk_update | bulk_delete | register
    """
    print("🔥 EMIT ADMIN EVENT:", entity, action)
    socketio.emit(
        "admin.changed",
        {
            "entity": entity,
            "action": action,
            "payload": payload or {},
        },
        namespace="/",
    )