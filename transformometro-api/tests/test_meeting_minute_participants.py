"""Participant/signer normalization — fail-closed identity rules."""

from __future__ import annotations

import pytest

from tm_app.application.services.meeting_minute_participants import (
    derive_signers_from_participants,
    normalize_participants,
)


def test_normalize_internal_requires_user_id():
    with pytest.raises(ValueError, match="user_id"):
        normalize_participants(
            [{"display_name": "Robério", "must_sign": True}]
        )


def test_normalize_must_sign_requires_identity():
    with pytest.raises(ValueError, match="must_sign"):
        normalize_participants(
            [
                {
                    "display_name": "Convidado",
                    "is_external": True,
                    "must_sign": True,
                }
            ]
        )


def test_normalize_internal_signer_ok():
    rows = normalize_participants(
        [
            {
                "user_id": "11111111-1111-1111-1111-111111111111",
                "display_name": "Ana",
                "must_sign": True,
                "role_in_meeting": "chair",
            }
        ]
    )
    assert rows[0]["user_id"] == "11111111-1111-1111-1111-111111111111"
    assert rows[0]["must_sign"] is True
    signers = derive_signers_from_participants(rows)
    assert len(signers) == 1
    assert signers[0]["display_name"] == "Ana"


def test_normalize_presence_only_external_ok():
    rows = normalize_participants(
        [
            {
                "display_name": "Visitante",
                "is_external": True,
                "must_sign": False,
            }
        ]
    )
    assert rows[0]["is_external"] is True
    assert derive_signers_from_participants(rows) == []


def test_derive_signers_skips_non_signing():
    rows = normalize_participants(
        [
            {
                "user_id": "11111111-1111-1111-1111-111111111111",
                "display_name": "Ana",
                "must_sign": False,
            },
            {
                "user_id": "22222222-2222-2222-2222-222222222222",
                "display_name": "Bia",
                "must_sign": True,
            },
        ]
    )
    signers = derive_signers_from_participants(rows)
    assert [s["display_name"] for s in signers] == ["Bia"]
