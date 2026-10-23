"""Requester identity enrichment — Core↔Protheus deterministic link (PR.IDENTITY.S1)."""

from __future__ import annotations

import pytest

from app.application.services.requester_identity_service import (
    RequesterIdentityService,
)


class FakeCoreGateway:
    def __init__(
        self,
        mappings=None,
        directory=None,
        profiles=None,
        photo=None,
        fail_identities=False,
    ):
        self._mappings = mappings or {}
        self._directory = directory or {}
        self._profiles = profiles or {}
        self._photo = photo
        self.fail_identities = fail_identities
        self.identity_calls: list[list[str]] = []
        self.directory_calls: list[list[str]] = []
        self.profile_calls: list[list[str]] = []
        self.photo_calls: list[str] = []

    def lookup_protheus_identities(self, *, protheus_user_ids):
        self.identity_calls.append(list(protheus_user_ids))
        if self.fail_identities:
            raise RuntimeError("core down")
        return {pid: self._mappings[pid] for pid in protheus_user_ids if pid in self._mappings}

    def lookup_directory_users(self, *, access_token, user_ids):
        self.directory_calls.append(list(user_ids))
        return {uid: self._directory[uid] for uid in user_ids if uid in self._directory}

    def lookup_person_profiles(self, *, user_ids):
        self.profile_calls.append(list(user_ids))
        return {uid: self._profiles[uid] for uid in user_ids if uid in self._profiles}

    def get_person_profile_photo(self, user_id):
        self.photo_calls.append(user_id)
        return self._photo


def _item(pid, name="ELAINE"):
    return {
        "request_number": "000001",
        "requester": {"protheus_user_id": pid, "code": "USR01", "name": name},
    }


