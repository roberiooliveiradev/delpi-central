from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from typing import Callable, TypeVar

T = TypeVar("T")


def run_named_callables(
    loaders: dict[str, Callable[[], T]],
    *,
    max_workers: int,
) -> dict[str, T]:
    """Executa loaders independentes em paralelo, preservando o contexto da request.

    `copy_context` é obrigatório: o JWT do gateway vive em ContextVar e
    ThreadPoolExecutor não propaga o contexto sozinho.
    """
    if not loaders:
        return {}
    workers = max(1, int(max_workers))
    if len(loaders) == 1 or workers == 1:
        return {key: loader() for key, loader in loaders.items()}

    results: dict[str, T] = {}
    with ThreadPoolExecutor(max_workers=min(workers, len(loaders))) as executor:
        futures = {
            executor.submit(copy_context().run, loader): key
            for key, loader in loaders.items()
        }
        for future, key in futures.items():
            results[key] = future.result()
    return results
