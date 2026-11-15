"""RQ-OPS — resource monitor, admission gate, job listing e existing_only.

Cobre: métricas com escopo rotulado (RQ-02), consulta read-only de
estado (RQ-01), listagem owner-scoped de jobs (RQ-03), admissão
atômica fail-closed (RQ-04), fases/progresso honesto (RQ-06) e
isolamento de identidade (RQ-09) — tudo sem OCR real.
"""

from __future__ import annotations

import asyncio
import threading

import pytest

from engineering_app.application.drawing import visual_admission
from engineering_app.application.drawing.analysis_jobs import (
    AnalysisJobStore,
    job_summary,
    reset_analysis_job_store,
    analysis_job_store,
)
from engineering_app.application.drawing.visual_admission import (
    ADMITTED,
    BUSY,
    OCR_UNAVAILABLE,
    RESOURCE_LIMIT,
    UNKNOWN_CAPACITY,
    ocr_runtime_status,
    reset_visual_admission_gate,
    visual_admission_gate,
)
from engineering_app.infrastructure.extraction import resource_monitor
from engineering_app.interface.mcp import semantic_bridge as sem
from tests.test_eva_mcp import _human_user, _set_context


@pytest.fixture(autouse=True)
def _clear_context():
    from delpi_auth.request_context import (
        clear_current_user,
        clear_request_authorization,
    )

    clear_current_user()
    clear_request_authorization()
    yield
    clear_current_user()
    clear_request_authorization()


@pytest.fixture
def flags(monkeypatch):
    monkeypatch.setenv("ENG_DRAWING_BENCHMARK_ENABLED", "true")
    monkeypatch.setenv("ENG_DRAWING_OCR_BENCHMARK_ENABLED", "true")
    reset_visual_admission_gate()
    reset_analysis_job_store()
    yield
    reset_analysis_job_store()
    reset_visual_admission_gate()


@pytest.fixture
def admit_ok(monkeypatch, flags):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {"admission_budget_mb": 9999}),
    )


# --- RQ-02 — resource monitor ---------------------------------------------


def test_meminfo_scope_and_units(tmp_path):
    fake = tmp_path / "meminfo"
    fake.write_text(
        "MemTotal:       10182608 kB\n"
        "MemFree:         512000 kB\n"
        "MemAvailable:   4194304 kB\n"
        "SwapTotal:      6291456 kB\n"
        "SwapFree:       1048576 kB\n"
    )
    info = resource_monitor.read_meminfo(fake)
    assert info["MemTotal"] == 9943
    assert info["MemAvailable"] == 4096
    assert info["SwapTotal"] == 6144


def test_meminfo_unavailable_returns_none(tmp_path):
    assert resource_monitor.read_meminfo(tmp_path / "nope") is None


def test_resource_usage_labels_scopes():
    usage = resource_monitor.resource_usage()
    mem = usage["memory"]
    assert "host_scope" in mem and "container_scope" in mem
    assert mem["host_scope"]["state"] in {"KNOWN", "UNKNOWN"}
    assert mem["container_scope"]["state"] in {"KNOWN", "UNKNOWN"}
    assert usage["observed_at"] > 0
    # Nada fabricado: campos UNKNOWN são None, não números inventados.
    if mem["host_scope"]["state"] == "UNKNOWN":
        assert mem["host_scope"]["available_mb"] is None


def test_admission_budget_fail_closed_unknown():
    usage = {
        "memory": {
            "admission_budget_mb": None,
            "admission_required_mb": 2560,
            "host_scope": {"state": "UNKNOWN"},
            "container_scope": {"state": "UNKNOWN"},
        }
    }
    decision, detail = resource_monitor.admission_budget_check(usage)
    assert decision == "unknown_capacity"
    assert detail["admission_budget_mb"] is None


def test_admission_budget_resource_limit():
    usage = {
        "memory": {
            "admission_budget_mb": 512,
            "admission_required_mb": 2560,
            "host_scope": {"state": "KNOWN"},
            "container_scope": {"state": "KNOWN"},
        }
    }
    decision, _ = resource_monitor.admission_budget_check(usage)
    assert decision == "resource_limit"


# --- RQ-04 — admission gate (atomicidade) ---------------------------------