def test_mapped_requester_gets_core_display_name():
    gw = FakeCoreGateway(
        mappings={"000123": {"user_id": "u-1", "protheus_user_id": "000123"}},
        directory={"u-1": {"id": "u-1", "name": "Elaine Souza"}},
    )
    payload = {"items": [_item("000123")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="tok")
    requester = payload["items"][0]["requester"]
    assert requester["display_name"] == "Elaine Souza"
    assert requester["name"] == "ELAINE"  # source untouched


def test_distinct_ids_deduplicated_single_lookup():
    gw = FakeCoreGateway(
        mappings={
            "1": {"user_id": "u-1"},
            "2": {"user_id": "u-2"},
        },
        directory={"u-1": {"name": "Ana"}, "u-2": {"name": "Beto"}},
    )
    payload = {"items": [_item("1"), _item("2"), _item("1"), _item("1")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    assert gw.identity_calls == [["1", "2"]]
    assert sorted(gw.directory_calls[0]) == ["u-1", "u-2"]
    assert payload["items"][0]["requester"]["display_name"] == "Ana"
    assert payload["items"][1]["requester"]["display_name"] == "Beto"
    assert payload["items"][3]["requester"]["display_name"] == "Ana"


def test_unmapped_requester_keeps_source_name():
    gw = FakeCoreGateway(mappings={})  # no link
    payload = {"items": [_item("999")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    requester = payload["items"][0]["requester"]
    assert "display_name" not in requester
    assert requester["name"] == "ELAINE"
    assert gw.directory_calls == []  # no user ids → no directory call


def test_user_not_in_directory_keeps_source_name():
    gw = FakeCoreGateway(mappings={"5": {"user_id": "u-5"}}, directory={})
    payload = {"items": [_item("5")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    assert "display_name" not in payload["items"][0]["requester"]


def test_core_unavailable_preserves_payload():
    gw = FakeCoreGateway(fail_identities=True)
    payload = {"items": [_item("1")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    assert payload["items"][0]["requester"]["name"] == "ELAINE"
    assert "display_name" not in payload["items"][0]["requester"]


def test_detail_payload_enriches_header_and_lines():
    gw = FakeCoreGateway(
        mappings={"7": {"user_id": "u-7"}, "8": {"user_id": "u-8"}},
        directory={"u-7": {"name": "Carla"}, "u-8": {"name": "Diego"}},
    )
    payload = {
        "requester": {"protheus_user_id": "7", "code": "C7", "name": "CARLA"},
        "lines": [
            {"requester": {"protheus_user_id": "8", "name": "DIEGO"}},
            {"requester": {"protheus_user_id": "", "name": "SEM ID"}},
            {"other": "no requester"},
        ],
    }
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    assert payload["requester"]["display_name"] == "Carla"
    assert payload["lines"][0]["requester"]["display_name"] == "Diego"
    assert "display_name" not in payload["lines"][1]["requester"]


def test_no_requesters_no_core_calls():
    gw = FakeCoreGateway()
    payload = {"items": [{"request_number": "1"}]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    assert gw.identity_calls == [] and gw.directory_calls == []


def test_leading_zeros_preserved_in_lookup():
    gw = FakeCoreGateway(mappings={"000042": {"user_id": "u-9"}}, directory={"u-9": {"name": "Zoe"}})
    payload = {"items": [_item("000042"), _item("42")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    assert gw.identity_calls == [["000042", "42"]]
    assert payload["items"][0]["requester"]["display_name"] == "Zoe"
    assert "display_name" not in payload["items"][1]["requester"]


def test_empty_access_token_still_uses_mappings_only_without_names():
    gw = FakeCoreGateway(mappings={"1": {"user_id": "u-1"}})
    payload = {"items": [_item("1")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="")
    assert gw.directory_calls == []
    assert "display_name" not in payload["items"][0]["requester"]


def test_mapped_requester_with_photo_gets_bff_photo_url():
    gw = FakeCoreGateway(
        mappings={"000123": {"user_id": "u-1"}},
        directory={"u-1": {"name": "Elaine Souza"}},
        profiles={"u-1": {"user_id": "u-1", "has_photo": True}},
    )
    payload = {"items": [_item("000123")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    requester = payload["items"][0]["requester"]
    assert requester["photo_url"] == "/purchase-requests/requesters/000123/photo"
    assert "u-1" not in requester["photo_url"]  # Core id never leaves the server


def test_mapped_requester_without_photo_has_no_photo_url():
    gw = FakeCoreGateway(
        mappings={"000123": {"user_id": "u-1"}},
        profiles={"u-1": {"user_id": "u-1", "has_photo": False}},
    )
    payload = {"items": [_item("000123")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    assert "photo_url" not in payload["items"][0]["requester"]


def test_unmapped_requester_never_gets_photo_url():
    gw = FakeCoreGateway(
        mappings={},
        profiles={"u-x": {"user_id": "u-x", "has_photo": True}},
    )
    payload = {"items": [_item("999")]}
    RequesterIdentityService(core_gateway=gw).enrich_payload(payload, access_token="t")
    assert "photo_url" not in payload["items"][0]["requester"]


def test_resolve_mapped_user_id_returns_uid_only_when_mapped():
    gw = FakeCoreGateway(mappings={"5": {"user_id": "u-5"}})
    service = RequesterIdentityService(core_gateway=gw)
    assert service.resolve_mapped_user_id("5") == "u-5"
    assert service.resolve_mapped_user_id("6") is None
    assert service.resolve_mapped_user_id("") is None


def test_get_requester_photo_streams_bytes_for_mapped_user():
    gw = FakeCoreGateway(
        mappings={"5": {"user_id": "u-5"}},
        photo=(b"\x89PNG", "image/png", "u5.png"),
    )
    service = RequesterIdentityService(core_gateway=gw)
    assert service.get_requester_photo("5") == (b"\x89PNG", "image/png", "u5.png")
    assert gw.photo_calls == ["u-5"]
    assert service.get_requester_photo("404") is None
    assert gw.photo_calls == ["u-5"]  # unmapped → no photo fetch
