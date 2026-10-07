"""Regression: concurrent governed writes of the same user (VISTA/TV 503
"Serviço de autorização indisponível." on font-size decrease, 2026-10-07).

Production model reproduced here: ONE app event loop, sync write handlers in
AnyIO worker threads, the real shared ``load_user_rbac`` (Core ``/me`` faked
at the HTTP transport) and the real PresentationMutation / PATCH write path
over an in-memory repository. The incident: overlapping writes (editor
``bump_font_size`` POST + autosave PATCH) made the per-token RBAC
``asyncio.Lock`` bind to a private ``asyncio.run`` loop — the waiter hung and
later writes failed with ``RuntimeError: ... bound to a different event loop``
→ 503 AUTHZ_UNAVAILABLE.
"""

from __future__ import annotations

import asyncio
import copy
import time
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import anyio
import httpx
import pytest

import tv_app.core.security as sec
from tv_app.core.security import (
    arequire_fresh_write_authorization as _real_async_gate,
)
from tv_app.core.security import (
    require_fresh_write_authorization as _real_sync_gate,
)

USER_ID = "user-1"
BEARER = {"Authorization": "Bearer tok-concurrency-user"}
BLOCK_ID = "3e58593e-blk-text"
CORE_LATENCY = 0.15
REQUEST_DEADLINE = 10.0


class _Core:
    """Core ``/me`` faked at the httpx transport of ``load_user_rbac``."""

    def __init__(self) -> None:
        self.mode = "ok"
        self.latency = CORE_LATENCY
        self.calls = 0

    async def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        assert request.url.path.endswith("/me")
        await asyncio.sleep(self.latency)
        if self.mode == "timeout":
            raise httpx.ReadTimeout("core /me timed out", request=request)
        if self.mode == "down":
            return httpx.Response(503, json={"detail": "unavailable"})
        permissions = [] if self.mode == "deny" else ["tv-dashboard.write"]
        return httpx.Response(
            200,
            json={
                "id": USER_ID,
                "email": "u@delpi.local",
                "name": "User",
                "roles": [],
                "groups": [],
                "permissions": permissions,
                "is_superadmin": False,
            },
        )


class _Repo:
    """In-memory PlaylistRepository subset used by access, patch and writes."""

    def __init__(self) -> None:
        self.own_playlist = uuid4()
        self.foreign_playlist = uuid4()
        self.slide_id = uuid4()
        self.revision = 1
        self.update_calls: list[dict[str, Any]] = []
        self.slide = {
            "id": str(self.slide_id),
            "playlistId": str(self.own_playlist),
            "title": "Comunicado",
            "durationSec": 30,
            "isActive": True,
            "sectionId": None,
            "nativeScreenKey": "custom_message",
            "nativeConfig": {
                "version": 5,
                "blocks": [
                    {
                        "id": BLOCK_ID,
                        "type": "text",
                        "content": "Aviso",
                        "style": {"fontSize": 28},
                    }
                ],
            },
        }

    def get_by_id(self, playlist_id):
        owner = USER_ID if UUID(str(playlist_id)) == self.own_playlist else "someone-else"
        return {
            "id": str(playlist_id),
            "name": "Programação",
            "ownerUserId": owner,
            "createdBy": owner,
            "revision": self.revision,
        }

    def get_share_role(self, playlist_id, actor):
        return None

    def get_revision(self, playlist_id):
        return self.revision

    def get_slide(self, slide_id, *, playlist_id=None):
        return copy.deepcopy(self.slide)

    def list_slides(self, playlist_id):
        return [copy.deepcopy(self.slide)]

    def update_slide(self, playlist_id, slide_id, body, *, actor_user_id, reason):
        self.update_calls.append({"reason": reason, "body": copy.deepcopy(body)})
        self.slide.update(copy.deepcopy(body))
        self.revision += 1
        return copy.deepcopy(self.slide)

    def font_size(self) -> int:
        return self.slide["nativeConfig"]["blocks"][0]["style"]["fontSize"]