def test_gate_single_slot_atomic(flags, monkeypatch):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {}),
    )
    gate = visual_admission_gate()
    outcome1, _ = gate.try_acquire()
    outcome2, detail = gate.try_acquire()
    assert outcome1 == ADMITTED
    assert outcome2 == BUSY
    assert detail["active_heavy_jobs"] == 1
    gate.release()
    outcome3, _ = gate.try_acquire()
    assert outcome3 == ADMITTED
    gate.release()


def test_gate_concurrent_callers_one_wins(flags, monkeypatch):
    """AC-04 — corrida real de threads: exatamente um ADMITTED."""
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {}),
    )
    gate = visual_admission_gate()
    results = []
    barrier = threading.Barrier(4)

    def racer():
        barrier.wait()
        results.append(gate.try_acquire()[0])

    threads = [threading.Thread(target=racer) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count(ADMITTED) == 1
    assert results.count(BUSY) == 3


def test_gate_ocr_disabled(monkeypatch):
    monkeypatch.delenv("ENG_DRAWING_OCR_BENCHMARK_ENABLED", raising=False)
    reset_visual_admission_gate()
    outcome, _ = visual_admission_gate().try_acquire()
    assert outcome == OCR_UNAVAILABLE


def test_gate_fail_closed_on_unknown_capacity(flags, monkeypatch):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("unknown_capacity", {}),
    )
    outcome, detail = visual_admission_gate().try_acquire()
    assert outcome == UNKNOWN_CAPACITY
    assert "fail-closed" in detail["reason"]


def test_gate_resource_limit(flags, monkeypatch):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("resource_limit", {}),
    )
    outcome, _ = visual_admission_gate().try_acquire()
    assert outcome == RESOURCE_LIMIT


# --- RQ-01 — ocr_runtime_status -------------------------------------------


def test_runtime_status_shape_and_vocabulary(flags):
    status = ocr_runtime_status()
    assert status["status"] in {
        "AVAILABLE", "BUSY", "RESOURCE_LIMIT",
        "UNAVAILABLE", "DEGRADED", "UNKNOWN",
    }
    assert status["ocr_enabled"] is True
    assert "observed_at" in status and status["freshness"] == "live"
    ru = status["resource_usage"]
    assert set(ru["scope"]) == {"host", "container"}
    assert "active_workers" in ru["ocr"]
    assert "available_slots" in ru["ocr"]
    assert status["resource_limits"]["isolation"] == "subprocess"
    assert status["result"]["process_local_jobs"] is True


def test_runtime_status_is_read_only(flags, monkeypatch):
    """AC-01 — consultar status nunca toca executor nem store."""
    calls = []
    monkeypatch.setattr(
        visual_admission.subprocess_executor,
        "active_workers",
        lambda: calls.append(1) or 0,
    )
    ocr_runtime_status()
    assert len(calls) <= 1  # só a leitura do contador — nenhum spawn


# --- RQ-03/06 — job store: listagem, existing_only, fases, supersede ------


def test_list_for_owner_isolated():
    store = AnalysisJobStore()
    store.get_or_start(
        product_code="P1",
        identity_fingerprint="alice",
        params_fingerprint="x",
        analysis_type="t",
    )
    store.get_or_start(
        product_code="P2",
        identity_fingerprint="bob",
        params_fingerprint="x",
        analysis_type="t",
    )
    mine = store.list_for_owner("alice")
    assert len(mine) == 1 and mine[0].product_code == "P1"
    assert all(
        j.owner_hash == store.owner_hash("alice") for j in mine
    )


def test_find_existing_creates_nothing():
    store = AnalysisJobStore()
    assert (
        store.find_existing(
            product_code="P1",
            identity_fingerprint="alice",
            params_fingerprint="x",
        )
        is None
    )
    assert store.list_for_owner("alice") == []


