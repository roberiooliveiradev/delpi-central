from __future__ import annotations

import threading
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class _Flight(Generic[T]):
    """Resultado compartilhado de uma execução downstream em andamento."""

    def __init__(self) -> None:
        self._done = threading.Event()
        self._result: T | None = None
        self._error: BaseException | None = None

    def complete_value(self, value: T) -> None:
        self._result = value
        self._done.set()

    def complete_error(self, error: BaseException) -> None:
        self._error = error
        self._done.set()

    def wait(self) -> T:
        self._done.wait()
        if self._error is not None:
            raise self._error
        return self._result


class SingleFlightRegistry(Generic[T]):
    """Coalescing in-process: N chamadas concorrentes com a mesma chave
    executam o fetch downstream exatamente uma vez.

    O escopo é por processo — o tv-dashboard-api roda um único worker uvicorn,
    com endpoints síncronos servidos pelo threadpool do anyio. Não é dedup
    distribuído entre réplicas.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._flights: dict[str, _Flight[T]] = {}

    def run(self, key: str, fetch: Callable[[], T]) -> T:
        with self._lock:
            flight = self._flights.get(key)
            if flight is None:
                flight = _Flight()
                self._flights[key] = flight
                leader = True
            else:
                leader = False

        if not leader:
            return flight.wait()

        try:
            flight.complete_value(fetch())
        except BaseException as exc:
            flight.complete_error(exc)
            raise
        finally:
            with self._lock:
                self._flights.pop(key, None)
        return flight._result

    def invalidate_all(self) -> None:
        """Descarta o índice de voos para novas chamadas.

        Waiters já registrados mantêm a referência ao próprio _Flight e
        completam normalmente; apenas novos joiners iniciam um fetch novo.
        """
        with self._lock:
            self._flights.clear()

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {"in_flight": len(self._flights)}
