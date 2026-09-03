import pytest

from app.domain.services.audit_5s.audit_5s_area_hierarchy_service import (
    AGGREGATOR_NOT_AUDITABLE_MESSAGE,
    CHILD_IS_AGGREGATOR_MESSAGE,
    HIERARCHY_BRANCH_FORBIDDEN_MESSAGE,
    PARENT_HAS_AUDITS_MESSAGE,
    PARENT_IS_SUB_AREA_MESSAGE,
    Audit5sAreaHierarchyError,
    assert_area_auditable,
    eligible_child_candidates,
    enrich_area_hierarchy_fields,
    is_hierarchy_write_allowed,
    is_leaf,
    mean_of_means,
    require_hierarchy_write_branch,
    validate_set_children,
)


def test_hierarchy_write_only_branch_02():
    assert is_hierarchy_write_allowed("02") is True
    assert is_hierarchy_write_allowed("01") is False
    with pytest.raises(Audit5sAreaHierarchyError, match="filial 02"):
        require_hierarchy_write_branch("01")


def test_enrich_and_leaf_flags():
    leaf = enrich_area_hierarchy_fields(
        {"id": "a1", "branch_code": "02", "name": "A", "parent_area_id": None, "children_count": 0}
    )
    assert leaf["is_aggregator"] is False
    assert leaf["is_sub_area"] is False
    assert is_leaf(leaf) is True

    sub = enrich_area_hierarchy_fields(
        {"id": "a2", "branch_code": "02", "name": "B", "parent_area_id": "p1", "children_count": 0}
    )
    assert sub["is_sub_area"] is True
    assert is_leaf(sub) is True

    parent = enrich_area_hierarchy_fields(
        {"id": "p1", "branch_code": "02", "name": "P", "parent_area_id": None, "children_count": 2}
    )
    assert parent["is_aggregator"] is True
    assert is_leaf(parent) is False


def test_assert_area_auditable_rejects_aggregator():
    assert_area_auditable({"id": "a", "children_count": 0})
    with pytest.raises(Audit5sAreaHierarchyError, match=AGGREGATOR_NOT_AUDITABLE_MESSAGE):
        assert_area_auditable({"id": "p", "children_count": 3})


def test_validate_set_children_happy_path():
    parent = {"id": "p1", "branch_code": "02", "parent_area_id": None, "children_count": 0}
    children = [
        {"id": "c1", "branch_code": "02", "parent_area_id": None, "children_count": 0},
        {"id": "c2", "branch_code": "02", "parent_area_id": None, "children_count": 0},
    ]
    result = validate_set_children(
        parent=parent,
        children=children,
        child_ids=["c1", "c2", "c1"],
        parent_audit_count=0,
    )
    assert result == ["c1", "c2"]


def test_validate_set_children_rejects_branch_01_parent():
    parent = {"id": "p1", "branch_code": "01", "parent_area_id": None, "children_count": 0}
    with pytest.raises(Audit5sAreaHierarchyError, match=HIERARCHY_BRANCH_FORBIDDEN_MESSAGE):
        validate_set_children(
            parent=parent,
            children=[],
            child_ids=[],
            parent_audit_count=0,
        )


def test_validate_set_children_rejects_parent_with_audits():
    parent = {"id": "p1", "branch_code": "02", "parent_area_id": None, "children_count": 0}
    with pytest.raises(Audit5sAreaHierarchyError, match=PARENT_HAS_AUDITS_MESSAGE):
        validate_set_children(
            parent=parent,
            children=[],
            child_ids=[],
            parent_audit_count=1,
        )


def test_validate_set_children_rejects_sub_area_as_parent():
    parent = {"id": "p1", "branch_code": "02", "parent_area_id": "other", "children_count": 0}
    with pytest.raises(Audit5sAreaHierarchyError, match=PARENT_IS_SUB_AREA_MESSAGE):
        validate_set_children(
            parent=parent,
            children=[],
            child_ids=[],
            parent_audit_count=0,
        )


def test_validate_set_children_rejects_aggregator_as_child():
    parent = {"id": "p1", "branch_code": "02", "parent_area_id": None, "children_count": 0}
    children = [
        {"id": "c1", "branch_code": "02", "parent_area_id": None, "children_count": 2},
    ]
    with pytest.raises(Audit5sAreaHierarchyError, match=CHILD_IS_AGGREGATOR_MESSAGE):
        validate_set_children(
            parent=parent,
            children=children,
            child_ids=["c1"],
            parent_audit_count=0,
        )


def test_mean_of_means():
    assert mean_of_means([80.0, 60.0]) == 70.0
    assert mean_of_means([80.0, None, 60.0]) == 70.0
    assert mean_of_means([]) is None
    assert mean_of_means([None, None]) is None


def test_eligible_child_candidates_excludes_other_aggregators():
    areas = [
        {"id": "p1", "branch_code": "02", "parent_area_id": None, "children_count": 2},
        {"id": "c1", "branch_code": "02", "parent_area_id": "p1", "children_count": 0},
        {"id": "loose", "branch_code": "02", "parent_area_id": None, "children_count": 0},
        {"id": "p2", "branch_code": "02", "parent_area_id": None, "children_count": 1},
    ]
    eligible = eligible_child_candidates(areas, parent_id="p1")
    ids = {a["id"] for a in eligible}
    assert ids == {"c1", "loose"}
