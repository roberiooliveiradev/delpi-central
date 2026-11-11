"""Offline lifecycle tests for INT-1 eval subject-token acquisition.

No live Keycloak / MCP / LLM. Never asserts on raw token values beyond
fixture strings.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def _load_auth():
    path = _SCRIPTS / "int1_eval_subject_auth.py"
    spec = importlib.util.spec_from_file_location("int1_eval_subject_auth", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def auth():
    return _load_auth()


def test_acquire_records_expires_in_without_logging_secret(auth, monkeypatch):
    monkeypatch.setenv("DEV_PORTAL_USERNAME", "u")
    monkeypatch.setenv("DEV_PORTAL_PASSWORD", "p")

    def fake_post(_url, _form):
        return {
            "access_token": "fixture-access-token-aaaaaaaa",
            "expires_in": 300,
            "token_type": "Bearer",
        }

    session = auth.acquire_subject_access_session(
        http_post=fake_post, now=1_700_000_000.0
    )
    assert session.expires_in_seconds == 300
    assert session.expires_at_epoch == 1_700_000_000.0 + 300
    assert session.token_fingerprint
    assert "fixture-access-token" not in str(
        auth.subject_session_public_meta(session)
    )
    assert auth.subject_session_is_fresh(
        session, now=1_700_000_000.0, skew_seconds=90
    )
    assert not auth.subject_session_is_fresh(
        session, now=1_700_000_250.0, skew_seconds=90
    )


def test_empty_token_fails_closed(auth, monkeypatch):
    monkeypatch.setenv("DEV_PORTAL_USERNAME", "u")
    monkeypatch.setenv("DEV_PORTAL_PASSWORD", "p")

    def fake_post(_url, _form):
        return {"access_token": "", "expires_in": 60}

    with pytest.raises(RuntimeError, match="subject_token_empty"):
        auth.acquire_subject_access_session(http_post=fake_post)


def test_reacquire_yields_distinct_fingerprints(auth, monkeypatch):
    monkeypatch.setenv("DEV_PORTAL_USERNAME", "u")
    monkeypatch.setenv("DEV_PORTAL_PASSWORD", "p")
    tokens = iter(["tok-one-11111111", "tok-two-22222222"])

    def fake_post(_url, _form):
        return {"access_token": next(tokens), "expires_in": 300}

    a = auth.acquire_subject_access_session(http_post=fake_post)
    b = auth.acquire_subject_access_session(http_post=fake_post)
    assert a.token_fingerprint != b.token_fingerprint


def test_near_expiry_requires_reacquire(auth, monkeypatch):
    monkeypatch.setenv("DEV_PORTAL_USERNAME", "u")
    monkeypatch.setenv("DEV_PORTAL_PASSWORD", "p")

    def fake_post(_url, _form):
        return {"access_token": "tok-near", "expires_in": 100}

    session = auth.acquire_subject_access_session(
        http_post=fake_post, now=1000.0
    )
    assert not auth.subject_session_is_fresh(
        session, now=1080.0, skew_seconds=90
    )


def test_missing_expires_in_treated_as_fresh(auth, monkeypatch):
    monkeypatch.setenv("DEV_PORTAL_USERNAME", "u")
    monkeypatch.setenv("DEV_PORTAL_PASSWORD", "p")

    def fake_post(_url, _form):
        return {"access_token": "tok-no-exp"}

    session = auth.acquire_subject_access_session(http_post=fake_post, now=1.0)
    assert session.expires_at_epoch is None
    assert auth.subject_session_is_fresh(session, now=10_000.0)
