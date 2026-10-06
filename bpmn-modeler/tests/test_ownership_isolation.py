"""Resource authorization isolation — Model.created_by as V1 owner.

Contract: required RBAC permission AND caller.subject == model.created_by.
Foreign ids are indistinguishable from missing ones (MODEL_NOT_FOUND),
no existence/owner disclosure. Superadmin capabilities never imply
cross-owner access; Revision ownership derives from the parent Model.
"""
from __future__ import annotations

import pytest

from bpmn_modeler.application.errors import MODEL_NOT_FOUND, ApplicationError
from bpmn_modeler.application.use_cases import CallerIdentity

from .conftest import ALL_PERMISSIONS, clean_input

ALICE = CallerIdentity(
    subject="alice", permissions=ALL_PERMISSIONS, display_name="Alice"
)
BOB = CallerIdentity(
    subject="bob", permissions=ALL_PERMISSIONS, display_name="Bob"
)
# superadmin recebe todas as capabilities via current_caller, mas o
# subject continua próprio — ownership não é bypassed pelo RBAC.
SUPERADMIN = CallerIdentity(
    subject="admin-1", permissions=ALL_PERMISSIONS, display_name="Root"
)

XML_ALT = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" '
    'id="d1" targetNamespace="urn:x" name="alt"/>'
)


def _not_found(fn, *args, **kwargs):
    with pytest.raises(ApplicationError) as exc:
        fn(*args, **kwargs)
    assert exc.value.code == MODEL_NOT_FOUND
    return exc.value


@pytest.fixture()
def alice_model(service):
    return service.create_model("Alice Model", ALICE).model_id


# --------------------------------------------------------------------- #
# LIST isolation (query, archive, pagination, ordering, has_more)        #
# --------------------------------------------------------------------- #


def test_list_models_is_owner_scoped(service):
    a1 = service.create_model("Alice One", ALICE).model_id
    a2 = service.create_model("Alice Two", ALICE).model_id
    b1 = service.create_model("Bob One", BOB).model_id

    alice = service.list_models(
        query=None, archived="active", sort="updated_at",
        direction="desc", page=1, page_size=25, caller=ALICE,
    )
    bob = service.list_models(
        query=None, archived="active", sort="updated_at",
        direction="desc", page=1, page_size=25, caller=BOB,
    )

    assert {m.id for m in alice.items} == {a1, a2}
    assert {m.id for m in bob.items} == {b1}


def test_list_owner_scope_applies_before_pagination(service):
    # Bob models intercalados por updated_at não ocupam página de Alice
    service.create_model("Bob Gap 1", BOB)
    for i in range(3):
        service.create_model(f"Alice {i}", ALICE)
    service.create_model("Bob Gap 2", BOB)

    page1 = service.list_models(
        query=None, archived="active", sort="updated_at",
        direction="desc", page=1, page_size=2, caller=ALICE,
    )
    page2 = service.list_models(
        query=None, archived="active", sort="updated_at",
        direction="desc", page=2, page_size=2, caller=ALICE,
    )
    assert len(page1.items) == 2
    assert page1.has_more is True
    assert len(page2.items) == 1
    assert page2.has_more is False
    seen = {m.id for m in page1.items} | {m.id for m in page2.items}
    assert len(seen) == 3


def test_list_owner_scope_combines_with_search_and_archive(service):
    keep = service.create_model("Relatório Alice", ALICE).model_id
    service.create_model("Relatório Bob", BOB)
    archived = service.create_model("Alice Archived", ALICE).model_id
    service.archive_model(archived, 1, ALICE)

    hits = service.list_models(
        query="Relatório", archived="active", sort="display_name",
        direction="asc", page=1, page_size=25, caller=ALICE,
    )
    assert [m.id for m in hits.items] == [keep]

    arch = service.list_models(
        query=None, archived="archived", sort="updated_at",
        direction="desc", page=1, page_size=25, caller=ALICE,
    )
    assert [m.id for m in arch.items] == [archived]


# --------------------------------------------------------------------- #
# DIRECT READS — foreign id ≡ MODEL_NOT_FOUND                            #
# --------------------------------------------------------------------- #


def test_foreign_reads_are_not_found(service, alice_model):
    _not_found(service.get_model, alice_model, BOB)
    _not_found(service.get_working_copy, alice_model, BOB)
    _not_found(service.export_working_copy, alice_model, BOB)
    _not_found(service.list_revisions, alice_model, 1, 25, BOB)
    _not_found(
        service.validate_working_copy, alice_model, clean_input(XML_ALT), BOB
    )


def test_foreign_revision_paths_are_not_found(service, alice_model):
    service.save_working_copy(
        alice_model, clean_input(XML_ALT), 1, ALICE
    )
    service.create_revision(alice_model, 2, ALICE, name="R1")

    _not_found(service.get_revision, alice_model, 1, BOB)
    _not_found(service.export_revision, alice_model, 1, BOB)


