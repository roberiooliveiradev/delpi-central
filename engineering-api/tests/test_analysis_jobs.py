"""DEC-VAL-030 — registry de jobs de análise prolongada."""
from engineering_app.application.drawing.analysis_jobs import (
    AnalysisJobStore, JOB_RUNNING_CAP_S)


def test_dedupe_same_params_shares_job():
    s = AnalysisJobStore()
    j1, c1 = s.get_or_start(
        product_code="90264017",
        identity_fingerprint="u1",
        params_fingerprint="p1")
    j2, c2 = s.get_or_start(
        product_code="90264017",
        identity_fingerprint="u1",
        params_fingerprint="p1")
    assert c1 is True and c2 is False
    assert j1.job_id == j2.job_id


def test_different_params_new_job():
    s = AnalysisJobStore()
    _, c1 = s.get_or_start(
        product_code="90264017",
        identity_fingerprint="u1", params_fingerprint="p1")
    _, c2 = s.get_or_start(
        product_code="90264017",
        identity_fingerprint="u1", params_fingerprint="p2")
    assert c1 and c2


def test_owner_isolation():
    s = AnalysisJobStore()
    job, _ = s.get_or_start(
        product_code="90264017",
        identity_fingerprint="u1", params_fingerprint="p1")
    assert s.get_for_owner(job.job_id, "u2") is None
    assert s.get_for_owner(job.job_id, "u1") is job


def test_complete_and_fail():
    s = AnalysisJobStore()
    job, _ = s.get_or_start(
        product_code="90264017",
        identity_fingerprint="u1", params_fingerprint="p1")
    s.complete(job.job_id, {"report": {"status": "X"}})
    assert s.get_for_owner(job.job_id, "u1").result["report"] == {"status": "X"}
    j2, _ = s.get_or_start(
        product_code="A",
        identity_fingerprint="u1", params_fingerprint="p1")
    s.fail(j2.job_id, "timeout", "t")
    assert s.get_for_owner(j2.job_id, "u1").error["code"] == "timeout"


def test_running_cap_fails_over_budget():
    import time
    s = AnalysisJobStore()
    job, _ = s.get_or_start(
        product_code="A", identity_fingerprint="u1",
        params_fingerprint="p1")
    job.created_ts = time.time() - JOB_RUNNING_CAP_S - 1
    j2, c2 = s.get_or_start(
        product_code="B", identity_fingerprint="u1",
        params_fingerprint="p1")
    assert s.get_for_owner(job.job_id, "u1").status == "FAILED"
    assert s.get_for_owner(job.job_id, "u1").error["code"] == "timeout"