@pytest.fixture()
def world(monkeypatch):
    from delpi_auth.middleware import fastapi_auth as fa

    from tv_app.application.services.data.presentation_mutation import (
        patch_service,
    )
    from tv_app.application.services import tv_presentation_write_service as tws
    from tv_app.application.services.playlist_access_service import (
        PlaylistAccessService,
    )
    from tv_app.interface.http import playlist_access_http
    from tv_app.interface.http.routes import slide_routes

    core = _Core()
    repo = _Repo()

    class _CoreClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(core.handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(
        fa,
        "httpx",
        SimpleNamespace(
            AsyncClient=_CoreClient,
            Timeout=httpx.Timeout,
            TimeoutException=httpx.TimeoutException,
            RequestError=httpx.RequestError,
        ),
    )
    monkeypatch.setattr(fa, "_RBAC_CACHE", {})
    monkeypatch.setattr(fa, "_RBAC_LOCKS", {})
    monkeypatch.setattr(
        fa, "validate_token", lambda token: {"sub": USER_ID, "email": "u@delpi.local"}
    )
    monkeypatch.setattr(sec, "require_fresh_write_authorization", _real_sync_gate)
    monkeypatch.setattr(sec, "arequire_fresh_write_authorization", _real_async_gate)

    monkeypatch.setattr(playlist_access_http, "_access", PlaylistAccessService(repo=repo))
    monkeypatch.setattr(slide_routes, "_writes", tws.TvPresentationWriteService(repo=repo))
    monkeypatch.setattr(patch_service, "PlaylistRepository", lambda: repo)
    monkeypatch.setattr(slide_routes, "notify_presentation_changed", lambda **_: None)
    monkeypatch.setattr(tws, "notify_presentation_changed", lambda **_: None)

    from tv_app.main import app

    return SimpleNamespace(app=app, core=core, repo=repo)


def _bump(world, delta: int = -1, *, playlist_id=None) -> dict[str, Any]:
    pid = playlist_id or world.repo.own_playlist
    return {
        "method": "POST",
        "url": f"/playlists/{pid}/slides/{world.repo.slide_id}/presentation-mutations",
        "json": {"ops": [{"op": "bump_font_size", "blockId": BLOCK_ID, "deltaSteps": delta}]},
    }


def _autosave(world) -> dict[str, Any]:
    return {
        "method": "PATCH",
        "url": f"/playlists/{world.repo.own_playlist}/slides/{world.repo.slide_id}",
        "json": {"title": "Comunicado", "durationSec": 30},
    }


def _send(world, *batches: list[dict[str, Any]]) -> list[list[httpx.Response]]:
    """Run request batches sequentially; requests inside a batch overlap.

    Every request shares the single app event loop of this ``anyio.run``.
    """

    async def _main():
        transport = httpx.ASGITransport(app=world.app)
        out: list[list[httpx.Response]] = []
        async with httpx.AsyncClient(
            transport=transport, base_url="http://tv", timeout=REQUEST_DEADLINE
        ) as client:
            for batch in batches:
                responses: list[httpx.Response | None] = [None] * len(batch)

                async def _one(i: int, spec: dict[str, Any]) -> None:
                    await anyio.sleep(0.01 * i)
                    responses[i] = await client.request(headers=BEARER, **spec)

                with anyio.fail_after(REQUEST_DEADLINE):
                    async with anyio.create_task_group() as tg:
                        for i, spec in enumerate(batch):
                            tg.start_soon(_one, i, spec)
                out.append(responses)  # type: ignore[arg-type]
        return out

    return anyio.run(_main)


def _codes(responses: list[httpx.Response]) -> list[int]:
    return [r.status_code for r in responses]


# ------------------------------------------------------------------
# Incident: overlapping writes of the same user
# ------------------------------------------------------------------


def test_overlapping_bump_and_autosave_never_503_nor_hang(world):
    """Original workflow: decrease-font POST overlaps the autosave PATCH."""
    batches = _send(
        world,
        [_bump(world), _autosave(world)],
        [_bump(world), _autosave(world), _bump(world)],
        [_bump(world)],
    )
    for responses in batches:
        assert _codes(responses) == [200] * len(responses), [r.json() for r in responses]
    assert world.repo.font_size() == 28 - 2 * 4


def test_each_overlapping_write_runs_its_own_fresh_core_lookup(world):
    """Freshness is per write: concurrent writes are not coalesced into one
    authorization decision (middleware lookups are cached, gate lookups not)."""
    (responses,) = _send(world, [_bump(world), _autosave(world), _bump(world)])
    assert _codes(responses) == [200, 200, 200]
    middleware_lookups = 1
    assert world.core.calls == middleware_lookups + 3


# ------------------------------------------------------------------
# Positive / read-back / sibling
# ------------------------------------------------------------------


def test_authorized_bump_persists_and_reads_back(world):
    ((resp,),) = _send(world, [_bump(world)])
    assert resp.status_code == 200, resp.json()
    data = resp.json()["data"]
    ack_block = data["nativeConfig"]["blocks"][0]
    assert ack_block["style"]["fontSize"] == 26
    assert world.repo.font_size() == 26
    assert [c["reason"] for c in world.repo.update_calls] == ["slide_updated"]


def test_sibling_autosave_patch_uses_same_healthy_gate(world):
    ((resp,),) = _send(world, [_autosave(world)])
    assert resp.status_code == 200, resp.json()
    assert world.core.calls == 2  # middleware + fresh gate lookup


# ------------------------------------------------------------------
# Negative: denial and dependency failure stay distinct and fail closed
# ------------------------------------------------------------------


def test_permission_revoked_in_core_denies_without_write(world):
    world.core.mode = "deny"
    (responses,) = _send(world, [_bump(world), _autosave(world)])
    assert _codes(responses) == [403, 403]
    assert world.repo.update_calls == []
    assert world.repo.font_size() == 28


def test_foreign_playlist_is_denied_without_write(world):
    ((resp,),) = _send(world, [_bump(world, playlist_id=world.repo.foreign_playlist)])
    assert resp.status_code == 404
    assert world.repo.update_calls == []


def test_core_unavailable_fails_closed_503_without_write(world):
    world.core.mode = "down"
    (responses,) = _send(world, [_bump(world), _autosave(world)])
    assert _codes(responses) == [503, 503]
    assert all(r.json()["message"] == "Serviço de autorização indisponível." for r in responses)
    assert world.repo.update_calls == []


def test_core_timeout_is_bounded_and_fails_closed(world):
    world.core.mode = "timeout"
    started = time.monotonic()
    ((resp,),) = _send(world, [_bump(world)])
    assert resp.status_code == 503
    assert time.monotonic() - started < REQUEST_DEADLINE
    assert world.repo.update_calls == []


def test_recovers_after_transient_core_failure(world):
    world.core.mode = "down"
    ((failed,),) = _send(world, [_bump(world)])
    assert failed.status_code == 503
    world.core.mode = "ok"
    (responses,) = _send(world, [_bump(world), _autosave(world)])
    assert _codes(responses) == [200, 200]
    assert world.repo.font_size() == 26