def test_supersede_frees_idempotent_key():
    store = AnalysisJobStore()
    job, _ = store.get_or_start(
        product_code="P1",
        identity_fingerprint="alice",
        params_fingerprint="x",
    )
    store.complete(job.job_id, {"ok": True})
    store.set_document_sha(job.job_id, "sha-old")
    store.supersede(job.job_id)
    assert job.status == "EXPIRED"
    assert job.error["code"] == "stale_document"
    # Mesma chave agora cria job novo.
    job2, created = store.get_or_start(
        product_code="P1",
        identity_fingerprint="alice",
        params_fingerprint="x",
    )
    assert created is True and job2.job_id != job.job_id
    # Job antigo continua consultável pelo owner (evidência), como EXPIRED.
    old = store.get_for_owner(job.job_id, "alice")
    assert old.status == "EXPIRED"


def test_phase_transitions_and_summary():
    store = AnalysisJobStore()
    job, _ = store.get_or_start(
        product_code="P1",
        identity_fingerprint="alice",
        params_fingerprint="x",
        analysis_type="product.drawing_understanding",
    )
    store.update_phase(job.job_id, "OCR")
    assert job.phase == "OCR"
    store.complete(job.job_id, {"r": 1})
    assert job.phase is None
    summary = job_summary(job)
    for key in (
        "job_id", "status", "phase", "created_at", "started_at",
        "finished_at", "elapsed_seconds", "result_available",
        "document_sha", "process_local_registry",
    ):
        assert key in summary
    assert summary["status"] == "COMPLETED"
    assert summary["result_available"] is True
    assert summary["elapsed_seconds"] >= 0


# --- RQ-07 — superfície MCP read (drawing.*) ------------------------------


async def test_read_runtime_status_via_semantic_read(flags):
    _set_context(_human_user())
    res = await sem.tool_read(entity="drawing", action="runtime_status")
    assert not res.is_error
    data = res.structured_content["data"]
    assert "ocr_runtime_status" in data
    assert data["ocr_runtime_status"]["status"] in {
        "AVAILABLE", "BUSY", "RESOURCE_LIMIT",
        "UNAVAILABLE", "DEGRADED", "UNKNOWN",
    }


async def test_read_runtime_status_requires_human(flags):
    res = await sem.tool_read(entity="drawing", action="runtime_status")
    assert res.is_error


async def test_read_job_list_owner_scoped(flags, monkeypatch):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {}),
    )

    async def instant(context, code, question, phase_cb=None):
        return {"analysis_type": "product.drawing_understanding", "ok": True}

    monkeypatch.setattr(sem, "_execute_drawing_understanding", instant)
    _set_context(_human_user())
    started = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    job_id = started.structured_content["data"]["job_id"]
    listed = await sem.tool_read(entity="drawing", action="job_list")
    data = listed.structured_content["data"]
    assert data["count"] == 1
    assert data["jobs"][0]["job_id"] == job_id
    assert data["process_local_registry"] is True
    # Outro usuário não vê nada — nem a existência.
    _set_context(_human_user(id="user-2"))
    other = await sem.tool_read(entity="drawing", action="job_list")
    assert other.structured_content["data"]["count"] == 0


# --- RQ-03C — existing_only nunca dispara OCR ------------------------------


async def test_existing_only_no_result_typed_404(flags, admit_ok):
    # _execute jamais é monkeypatched aqui: se existing_only iniciar
    # processamento, a fixture admit_ok não o impediria e o job ficaria
    # RUNNING em vez de 404 — o próprio comportamento denuncia.
    _set_context(_human_user())
    res = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030", "existing_only": True},
    )
    assert res.is_error
    assert res.structured_content["error_code"] == "no_existing_result"
    assert res.structured_content["status_code"] == 404


async def test_existing_only_returns_running_job(flags, monkeypatch):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {}),
    )
    release = asyncio.Event()

    async def slow(context, code, question, phase_cb=None):
        await release.wait()
        return {"analysis_type": "t", "ok": True}

    monkeypatch.setattr(sem, "_execute_drawing_understanding", slow)
    _set_context(_human_user())
    started = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    job_id = started.structured_content["data"]["job_id"]
    again = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={
            "product_code": "90264030",
            "existing_only": True,
        },
    )
    assert not again.is_error
    data = again.structured_content["data"]
    assert data["status"] == "RUNNING" and data["job_id"] == job_id
    release.set()


# --- RQ-04 — admissão via MCP ----------------------------------------------