def test_nonexistent_and_foreign_indistinguishable(service, alice_model):
    import uuid

    foreign = _not_found(service.get_model, alice_model, BOB)
    missing = _not_found(service.get_model, str(uuid.uuid4()), BOB)
    assert foreign.code == missing.code == MODEL_NOT_FOUND
    assert foreign.message == missing.message


# --------------------------------------------------------------------- #
# WRITES — global permissions never authorize foreign mutation           #
# --------------------------------------------------------------------- #


def test_foreign_writes_are_denied_and_leave_resource_unchanged(
    service, alice_model
):
    before = service.get_model(alice_model, ALICE)

    _not_found(
        service.save_working_copy,
        alice_model, clean_input(XML_ALT), before.version, BOB,
    )
    _not_found(
        service.rename_model,
        alice_model, "Bob Rename", before.version, BOB,
    )
    _not_found(
        service.duplicate_model, alice_model, "Bob Copy", BOB,
    )
    _not_found(
        service.archive_model, alice_model, before.version, BOB,
    )
    _not_found(
        service.unarchive_model, alice_model, before.version, BOB,
    )
    _not_found(
        service.create_revision, alice_model, before.version, BOB,
    )
    _not_found(
        service.restore_revision, alice_model, 1, before.version, BOB,
    )

    after = service.get_model(alice_model, ALICE)
    assert after.version == before.version
    assert after.display_name == before.display_name
    assert after.archived_at == before.archived_at
    assert (
        after.working_copy.artifact.content
        == before.working_copy.artifact.content
    )
    assert len(after.revisions) == len(before.revisions)


# --------------------------------------------------------------------- #
# SUPERADMIN — capabilities globais não implicam cross-owner             #
# --------------------------------------------------------------------- #


def test_superadmin_has_no_cross_owner_access(service, alice_model):
    # capabilities globais completas — mesmas que current_caller injeta
    # para is_superadmin — mas subject próprio: ownership ainda decide.
    _not_found(service.get_model, alice_model, SUPERADMIN)
    _not_found(
        service.save_working_copy,
        alice_model, clean_input(XML_ALT), 1, SUPERADMIN,
    )
    _not_found(
        service.rename_model, alice_model, "Admin Rename", 1, SUPERADMIN,
    )
    listed = service.list_models(
        query=None, archived="all", sort="updated_at",
        direction="desc", page=1, page_size=100, caller=SUPERADMIN,
    )
    assert not any(m.id == alice_model for m in listed.items)


# --------------------------------------------------------------------- #
# REVISION ownership deriva do Model pai                                  #
# --------------------------------------------------------------------- #


def test_revision_ownership_derives_from_model(service, alice_model):
    service.save_working_copy(alice_model, clean_input(XML_ALT), 1, ALICE)
    service.create_revision(alice_model, 2, ALICE, name="R1")

    # revision.created_by é audit metadata — autorização vem do Model
    revision = service.get_revision(alice_model, 1, ALICE)
    assert revision.created_by == "alice"

    # um caller cujo subject coincida com revision.created_by mas não
    # com model.created_by não ganha acesso (cenário: model_id foreign)
    foreign = CallerIdentity(
        subject="alice-other", permissions=ALL_PERMISSIONS
    )
    _not_found(service.get_revision, alice_model, 1, foreign)
    _not_found(service.restore_revision, alice_model, 1, 3, foreign)


# --------------------------------------------------------------------- #
# HAPPY PATH — owner mantém jornada completa                              #
# --------------------------------------------------------------------- #


def test_owner_full_journey(service):
    mid = service.create_model("Journey", ALICE).model_id
    service.save_working_copy(mid, clean_input(XML_ALT), 1, ALICE)
    service.rename_model(mid, "Journey Renamed", 2, ALICE)
    service.create_revision(mid, 3, ALICE, name="R1")
    service.save_working_copy(
        mid, clean_input(XML_ALT.replace("alt", "alt2")), 4, ALICE
    )
    service.create_revision(mid, 5, ALICE, name="R2")
    service.restore_revision(mid, 1, 6, ALICE)
    service.archive_model(mid, 7, ALICE)
    service.unarchive_model(mid, 8, ALICE)
    copy_outcome = service.duplicate_model(mid, "Journey Copy", ALICE)
    assert copy_outcome.changed
    assert service.get_model(mid, ALICE).version == 9
    assert service.get_working_copy(mid, ALICE).version == 9
    assert service.export_working_copy(mid, ALICE)
    assert len(service.list_revisions(mid, 1, 25, ALICE).items) == 3
    report = service.validate_working_copy(mid, clean_input(XML_ALT), ALICE)
    assert report is not None
