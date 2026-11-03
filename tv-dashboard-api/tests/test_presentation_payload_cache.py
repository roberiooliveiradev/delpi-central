"""Regressão: payload de apresentação compartilhado entre kiosks.

Incidente 03/11/2026 — cada kiosk fazia polling do payload completo a cada
heartbeat e cada poll remontava todas as telas nativas (→ N blocos → api-delpi).
Com vários kiosks no mesmo token a carga multiplicava: rajada de ~800 req/5min.
O cache + single-flight de payload reaproveitam as primitivas já usadas nas
camadas de dados; TTL = heartbeat do player.
"""
from __future__ import annotations

import threading

import pytest

from tv_app.application.services import presentation_payload_service as mod
from tv_app.application.services.presentation_payload_service import (
    PresentationPayloadService,
)


@pytest.fixture(autouse=True)
def _reset_payload_cache():
    mod.reset_presentation_payload_cache()
    yield
    mod.reset_presentation_payload_cache()


class _FakeRepo:
    def __init__(self, playlist):
        self._playlist = playlist
        self.viewed = []

    def get_by_token(self, token):
        return self._playlist if token == "tok-1" else None

    def get_by_id(self, playlist_id):
        return self._playlist

    def touch_view(self, token):
        self.viewed.append(token)


class _StubPayloadService(PresentationPayloadService):
    def __init__(self, playlist, *, delay: float = 0.0, fail_first: int = 0):
        self._repo = _FakeRepo(playlist)
        self.calls = 0
        self._delay = delay
        self._fail_first = fail_first

    def _assemble_payload(self, playlist, **_kwargs):
        self.calls += 1
        if self.calls <= self._fail_first:
            raise RuntimeError("assemble falhou")
        if self._delay:
            import time

            time.sleep(self._delay)
        return {"playlist": {"id": str(playlist.get("id")), "name": "P"}}


def _service(playlist=None, **kw):
    return _StubPayloadService(
        playlist or {"id": "p1", "isActive": True, "publicToken": "tok-1"}, **kw
    )


def test_repeated_polls_share_one_assembly():
    svc = _service()
    a = svc.build_by_token("tok-1")
    b = svc.build_by_token("tok-1")
    c = svc.build_by_token("tok-1")
    assert svc.calls == 1
    assert a == b == c


def test_concurrent_polls_coalesce_to_one_assembly():
    svc = _service(delay=0.1)
    results, errors = [], []

    def poll():
        try:
            results.append(svc.build_by_token("tok-1"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=poll, daemon=True) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert not errors
    assert svc.calls == 1
    assert len(results) == 8


def test_different_authorization_scopes_do_not_share():
    svc = _service()
    svc.build_by_token("tok-1", authorization="Bearer aaa")
    svc.build_by_token("tok-1", authorization="Bearer bbb")
    svc.build_by_token("tok-1", authorization=None)
    assert svc.calls == 3


def test_different_filter_overrides_do_not_share():
    svc = _service()
    svc.build_by_token("tok-1", filter_overrides={"branch": "01"})
    svc.build_by_token("tok-1", filter_overrides={"branch": "02"})
    svc.build_by_token("tok-1", filter_overrides={"branch": "01"})
    assert svc.calls == 2


def test_assembly_failure_is_not_cached():
    svc = _service(fail_first=1)
    with pytest.raises(RuntimeError):
        svc.build_by_token("tok-1")
    assert svc.build_by_token("tok-1") is not None
    assert svc.calls == 2


def test_inactive_playlist_returns_none_without_cache():
    svc = _service({"id": "p1", "isActive": False, "publicToken": "tok-1"})
    assert svc.build_by_token("tok-1") is None
    assert svc.calls == 0


def test_track_view_side_effect_preserved_on_cache_hit():
    svc = _service()
    svc.build_by_token("tok-1", track_view=True)
    svc.build_by_token("tok-1", track_view=True)
    assert svc._repo.viewed == ["tok-1", "tok-1"]


def test_reset_invalidates_cached_payload():
    svc = _service()
    svc.build_by_token("tok-1")
    mod.reset_presentation_payload_cache()
    svc.build_by_token("tok-1")
    assert svc.calls == 2


def test_build_by_id_preview_also_cached_and_scoped():
    svc = _service()
    from uuid import uuid4

    pid = uuid4()
    svc.build_by_id(pid, authorization="Bearer aaa")
    svc.build_by_id(pid, authorization="Bearer aaa")
    svc.build_by_id(pid, authorization="Bearer bbb")
    # preview scope separado de public (mesmo token não colide)
    svc.build_by_token("tok-1", authorization="Bearer aaa")
    assert svc.calls == 3
