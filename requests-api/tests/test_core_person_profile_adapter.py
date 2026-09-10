from __future__ import annotations

from requests_app.infrastructure.gateways.core_person_profile_adapter import (
    InMemoryCorePersonProfileAdapter,
)


def test_inmemory_adapter_photo_and_lookup():
    adapter = InMemoryCorePersonProfileAdapter()
    adapter.photos["u-1"] = (b"img", "image/png", "photo.png")
    adapter.has_photo["u-1"] = True
    adapter.has_photo["u-2"] = False

    assert adapter.get_photo("u-1") == (b"img", "image/png", "photo.png")
    assert adapter.get_photo("missing") is None
    assert adapter.lookup_has_photo(["u-1", "u-2"]) == {
        "u-1": True,
        "u-2": False,
    }
