"""DELPI-CHARACTER-AVATARS-002 — avatar discovery projection (EVA).

Owner-local additive ``avatar_distribution`` on the persona projection:
official URL, version, MIME and integrity pinned to the canonical ficha +
served asset; safe-fail when the avatar is not approved.
"""

import dataclasses
import hashlib
from pathlib import Path, PurePosixPath

import pytest

from engineering_app.application.eva.agent_intelligence_service import (
    EvaAgentIntelligenceService as Svc,
)

_SERVICE_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _official_public_origin(monkeypatch: pytest.MonkeyPatch):
    """O contrato testado é a URL pública oficial — a canonical fallback
    https do serviço quando ``PUBLIC_BASE_URL`` não é configurada. Sem o
    pin, o valor ambiental de dev (http://localhost) quebraria a
    assertiva independente do código sob teste."""
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)


def test_avatar_distribution_official_metadata():
    dist = Svc.avatar_distribution()
    assert dist is not None
    assert dist["kind"] == "public_https"
    # origin is env-driven (PUBLIC_BASE_URL); the path contract is exact
    assert dist["url"].endswith(
        "/apps/engineering-api/public/characters/eva/avatar/avatar-v1.jpg"
    )
    assert dist["url"].startswith("https://")
    assert dist["version"] == "avatar-v1"
    assert dist["mime_type"] == "image/jpeg"
    assert (
        dist["sha256"]
        == "18d9e05fc91388e236d3df6a8118634a604caeaf9dc0626bed4de240efc4e6fc"
    )


def test_avatar_distribution_matches_canonical_ficha():
    profile = Svc.character_profile()
    filename = PurePosixPath(profile.appearance.avatar_reference).name
    dist = Svc.avatar_distribution()
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    assert dist["url"].endswith(f"/avatar/{filename}")
    assert dist["version"] == filename.rsplit(".", 1)[0]


def test_avatar_distribution_sha_matches_asset_bytes():
    dist = Svc.avatar_distribution()
    asset = Svc.character_profile().appearance.avatar_reference
    digest = hashlib.sha256((_SERVICE_ROOT / asset).read_bytes()).hexdigest()
    assert dist["sha256"] == digest


def test_avatar_distribution_in_persona_context():
    ctx = Svc.persona_context()
    assert ctx["avatar_status"] == "OFFICIAL_AVATAR_APPROVED"
    assert ctx["avatar_distribution"]["url"].startswith("https://")
    # canonical internal reference is preserved untouched
    assert "avatar_reference" in ctx


def test_avatar_distribution_safe_fail_when_not_approved():
    profile = Svc.character_profile()
    broken = dataclasses.replace(
        profile,
        appearance=dataclasses.replace(profile.appearance, avatar_status="UNSET"),
    )
    orig = Svc.character_profile
    Svc.character_profile = classmethod(lambda c: broken)
    try:
        assert Svc.avatar_distribution() is None
        assert "avatar_distribution" not in Svc.persona_context()
    finally:
        Svc.character_profile = orig


def test_avatar_distribution_base_url_honors_env(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://homolog.example.com")
    dist = Svc.avatar_distribution()
    assert dist["url"].startswith("https://homolog.example.com")


def test_avatar_distribution_url_not_user_controlled():
    dist = Svc.avatar_distribution()
    assert ".." not in dist["url"]
    assert "%" not in dist["url"]
    assert dist["url"].count("://") == 1
