import logging
import queue
import threading
from typing import Any, Callable, Generator, Iterable

from flask import Flask

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
    continua até o fim e persiste a resposta (commit no evento ``done``).
    """
    event_queue: queue.Queue[Any] = queue.Queue()
    state = {"committed": False}

    def producer() -> None:
        with app.app_context():
            try:
                for event in stream_factory():
                    event_queue.put(event)
                    if event.get("type") == "done":
                        db.session.commit()
                        state["committed"] = True
                event_queue.put(_SENTINEL)
            except Exception:
                logger.exception(
                    "chat_stream_producer_failed",
                    extra={"session_id": session_id},
                )
                try:
                    db.session.rollback()
                except Exception:
                    pass
                event_queue.put(_SENTINEL)

    threading.Thread(target=producer, daemon=True).start()

    while True:
        item = event_queue.get()
        if item is _SENTINEL:
            break
        yield item
