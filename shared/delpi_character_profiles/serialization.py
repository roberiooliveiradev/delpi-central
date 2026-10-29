"""Deterministic (de)serialization for the character-profile contract.

Pure stdlib. Serialized payloads always carry their version axis
(``schema_version`` / ``public_projection_version``) and unknown fields are
tolerated on load (forward compatibility) unless ``strict=True`` — which
fails explicitly instead of silently dropping data.
"""

from __future__ import annotations

import json
import typing
from dataclasses import fields, is_dataclass
from typing import Any, Mapping, TypeVar

from .models import (
    SCHEMA_VERSION,
    CharacterProfile,
    CharacterPublicProfile,
)
from .versioning import (
    assert_public_projection_compatible,
    assert_schema_compatible,
)

_T = TypeVar("_T")


def _to_plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: _to_plain(getattr(value, f.name))
            for f in fields(value)
            if getattr(value, f.name) is not None
        }
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


def _build(cls: type[_T], data: Mapping[str, Any], *, strict: bool) -> _T:
    """Rebuild a dataclass from a mapping, coercing lists to tuples.

    Annotations are strings under ``from __future__ import annotations``, so
    real types are resolved via ``get_type_hints`` once per call.
    """
    hints = typing.get_type_hints(cls)
    known = {f.name for f in fields(cls)}
    unknown = set(data) - known
    if unknown and strict:
        raise ValueError(f"unknown fields for {cls.__name__}: {sorted(unknown)}")
    kwargs: dict[str, Any] = {}
    for name in known & set(data):
        value = data[name]
        ftype = hints.get(name)
        if is_dataclass(ftype) and isinstance(value, Mapping):
            value = _build(ftype, value, strict=strict)
        elif isinstance(value, list):
            args = typing.get_args(ftype)
            item_type = args[0] if args else None
            value = tuple(
                _build(item_type, v, strict=strict)
                if is_dataclass(item_type) and isinstance(v, Mapping)
                else v
                for v in value
            )
        kwargs[name] = value
    return cls(**kwargs)


def profile_to_dict(profile: CharacterProfile) -> dict[str, Any]:
    """Serialize a full profile to a plain mapping (tuples → lists, ``None``
    fields omitted to keep payloads compact)."""
    return _to_plain(profile)


def profile_from_dict(
    data: Mapping[str, Any], *, strict: bool = False
) -> CharacterProfile:
    """Deserialize a profile payload, asserting schema compatibility first."""
    assert_schema_compatible(data.get("schema_version", SCHEMA_VERSION))
    return _build(CharacterProfile, data, strict=strict)


def public_profile_to_dict(
    public: CharacterPublicProfile,
) -> dict[str, Any]:
    """Serialize a public projection payload."""
    return _to_plain(public)


def public_profile_from_dict(
    data: Mapping[str, Any], *, strict: bool = False
) -> CharacterPublicProfile:
    """Deserialize a received public profile, asserting projection-version
    compatibility first."""
    assert_public_projection_compatible(
        data.get("public_projection_version", 1)
    )
    return _build(CharacterPublicProfile, data, strict=strict)


def dumps_deterministic(obj: Any) -> str:
    """Stable JSON: sorted keys, UTF-8, no incidental whitespace variance.

    Suitable for committed artifacts, content hashes and golden tests.
    """
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def profile_to_json(profile: CharacterProfile) -> str:
    return dumps_deterministic(profile_to_dict(profile))


def public_profile_to_json(public: CharacterPublicProfile) -> str:
    return dumps_deterministic(public_profile_to_dict(public))
