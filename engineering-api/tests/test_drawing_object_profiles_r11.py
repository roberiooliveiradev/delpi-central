"""R11 — object profiles: modelos, relações, semântica consumo×montagem."""
import pytest
from engineering_app.domain.drawing.object_profiles import (
    DrawingObjectSet, ObjectType, ObservationState, VerificationState,
    RelationType, DrawingRelation, bom_occurrence, table_item, dimension,
)
from engineering_app.application.drawing.object_profiles_builder import (
    build_object_profiles,
)


def test_bom_occurrence_preserves_consumption_hierarchy():
    o = bom_occurrence("occ1", component_code="10210771", parent_code="P",
                       bom_level=1, bom_path="P>10210771",
                       consumption_quantity="500", consumption_unit="mm")
    assert o.attributes["consumption_quantity"] == "500"
    assert o.attributes["consumption_unit"] == "mm"
    assert o.attributes["bom_path"] == "P>10210771"
    assert o.official is True


def test_consumption_vs_assembly_never_same():
    """Cabo 500mm na BOM ≠ quantidade 1 no desenho — campos distintos."""
    occ = bom_occurrence("o1", component_code="C1", parent_code="P",
                         bom_level=0, bom_path="P", consumption_quantity="500",
                         consumption_unit="mm")
    item = table_item("r0", item_label="A1", assembly_quantity="1",
                      component_code_candidate="C1",
                      description_candidate="CABO", table_region="t")
    assert occ.attributes["consumption_quantity"] == "500"
    assert item.attributes["assembly_quantity"] == "1"
    # nunca comparados como a mesma quantidade
    assert occ.attributes["consumption_quantity"] != item.attributes["assembly_quantity"]


def test_object_set_integrity():
    s = DrawingObjectSet(document_sha="h")
    o1 = bom_occurrence("o1", component_code="C", parent_code="P",
                        bom_level=0, bom_path="P",
                        consumption_quantity="1", consumption_unit="un")
    s.add_object(o1)
    with pytest.raises(ValueError):
        s.add_object(o1)  # duplicate id
    with pytest.raises(ValueError):
        s.add_relation(DrawingRelation(
            source_object_id="o1", target_object_id="ghost",
            relation_type=RelationType.REPRESENTED_BY))  # dangling ref


def test_relations_candidate_not_auto_verified():
    out = build_object_profiles(
        bom_occurrences=[{"occurrence_id": "o1", "component_code": "10210771",
                          "depth": 0, "path": "P", "quantity_raw": "500",
                          "unit_raw": "mm"}],
        visual_observations=[],
        component_rows=[{"item": "A1", "quantity": "1",
                         "component_code": "10210771",
                         "description": "VEDACAO", "region": "component_table"}],
        document_sha="h")
    assert out["contract_version"] == "drawing_object_profiles.v1"
    assert out["not_official"] is True
    rels = out["relations"]
    assert len(rels) == 1
    # igualdade de código NUNCA verifica — permanece candidato/pendente
    assert rels[0]["verification_state"] == "NOT_CHECKED"
    assert "code_match é candidato" in rels[0]["uncertainty_reason"]
    assert out["objects"][0]["official"] is True   # BOM = oficial
    assert out["objects"][1]["official"] is False  # table item = observado
