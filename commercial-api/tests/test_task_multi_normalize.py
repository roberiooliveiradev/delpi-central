from commercial_app.domain.entities.task import (
    TaskCustomerRef,
    normalize_assignee_group_ids,
    normalize_assignee_user_ids,
    normalize_task_customers,
)


def test_normalize_assignee_user_ids_prefers_list_and_caps():
    ids = normalize_assignee_user_ids(
        assignee_user_ids=["a", "b", "a", ""] + [f"u{i}" for i in range(25)],
        assignee_user_id="ignored",
        fallback_user_id="caller",
        max_items=20,
    )
    assert ids[0] == "a"
    assert ids[1] == "b"
    assert len(ids) == 20
    assert len(set(ids)) == 20


def test_normalize_assignee_user_ids_singular_and_fallback():
    assert normalize_assignee_user_ids(
        assignee_user_ids=None,
        assignee_user_id="seller-a",
        fallback_user_id="caller",
    ) == ["seller-a"]
    assert normalize_assignee_user_ids(
        assignee_user_ids=None,
        assignee_user_id=None,
        fallback_user_id="caller",
    ) == ["caller"]


def test_normalize_task_customers_from_body_dicts_and_singular():
    items = normalize_task_customers(
        customers=[
            {"code": "0001", "store": "01", "name": "ACME"},
            {"customer_code": "0001", "customer_store": "01"},
            {"code": "0002", "store": "01"},
        ],
        customer_code=None,
        customer_store=None,
    )
    assert items == [
        TaskCustomerRef("0001", "01", "ACME"),
        TaskCustomerRef("0002", "01", None),
    ]
    singular = normalize_task_customers(
        customers=None,
        customer_code="0009",
        customer_store="02",
        customer_name="Beta",
    )
    assert singular == [TaskCustomerRef("0009", "02", "Beta")]


def test_normalize_assignee_group_ids_dedupes_and_caps():
    ids = normalize_assignee_group_ids(
        assignee_group_ids=["g1", "g1", "", "g2"] + [f"g{i}" for i in range(30)],
        max_items=20,
    )
    assert ids[0] == "g1"
    assert ids[1] == "g2"
    assert len(ids) == 20
    assert normalize_assignee_group_ids(assignee_group_ids=None) == []
