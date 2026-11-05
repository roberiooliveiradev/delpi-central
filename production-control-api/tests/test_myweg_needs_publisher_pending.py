"""Automação --publish-pending — descoberta cronológica, watermark e locks."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from production_control_app.jobs.myweg_needs_publisher.cli import main as publisher_main
from production_control_app.jobs.myweg_needs_publisher.http_client import (
    MyWegNeedsPublisherClient,
)
from production_control_app.jobs.myweg_needs_publisher.pending import run_pending_publish
from production_control_app.jobs.myweg_needs_publisher.state_store import PublisherStateStore
from production_control_app.jobs.myweg_needs_publisher.config import PublisherConfig

_FIXTURES = Path(__file__).parent / "fixtures" / "myweg" / "collections"
_COMPLETE_ID = "20261104_172829_20261104_142827_EXPORT_20261104_142826"
_COMPLETE = _FIXTURES / _COMPLETE_ID
_SP = ZoneInfo("America/Sao_Paulo")


def _copy_collection(dst_root: Path, *, collection_id: str) -> Path:
    target = dst_root / collection_id
    shutil.copytree(_COMPLETE, target)
    resumo = json.loads((target / "resumo.json").read_text(encoding="utf-8"))
    resumo["collection_id"] = collection_id
    (target / "resumo.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return target


def _config(
    tmp_path: Path,
    root: Path,
    *,
    activation: datetime | None,
    auto_sb1_resolve: bool = False,
) -> PublisherConfig:
    return PublisherConfig(
        normalized_root=root,
        state_dir=tmp_path / "state",
        api_base_url="http://pc-api",
        service_token="tok",
        caller_app="myweg-needs-publisher",
        timeout_seconds=5,
        max_attempts=1,
        stability_wait_seconds=0,
        max_batches_per_run=5,
        activation_collected_at=activation,
        auto_sb1_resolve=auto_sb1_resolve,
        max_sb1_batches_per_run=5,
        branch="02",
    )


def test_pending_requires_activation_watermark(tmp_path, monkeypatch, capsys):
    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "tok")
    monkeypatch.setenv("MYWEG_PUBLISHER_STABILITY_WAIT_SECONDS", "0")
    code = publisher_main(
        [
            "--dry-run",
            "--publish-pending",
            "--normalized-root",
            str(root),
            "--state-dir",
            str(tmp_path / "state"),
            "--json",
        ]
    )
    assert code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "activation_watermark_required"


def test_pending_processes_oldest_first_with_max_batches(tmp_path):
    root = tmp_path / "norm"
    older_id = "20261103_100000_20261103_090000_EXPORT_20261103_090000"
    newer_id = "20261104_172829_20261104_142827_EXPORT_20261104_142826"
    _copy_collection(root, collection_id=older_id)
    _copy_collection(root, collection_id=newer_id)

    published_order: list[str] = []

    class CaptureTransport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            body = json.loads(request.content.decode("utf-8"))
            published_order.append(body["collection_id"])
            return httpx.Response(
                201,
                json={
                    "success": True,
                    "data": {"created": True, "id": body["collection_id"], "recordCount": 3},
                },
            )

    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=CaptureTransport(),
        max_attempts=1,
    )
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation)
    first = run_pending_publish(
        config=config,
        dry_run=False,
        max_batches=1,
        include_historical=False,
        client=client,
    )
    assert first["published"] == 1
    assert published_order == [older_id]
    assert any(i.get("status") == "deferred_max_batches" for i in first["items"])

    second = run_pending_publish(
        config=config,
        dry_run=False,
        max_batches=5,
        include_historical=False,
        client=client,
    )
    assert second["published"] == 1
    assert published_order == [older_id, newer_id]


def test_pending_skips_already_published_same_hash(tmp_path):
    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation)
    state = PublisherStateStore(config.state_dir)

    class CountingTransport(httpx.BaseTransport):
        def __init__(self):
            self.calls = 0

        def handle_request(self, request):  # noqa: ANN001
            self.calls += 1
            body = json.loads(request.content.decode("utf-8"))
            return httpx.Response(
                201,
                json={"success": True, "data": {"created": True, "id": "x", "recordCount": 3}},
            )

    transport = CountingTransport()
    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=transport,
        max_attempts=1,
    )
    first = run_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert first["published"] == 1
    assert transport.calls == 1

    second = run_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert second["published"] == 0
    assert any(i.get("status") == "already_published" for i in second["items"])
    assert transport.calls == 1
    assert state.get_success_for_collection(_COMPLETE_ID) is not None


def test_pending_hash_conflict_does_not_overwrite(tmp_path):
    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation)
    state = PublisherStateStore(config.state_dir)
    state.record_attempt(
        collection_id=_COMPLETE_ID,
        payload_sha256="a" * 64,
        status="published",
        http_status=201,
        result="created=true",
    )

    class BoomTransport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            raise AssertionError("conflito local não deve chamar HTTP")

    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=BoomTransport(),
        max_attempts=1,
    )
    result = run_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 0
    assert any(i.get("status") == "conflict" for i in result["items"])


def test_pending_incomplete_folder_recorded_not_silent(tmp_path):
    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    shutil.copytree(_FIXTURES / "sample_incomplete", root / "sample_incomplete")
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation)
    result = run_pending_publish(
        config=config, dry_run=True, max_batches=5, include_historical=False, client=None
    )
    blocked = [i for i in result["items"] if i.get("collection_id") == "sample_incomplete"]
    assert blocked
    assert blocked[0]["status"] == "blocked"


def test_set_activation_watermark_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "tok")
    code = publisher_main(
        [
            "--set-activation-watermark",
            "2026-11-04T14:28:27-03:00",
            "--state-dir",
            str(tmp_path / "state"),
            "--normalized-root",
            str(tmp_path / "empty"),
            "--json",
        ]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    store = PublisherStateStore(tmp_path / "state")
    assert store.get_activation_watermark() is not None


def test_run_lock_busy(tmp_path):
    import multiprocessing as mp

    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation)

    def _hold(state_dir: str, ready: mp.Event, done: mp.Event) -> None:  # type: ignore[name-defined]
        store = PublisherStateStore(Path(state_dir))
        with store.acquire_run_lock() as held:
            assert held is True
            ready.set()
            done.wait(10)

    ready: mp.Event = mp.Event()
    done: mp.Event = mp.Event()
    proc = mp.Process(target=_hold, args=(str(config.state_dir), ready, done))
    proc.start()
    assert ready.wait(5)
    nested = run_pending_publish(
        config=config, dry_run=True, max_batches=5, include_historical=False
    )
    assert nested["status"] == "busy"
    done.set()
    proc.join(5)
    assert proc.exitcode == 0


def test_publish_then_auto_sb1_resolve(tmp_path):
    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation, auto_sb1_resolve=True)
    paths: list[str] = []

    class DualTransport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            paths.append(request.url.path)
            if request.url.path.endswith("/need-batches"):
                return httpx.Response(
                    201,
                    json={
                        "success": True,
                        "data": {"created": True, "id": "b1", "recordCount": 3},
                    },
                )
            assert request.url.path.endswith("/sb1-resolve")
            body = json.loads(request.content.decode("utf-8"))
            assert body["dry_run"] is False
            assert body["skip_if_complete"] is True
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "persisted": True,
                        "skipped": False,
                        "status": "resolved",
                        "counts": {"confirmed": 3, "ambiguous": 0},
                        "semantics": {"proven": True},
                        "resolutionRunId": "run-1",
                    },
                },
            )

    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=DualTransport(),
        max_attempts=1,
    )
    result = run_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 1
    assert result["sb1_resolved"] == 1
    assert result["sb1_failed"] == 0
    assert paths[-2].endswith("/need-batches")
    assert paths[-1].endswith("/sb1-resolve")
    item = next(i for i in result["items"] if i.get("status") == "published")
    assert item["sb1"]["status"] == "resolved"
    state = PublisherStateStore(config.state_dir)
    success = state.get_success_for_collection(_COMPLETE_ID)
    assert success is not None
    assert success["status"] == "published"
    assert success["sb1_status"] == "sb1_resolved"


def test_already_published_recovers_pending_sb1(tmp_path):
    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation, auto_sb1_resolve=True)
    state = PublisherStateStore(config.state_dir)
    # Simula ingestão OK sem SB1 (bug pré-automação).
    from production_control_app.jobs.myweg_needs_publisher.collection_reader import (
        load_collection,
    )
    from production_control_app.jobs.myweg_needs_publisher.payload_builder import (
        build_ingest_payload,
    )

    built = build_ingest_payload(
        load_collection(root / _COMPLETE_ID, stability_wait_seconds=0)
    )
    state.record_attempt(
        collection_id=_COMPLETE_ID,
        payload_sha256=str(built["batch"]["payload_sha256"]),
        status="published",
        http_status=201,
        result="created=true",
    )

    class ResolveOnlyTransport(httpx.BaseTransport):
        def __init__(self):
            self.calls = 0

        def handle_request(self, request):  # noqa: ANN001
            self.calls += 1
            assert request.url.path.endswith("/sb1-resolve")
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "persisted": True,
                        "skipped": False,
                        "counts": {"confirmed": 495, "ambiguous": 1},
                        "semantics": {"proven": True},
                        "resolutionRunId": "run-recover",
                    },
                },
            )

    transport = ResolveOnlyTransport()
    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=transport,
        max_attempts=1,
    )
    result = run_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 0
    assert result["sb1_resolved"] == 1
    assert transport.calls == 1


def test_already_resolved_skips_without_failure(tmp_path):
    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation, auto_sb1_resolve=True)
    state = PublisherStateStore(config.state_dir)
    from production_control_app.jobs.myweg_needs_publisher.collection_reader import (
        load_collection,
    )
    from production_control_app.jobs.myweg_needs_publisher.payload_builder import (
        build_ingest_payload,
    )

    built = build_ingest_payload(
        load_collection(root / _COMPLETE_ID, stability_wait_seconds=0)
    )
    state.record_attempt(
        collection_id=_COMPLETE_ID,
        payload_sha256=str(built["batch"]["payload_sha256"]),
        status="published",
        http_status=201,
        result="created=true",
    )

    class SkipTransport(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "persisted": False,
                        "skipped": True,
                        "status": "already_resolved",
                        "counts": {"confirmed": 496},
                        "semantics": {"proven": True},
                    },
                },
            )

    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=SkipTransport(),
        max_attempts=1,
    )
    result = run_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["sb1_skipped"] == 1
    assert result["sb1_failed"] == 0
    assert result["ok"] is True


def test_sb1_auth_failure_does_not_erase_ingest(tmp_path):
    root = tmp_path / "norm"
    _copy_collection(root, collection_id=_COMPLETE_ID)
    activation = datetime(2026, 11, 1, 0, 0, tzinfo=_SP)
    config = _config(tmp_path, root, activation=activation, auto_sb1_resolve=True)

    class AuthFailAfterPublish(httpx.BaseTransport):
        def handle_request(self, request):  # noqa: ANN001
            if request.url.path.endswith("/need-batches"):
                return httpx.Response(
                    201,
                    json={"success": True, "data": {"created": True, "id": "b1"}},
                )
            return httpx.Response(401, json={"success": False, "message": "token inválido"})

    client = MyWegNeedsPublisherClient(
        base_url="http://pc-api",
        service_token="tok",
        caller_app="pub",
        transport=AuthFailAfterPublish(),
        max_attempts=1,
    )
    result = run_pending_publish(
        config=config, dry_run=False, max_batches=5, include_historical=False, client=client
    )
    assert result["published"] == 1
    assert result["sb1_failed"] == 1
    state = PublisherStateStore(config.state_dir)
    success = state.get_success_for_collection(_COMPLETE_ID)
    assert success is not None
    assert success["status"] == "published"
