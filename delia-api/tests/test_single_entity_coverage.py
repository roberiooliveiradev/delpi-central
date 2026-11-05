"""Single-entity owner shapes — coverage binding (doc 289 residual B).

``_resolver_entities`` extracted list collections only; a
``get_product_detail``-style response (``data.product`` = single
Mapping carrying the owner-declared ``code``) never became evidence,
so the requested identifier stayed ``uncovered`` and the turn ended
NON_GROUNDED despite a real owner record. The fix recognizes a single
entity Mapping under the data surface — bounded by an owner-declared
identity field, never by key name alone.
"""

from __future__ import annotations

from app.application.capability_provision.generic_evidence_renderer import (
    _resolver_entities,
)

_DETAIL_SHAPE = {
    "action_id": "get_product_detail",
    "status": "ok",
    "entity": "product_detail",
    "shape": "single_entity",
    "data": {
        "product": {
            "code": "99999999",
            "description": "PRODUTO UTILIZADO GENERICO PODER TERCEIROS",
            "type": "MP",
            "group_code": "9999",
            "active": "S",
            "blocked": "1",
        }
    },
    "truncated": False,
    "is_complete": True,
}


class TestSingleEntityExtraction:
    def test_single_entity_under_data_is_evidence(self):
        entities = _resolver_entities(_DETAIL_SHAPE)
        assert len(entities) == 1
        assert entities[0]["code"] == "99999999"

    def test_entity_field_uses_any_declared_code_key(self):
        shape = {
            "data": {
                "record": {"product_code": "50220013", "description": "X"}
            }
        }
        entities = _resolver_entities(shape)
        assert len(entities) == 1
        assert entities[0]["product_code"] == "50220013"

    def test_collections_still_take_precedence(self):
        shape = {
            "data": {
                "items": [{"product_code": "1"}],
                "product": {"code": "2"},
            }
        }
        entities = _resolver_entities(shape)
        assert entities[0].get("product_code") == "1"

    def test_metadata_mapping_without_code_is_not_entity(self):
        shape = {
            "data": {
                "pagination": {"page": 1, "total": 5},
                "items": [{"product_code": "7"}],
            }
        }
        entities = _resolver_entities(shape)
        assert [e.get("product_code") for e in entities] == ["7"]

    def test_mapping_without_code_fields_yields_nothing(self):
        shape = {"data": {"summary": {"total": 3, "note": "x"}}}
        assert _resolver_entities(shape) == ()

    def test_capability_descriptor_is_not_entity(self):
        shape = {
            "data": {
                "descriptor": {
                    "code": "read",
                    "name": "read",
                    "inputSchema": {"type": "object"},
                }
            }
        }
        assert _resolver_entities(shape) == ()
