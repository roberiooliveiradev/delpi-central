from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from typing import Callable, TypeVar

T = TypeVar("T")


def submit_in_request_context(executor: ThreadPoolExecutor, fn: Callable[[], T]):
    """Executa fn em thread worker preservando contextvars (JWT do usuário)."""
    ctx = copy_context()
    return executor.submit(ctx.run, fn)
