"""InvestigationAnswer declared-schema contract (G1, doc 256/287).

``schema_version`` pins the declared-answer contract version. It is a
``Literal["1"]`` so the JSON schema exposed to the model carries a
``const`` constraint — a model that emits ``"1.0"`` or any other
version fails validation with a retryable schema error instead of the
declaration being silently dropped downstream
(``declared_schema_rejected``). No normalization, no parallel parser:
out-of-contract versions never reach the deterministic acceptor.
"""

from __future__ import annotations

import json

import pytest
from pydantic import TypeAdapter, ValidationError

from app.application.capability_provision.contracts import (
    InvestigationAnswer,
)

_ADAPTER = TypeAdapter(InvestigationAnswer)


def _payload(**overrides):
    base = {
        "schema_version": "1",
        "status": "complete",
        "answer": "produto X",
        "evidence_refs": [0],
        "unmet_obligations": [],
        "limitations": [],
        "clarification_question": None,
    }
    base.update(overrides)
    return base


class TestJsonSchemaSurface:
    def test_schema_version_is_const(self):
        schema = _ADAPTER.json_schema()
        prop = schema["properties"]["schema_version"]
        assert prop.get("const") == "1"
        assert prop.get("type") == "string"

    def test_contract_shape_stable(self):
        schema = _ADAPTER.json_schema()
        for name in (
            "status",
            "answer",
            "evidence_refs",
            "unmet_obligations",
            "limitations",
        ):
            assert name in schema["properties"], name


class TestVersionValidation:
    def test_version_one_accepted(self):
        answer = _ADAPTER.validate_python(_payload())
        assert answer.schema_version == "1"
        assert answer.answer == "produto X"

    @pytest.mark.parametrize("version", ["1.0", "2", "v1", 1, None])
    def test_incompatible_version_rejected(self, version):
        with pytest.raises(ValidationError):
            _ADAPTER.validate_python(_payload(schema_version=version))

    def test_missing_version_uses_contract_default(self):
        payload = _payload()
        payload.pop("schema_version")
        answer = _ADAPTER.validate_python(payload)
        assert answer.schema_version == "1"


class TestRoundTrip:
    def test_serialization_preserves_version(self):
        answer = _ADAPTER.validate_python(_payload())
        dumped = json.loads(
            _ADAPTER.dump_json(answer, by_alias=True)
        )
        assert dumped["schema_version"] == "1"
