"""Regressão: fan-out de coletores do snapshot limitado por setting.

Incidente 03/11/2026 — `_collect_parallel` abria `ThreadPoolExecutor` com
`max_workers=len(collectors)`, disparando uma rajada simultânea de queries
pesadas na api-delpi e contribuindo para o esgotamento do pool TOTVS.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from si_app.config import settings
from si_app.infrastructure.providers.strategic_indicators import (
    real_indicator_measurements_provider as mod,
)


def _new_provider():
    return object.__new__(mod.RealStrategicIndicatorsMeasurementsProvider)


def _collectors(n: int):
    return [
        (f"dept-{i}", (lambda: {"items": [], "errors": []})) for i in range(n)
    ]


def test_collect_parallel_caps_workers_by_setting(monkeypatch):
    monkeypatch.setattr(settings, "SI_SNAPSHOT_MAX_PARALLEL_COLLECTORS", 3)
    captured: dict = {}
    real_executor = ThreadPoolExecutor

    class RecordingExecutor(real_executor):
        def __init__(self, *args, **kwargs):
            captured["max_workers"] = kwargs.get(
                "max_workers", args[0] if args else None
            )
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(mod, "ThreadPoolExecutor", RecordingExecutor)

    results = _new_provider()._collect_parallel(_collectors(8))

    assert captured["max_workers"] == 3
    assert len(results) == 8


def test_collect_parallel_uses_collector_count_when_smaller(monkeypatch):
    monkeypatch.setattr(settings, "SI_SNAPSHOT_MAX_PARALLEL_COLLECTORS", 3)
    captured: dict = {}
    real_executor = ThreadPoolExecutor

    class RecordingExecutor(real_executor):
        def __init__(self, *args, **kwargs):
            captured["max_workers"] = kwargs.get(
                "max_workers", args[0] if args else None
            )
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(mod, "ThreadPoolExecutor", RecordingExecutor)

    _new_provider()._collect_parallel(_collectors(2))

    assert captured["max_workers"] == 2


def test_collect_parallel_preserves_result_order_and_errors():
    provider = _new_provider()
    collectors = [
        ("ok", lambda: {"items": [{"x": 1}], "errors": []}),
        ("fails", lambda: (_ for _ in ()).throw(RuntimeError("boom"))),
    ]
    results = provider._collect_parallel(collectors)
    assert results[0]["items"] == [{"x": 1}]
    assert results[1]["errors"][0]["message"] == "boom"
    assert results[1]["errors"][0]["source"] == "fails_snapshot"
