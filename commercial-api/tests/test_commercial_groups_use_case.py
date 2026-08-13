from unittest.mock import MagicMock

from commercial_app.application.use_cases.manage_commercial_groups import (
    CreateCommercialGroupRequest,
    ManageCommercialGroupsUseCase,
    group_summary_to_dict,
    group_to_dict,
)
from commercial_app.domain.entities.commercial_group import (
    CommercialGroup,
    CommercialGroupMember,
)


def _group(**kwargs) -> CommercialGroup:
    defaults = dict(
        id="g1",
        kind="sellers",
        name="Vendedores",
        active=True,
        sort_order=10,
        members=(CommercialGroupMember(user_id="u1"),),
    )
    defaults.update(kwargs)
    return CommercialGroup(**defaults)


def test_group_to_dict_shape() -> None:
    payload = group_to_dict(_group())
    assert payload["id"] == "g1"
    assert payload["kind"] == "sellers"
    assert payload["name"] == "Vendedores"
    assert payload["member_count"] == 1
    assert payload["members"] == [{"user_id": "u1"}]


def test_group_summary_omits_members() -> None:
    payload = group_summary_to_dict(_group())
    assert "members" not in payload
    assert payload["kind"] == "sellers"


def test_list_groups_delegates_to_repository() -> None:
    repository = MagicMock()
    repository.list_groups.return_value = [_group(), _group(id="g2", kind="billing")]
    use_case = ManageCommercialGroupsUseCase(repository)

    result = use_case.list_groups(active_only=True)

    assert len(result) == 2
    repository.list_groups.assert_called_once_with(active_only=True)


def test_get_group_raises_when_missing() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = None
    use_case = ManageCommercialGroupsUseCase(repository)

    try:
        use_case.get_group("missing")
        assert False, "expected LookupError"
    except LookupError as exc:
        assert "não encontrado" in str(exc)


def test_create_group_rejects_duplicate_kind() -> None:
    repository = MagicMock()
    repository.get_by_kind.return_value = _group()
    use_case = ManageCommercialGroupsUseCase(repository)

    try:
        use_case.create_group(
            CreateCommercialGroupRequest(kind="sellers", name="Outro")
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "sellers" in str(exc)
    repository.create_group.assert_not_called()


def test_create_group_success_and_audit() -> None:
    repository = MagicMock()
    repository.get_by_kind.return_value = None
    created = _group(id="g-new", kind="custom", name="Custom", members=())
    repository.create_group.return_value = created
    audit = MagicMock()
    use_case = ManageCommercialGroupsUseCase(repository, audit_repository=audit)

    result = use_case.create_group(
        CreateCommercialGroupRequest(
            kind="custom",
            name="Custom",
            sort_order=50,
            created_by_user_id="actor-1",
        )
    )

    assert result.id == "g-new"
    repository.create_group.assert_called_once_with(
        kind="custom",
        name="Custom",
        sort_order=50,
        active=True,
    )
    audit.append.assert_called_once()
    assert audit.append.call_args.kwargs["action"] == "commercial_group.create"


def test_add_member_requires_portal_access() -> None:
    repository = MagicMock()
    portal = MagicMock()
    portal.has_commercial_portal_access_batch.return_value = {"u2": False}
    use_case = ManageCommercialGroupsUseCase(repository, portal_access=portal)

    try:
        use_case.add_member(group_id="g1", user_id="u2")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Portal Comercial" in str(exc)
    repository.add_member.assert_not_called()


def test_add_member_success() -> None:
    repository = MagicMock()
    updated = _group(
        members=(
            CommercialGroupMember(user_id="u1"),
            CommercialGroupMember(user_id="u2"),
        )
    )
    repository.add_member.return_value = updated
    use_case = ManageCommercialGroupsUseCase(repository)

    result = use_case.add_member(group_id="g1", user_id="u2", actor_user_id="actor")

    assert result.member_count == 2
    repository.add_member.assert_called_once_with(group_id="g1", user_id="u2")


def test_replace_members_dedupes_and_audits() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = _group(members=())
    updated = _group(
        members=(
            CommercialGroupMember(user_id="a"),
            CommercialGroupMember(user_id="b"),
        )
    )
    repository.replace_members.return_value = updated
    audit = MagicMock()
    use_case = ManageCommercialGroupsUseCase(repository, audit_repository=audit)

    result = use_case.replace_members(
        group_id="g1",
        user_ids=["a", "a", "b", ""],
        actor_user_id="actor",
    )

    assert [m.user_id for m in result.members] == ["a", "b"]
    call = repository.replace_members.call_args
    assert call.kwargs["group_id"] == "g1"
    assert [m.user_id for m in call.kwargs["members"]] == ["a", "b"]
    assert audit.append.call_args.kwargs["action"] == "commercial_group.replace_members"


def test_remove_member_success() -> None:
    repository = MagicMock()
    repository.remove_member.return_value = _group(members=())
    use_case = ManageCommercialGroupsUseCase(repository)

    result = use_case.remove_member(group_id="g1", user_id="u1")

    assert result.member_count == 0
    repository.remove_member.assert_called_once_with(group_id="g1", user_id="u1")


def test_team_roster_hooks_delegate() -> None:
    repository = MagicMock()
    repository.list_member_user_ids_by_group_id.return_value = ["u1", "u2"]
    repository.list_groups_by_user_id.return_value = [_group(members=())]
    repository.list_memberships_by_user_ids.return_value = [
        ("u1", _group(members=())),
    ]
    use_case = ManageCommercialGroupsUseCase(repository)

    assert use_case.list_member_user_ids_by_group_id("g1") == ["u1", "u2"]
    assert len(use_case.list_groups_by_user_id("u1")) == 1
    assert use_case.list_memberships_by_user_ids(["u1"])[0][0] == "u1"
    repository.list_member_user_ids_by_group_id.assert_called_once_with("g1")
    repository.list_groups_by_user_id.assert_called_once_with("u1")
    repository.list_memberships_by_user_ids.assert_called_once_with(["u1"])
