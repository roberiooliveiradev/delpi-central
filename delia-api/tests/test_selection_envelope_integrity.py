"""C2 — JSON envelope integrity for selection payloads (bounded rework).

``_group_summaries`` / ``_capability_payload`` previously applied a
raw ``[:MAX_SURFACE_CHARS]`` cut on the serialized envelope: the cut
could sever JSON structure, bisect a capability entry or drop the
appended ``business_subject``/``prior_observation`` — the model would
receive a syntactically invalid catalog. These tests freeze the
contract:

- output is always valid JSON;
- length never exceeds ``MAX_SURFACE_CHARS`` when the catalog
  structurally fits;
- optional fields survive whole or are structurally reduced —
  never severed mid-document;
- identifiers stay complete; under extreme pressure omissions are
  truthfully marked, never silently severed.
"""

from __future__ import annotations

import json

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
)
from app.application.capability_provision.orchestration import (
    MAX_SURFACE_CHARS,
    _capability_payload,
    _group_summaries,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import SpecialistOperationClass

MAX_DESC = 512  # generous upper bound for fabricated descriptions


def _cap(idx: int, desc_len: int = 40, group_id: str = "g"):
    name = f"cap_{idx}"
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id="openapi",
        remote_name=name,
        owner=group_id,
        operation_class=SpecialistOperationClass.READ,
        description="d" * desc_len,
        input_schema={"type": "object", "properties": {}},
        binding={"ref": name},
    )


def _group(group_id: str, caps) -> CapabilityGroup:
    return CapabilityGroup(
        provider_id="openapi",
        group_id=group_id,
        owner_ref=group_id,
        display_name=group_id,
        capabilities=tuple(caps),
        source=SourceRef(
            source_id=group_id,
            source_system=group_id,
            provider_name=group_id,
        ),
    )


def _groups(count: int, caps_each: int, desc_len: int = 40):
    return {
        f"openapi:grp{i}": _group(
            f"grp{i}", [_cap(i * 1000 + j, desc_len, f"grp{i}")
                        for j in range(caps_each)]
        )
        for i in range(count)
    }


def _observation(chars: int = 600):
    return {
        "prior_result_available": True,
        "authoritative": False,
        "untrusted_excerpt": "x" * chars,
    }


# ---------- _group_summaries ----------


def test_small_catalog_valid_json():
    payload = _group_summaries(_groups(2, 3))
    data = json.loads(payload)
    assert isinstance(data, list)
    assert len(payload) <= MAX_SURFACE_CHARS


def test_subject_only_envelope_valid_and_whole():
    payload = _group_summaries(
        _groups(2, 3), business_subject="terminal pino"
    )
    data = json.loads(payload)
    assert data["business_subject"] == "terminal pino"
    assert isinstance(data["capability_groups"], list)


def test_observation_only_envelope_valid():
    payload = _group_summaries(
        _groups(2, 3), prior_observation=_observation()
    )
    data = json.loads(payload)
    assert data["prior_observation"]["untrusted_excerpt"]


def test_both_optionals_valid_json():
    payload = _group_summaries(
        _groups(2, 3),
        prior_observation=_observation(),
        business_subject="terminal bala",
    )
    data = json.loads(payload)
    assert data["business_subject"] == "terminal bala"
    assert data["prior_observation"]["untrusted_excerpt"]


def test_over_limit_catalog_produces_valid_bounded_json():
    """10 groups x 20 caps with fat descriptions exceed 6000 chars."""
    payload = _group_summaries(_groups(10, 20, desc_len=2000))
    assert len(payload) <= MAX_SURFACE_CHARS
    data = json.loads(payload)  # must not raise — no mid-JSON cut
    assert isinstance(data, list)


def test_fairness_all_groups_listed_under_pressure():
    payload = _group_summaries(_groups(10, 20, desc_len=2000))
    data = json.loads(payload)
    groups_list = (
        data["capability_groups"] if isinstance(data, dict) else data
    )
    ids = {g["capability_group_id"] for g in groups_list}
    assert ids == {f"openapi:grp{i}" for i in range(10)}


def test_omission_is_truthfully_marked_not_severed():
    payload = _group_summaries(_groups(10, 20, desc_len=2000))
    data = json.loads(payload)
    groups_list = (
        data["capability_groups"] if isinstance(data, dict) else data
    )
    for g in groups_list:
        listed = len(g["capabilities"])
        omitted = g.get("capabilities_omitted", 0)
        # truthfulness: listed + omitted never exceeds the real 20
        assert listed + omitted <= 20
        if omitted:
            assert listed + omitted == 20


def test_max_subject_and_observation_survive_whole_or_bounded():
    subject = "s" * 240
    payload = _group_summaries(
        _groups(4, 8, desc_len=1500),
        prior_observation=_observation(4000),
        business_subject=subject,
    )
    data = json.loads(payload)
    assert len(payload) <= MAX_SURFACE_CHARS
    # subject is kept whole when included — never severed
    assert data["business_subject"] == subject


def test_unicode_and_escapes_roundtrip():
    cap = _cap(1, 5, "gã")
    cap = ProviderCapability(
        capability_id=cap.capability_id,
        group_id=cap.group_id,
        provider_id=cap.provider_id,
        remote_name=cap.remote_name,
        owner=cap.owner,
        operation_class=cap.operation_class,
        description='açúcar "quoted" \\ \n çñü',
        input_schema=cap.input_schema,
        binding=cap.binding,
    )
    payload = _group_summaries(
        {"openapi:gã": _group("gã", [cap])},
        business_subject='términal "bala"',
    )
    data = json.loads(payload)
    assert data["business_subject"] == 'términal "bala"'


# ---------- _capability_payload ----------


def test_capability_payload_small_valid():
    payload = _capability_payload(_group("g", [_cap(i) for i in range(3)]))
    data = json.loads(payload)
    assert isinstance(data, list)
    assert len(payload) <= MAX_SURFACE_CHARS


def test_capability_payload_over_limit_valid_bounded():
    """80 capabilities with fat descriptions exceed 6000 chars."""
    group = _group("g", [_cap(i, desc_len=400) for i in range(80)])
    payload = _capability_payload(
        group,
        prior_observation=_observation(3000),
        business_subject="terminal pino",
    )
    assert len(payload) <= MAX_SURFACE_CHARS
    data = json.loads(payload)
    caps = (
        data["capabilities"] if isinstance(data, dict) else data
    )
    assert isinstance(caps, list)
    assert data["business_subject"] == "terminal pino"
    if isinstance(data, dict) and data.get("capabilities_omitted"):
        assert len(caps) + data["capabilities_omitted"] == 80


def test_capability_payload_identifiers_complete_under_compaction():
    group = _group("g", [_cap(i, desc_len=300) for i in range(60)])
    payload = _capability_payload(group)
    data = json.loads(payload)
    caps = data["capabilities"] if isinstance(data, dict) else data
    for entry in caps:
        assert entry["remote_name"].startswith("cap_")
        assert entry["operation_class"] == "READ"
