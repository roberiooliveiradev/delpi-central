import logging
import queue
import threading
from typing import Any, Callable, Generator, Iterable

from flask import Flask

from app.application.services.chat_stream_checkpoint_service import (
    ChatStreamCheckpointService,
)
from app.extensions.db import db

logger = logging.getLogger(__name__)

_SENTINEL = object()


def stream_chat_events_with_background_completion(
    app: Flask,
    stream_factory: Callable[[], Iterable[dict[str, Any]]],
    *,
    session_id: str | None = None,
) -> Generator[dict[str, Any], None, None]:
    """
    Executa o stream do chat em uma thread separada e repassa eventos via fila.

    Se o cliente SSE desconectar, o consumidor interrompe o yield, mas o produtor
    continua até o fim e persiste a resposta (commits incrementais em checkpoints).
    """
    event_queue: queue.Queue[Any] = queue.Queue()
    state = {"committed": False}

    def producer() -> None:
        with app.app_context():
            try:
                for event in stream_factory():
                    event_queue.put(event)
                    if ChatStreamCheckpointService.should_commit(event):
                        db.session.commit()
                        state["committed"] = True
                        logger.debug(
                            "chat_stream_checkpoint_committed",
                            extra={
                                "session_id": session_id,
                                "event_type": event.get("type"),
                            },
                        )
                event_queue.put(_SENTINEL)
            except Exception as exc:
                logger.exception(
                    "chat_stream_producer_failed",
                    extra={"session_id": session_id},
                )
                try:
                    db.session.rollback()
                except Exception:
                    pass
                try:
                    from app.application.services.chat_stream_failure_recovery_service import (
                        ChatStreamFailureRecoveryService,
                    )
                    from app.composition.repository_composer import (
                        make_chat_session_repository,
                    )

                    ChatStreamFailureRecoveryService.recover(
                        chat_repository=make_chat_session_repository(),
                        session_id=session_id,
                        detail=str(exc),
                    )
                    db.session.commit()
                except Exception:
                    logger.exception(
                        "chat_stream_failure_recovery_failed",
                        extra={"session_id": session_id},
                    )
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                event_queue.put(
                    {
                        "type": "error",
                        "message": "Erro ao gerar resposta em streaming.",
                        "detail": str(exc)[:300],
                        "errorType": exc.__class__.__name__,
                    }
                )
                event_queue.put(_SENTINEL)

    threading.Thread(target=producer, daemon=True).start()

    while True:
        item = event_queue.get()
        if item is _SENTINEL:
            break
        yield item