async def test_second_heavy_job_rejected_busy(flags, monkeypatch):
    """AC-04 — um job RUNNING segura o slot; produto diferente → BUSY."""
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {}),
    )
    release = asyncio.Event()

    async def slow(context, code, question, phase_cb=None):
        await release.wait()
        return {"analysis_type": "t", "ok": True}

    monkeypatch.setattr(sem, "_execute_drawing_understanding", slow)
    _set_context(_human_user())
    first = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    assert not first.is_error
    second = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264017"},
    )
    assert second.is_error
    body = second.structured_content
    assert body["error_code"] == "ocr_busy"
    assert body["status_code"] == 503
    assert body["data"]["admission_state"] == BUSY
    release.set()


async def test_admission_releases_slot_on_failure(flags, monkeypatch):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {}),
    )

    async def boom(context, code, question, phase_cb=None):
        raise RuntimeError("crash")

    monkeypatch.setattr(sem, "_execute_drawing_understanding", boom)
    _set_context(_human_user())
    await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    for _ in range(100):
        if visual_admission_gate().active_heavy_jobs() == 0:
            break
        await asyncio.sleep(0.01)
    assert visual_admission_gate().active_heavy_jobs() == 0


# --- RQ-03D — identidade documental ----------------------------------------


async def test_stale_document_not_reused(flags, monkeypatch):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {}),
    )
    calls = []

    async def instant(context, code, question, phase_cb=None):
        calls.append(code)
        return {"analysis_type": "t", "ok": True}

    monkeypatch.setattr(sem, "_execute_drawing_understanding", instant)
    _set_context(_human_user())
    first = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    job_id = first.structured_content["data"]["job_id"]
    for _ in range(100):
        poll = await sem.tool_analyze(
            analysis_type="product.drawing_understanding",
            parameters={"product_code": "90264030", "job_id": job_id},
        )
        if not poll.is_error and poll.structured_content["data"].get(
            "status"
        ) == "COMPLETED":
            break
        await asyncio.sleep(0.01)
    store = analysis_job_store()
    store.set_document_sha(job_id, "sha-old-doc")
    # Documento vigente difere → supersede + nova análise.
    monkeypatch.setattr(
        sem, "_current_drawing_document_sha", _async_return("sha-new-doc")
    )
    again = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    assert not again.is_error
    data = again.structured_content["data"]
    assert data["status"] == "RUNNING"
    assert data["job_id"] != job_id
    for _ in range(100):
        if calls.count("90264030") == 2:
            break
        await asyncio.sleep(0.01)
    assert calls.count("90264030") == 2
    # E o job antigo aparece como EXPIRED, não COMPLETED.
    old = store.get_for_owner(
        job_id, _fp_of("user-1")
    )
    assert old.status == "EXPIRED"


async def test_existing_only_stale_document(flags, monkeypatch):
    monkeypatch.setattr(
        resource_monitor,
        "admission_budget_check",
        lambda usage=None: ("ok", {}),
    )
    store = analysis_job_store()
    ident = _fp_of("user-1")
    job, _ = store.get_or_start(
        product_code="90264030",
        identity_fingerprint=ident,
        params_fingerprint=_params_fp_of(),
        analysis_type="product.drawing_understanding",
    )
    store.complete(job.job_id, {"ok": True})
    store.set_document_sha(job.job_id, "sha-old-doc")
    monkeypatch.setattr(
        sem, "_current_drawing_document_sha", _async_return("sha-new-doc")
    )
    _set_context(_human_user())
    res = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030", "existing_only": True},
    )
    assert res.is_error
    assert res.structured_content["error_code"] == "stale_document"


def _fp_of(user_id: str) -> str:
    import hashlib

    return hashlib.sha256(f"uid:{user_id}".encode()).hexdigest()[:20]


def _params_fp_of() -> str:
    import hashlib
    import json

    from engineering_app.application.drawing.perception_contract import (
        TABLE_PERCEPTION_REVISION,
    )

    return hashlib.sha256(
        json.dumps(
            {
                "kind": "product.drawing_understanding",
                "code": "90264030",
                "table_perception": TABLE_PERCEPTION_REVISION,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()[:20]


def _async_return(value):
    async def _inner(*a, **kw):
        return value

    return _inner
