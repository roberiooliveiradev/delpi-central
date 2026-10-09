"""G7 — documento BPMN nativo por processo: contrato do use case.

Provam: XOR dual-mode nas duas direções, concorrência otimista
(expected_version → 409), revisões explícitas append-only, restore com
proveniência e fronteira de segurança fail-closed.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.use_cases.manage_process_bpmn_document import (
    DualModeConflict,
    ProcessBpmnDocumentUseCases,
    UnsafeArtifact,
    VersionConflict,
)
from tm_app.application.use_cases.manage_process_bpmn_reference import (
    DualModeConflict as RefDualModeConflict,
    ProcessBpmnReferenceUseCases,
)
from tm_app.domain.entities.process_bpmn_document import (
    ProcessBpmnDocument,
    ProcessBpmnRevision,
)

PROCESSO = "33333333-3333-3333-3333-333333333333"
USER = SimpleNamespace(id="user-a", sub="user-a", is_superadmin=True, permissions=[])
NO_ACCESS = SimpleNamespace(
    id="user-b", sub="user-b", is_superadmin=False, permissions=[]
)

XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"/>'
)


class _Report:
    def __init__(self, issues=()):
        self.evaluated_stages = frozenset()
        self.not_evaluated_stages = frozenset()
        self.issues = issues


class FakeValidator:
    """Stub da fronteira — o pipeline real (XSD+regras) é testado no smoke."""

    def __init__(self, report=None) -> None:
        self.report = report or _Report()
        self.calls = 0

    def validate(self, artifact, evidence=None):
        self.calls += 1
        return self.report


class FakeDocRepo:
    def __init__(self) -> None:
        self.docs: dict[str, ProcessBpmnDocument] = {}
        self.revisions: list[ProcessBpmnRevision] = []
        self.exists = True

    def process_exists(self, processo_id: str) -> bool:
        return self.exists

    def get_active(self, processo_id: str):
        return self.docs.get(processo_id)

    def has_active(self, processo_id: str) -> bool:
        return processo_id in self.docs

    def create(self, *, processo_id, working_copy_xml, working_copy_sha256, actor_user_id):
        doc = ProcessBpmnDocument(
            id="doc-1",
            processo_id=processo_id,
            working_copy_xml=working_copy_xml,
            working_copy_sha256=working_copy_sha256,
            version=1,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.docs[processo_id] = doc
        return doc

    def update_working_copy(
        self, *, document_id, working_copy_xml, working_copy_sha256, expected_version, actor_user_id
    ):
        for pid, doc in self.docs.items():
            if doc.id == document_id:
                if doc.version != expected_version:
                    return None
                doc.working_copy_xml = working_copy_xml
                doc.working_copy_sha256 = working_copy_sha256
                doc.version += 1
                return doc
        return None

    def soft_delete(self, *, processo_id, actor_user_id):
        return self.docs.pop(processo_id, None)

    def list_revisions(self, document_id: str):
        return [r for r in self.revisions if r.document_id == document_id]

    def get_revision(self, document_id, revision_number, *, with_artifact=False):
        for r in self.revisions:
            if r.document_id == document_id and r.revision_number == revision_number:
                return r
        return None

    def get_latest_revision_number(self, document_id: str):
        nums = [r.revision_number for r in self.revisions if r.document_id == document_id]
        return max(nums) if nums else None

    def create_revision(self, **kw):
        n = (self.get_latest_revision_number(kw["document_id"]) or 0) + 1
        for doc in self.docs.values():
            if doc.id == kw["document_id"] and doc.version != kw["expected_version"]:
                return None
        rev = ProcessBpmnRevision(
            id=f"rev-{n}",
            document_id=kw["document_id"],
            revision_number=n,
            artifact_sha256=kw["artifact_sha256"],
            origin=kw["origin"],
            restored_from_revision_id=kw["restored_from_revision_id"],
            name=kw["name"],
            description=kw["description"],
            created_by_user_id=kw["actor_user_id"],
            created_by_name=kw["actor_name"],
            artifact_xml=kw["artifact_xml"],
        )
        self.revisions.append(rev)
        return rev

    def restore_revision(self, *, document_id, revision_number, expected_version, actor_user_id, actor_name):
        doc = next((d for d in self.docs.values() if d.id == document_id), None)
        if doc is None or doc.version != expected_version:
            return None
        src = self.get_revision(document_id, revision_number, with_artifact=True)
        if src is None:
            return None
        doc.working_copy_xml = src.artifact_xml
        doc.working_copy_sha256 = src.artifact_sha256
        doc.version += 1
        n = (self.get_latest_revision_number(document_id) or 0) + 1
        rev = ProcessBpmnRevision(
            id=f"rev-{n}",
            document_id=document_id,
            revision_number=n,
            artifact_sha256=src.artifact_sha256,
            origin="restore",
            restored_from_revision_id=src.id,
            name=None,
            description=None,
            created_by_user_id=actor_user_id,
            created_by_name=actor_name,
            source_revision_number=src.revision_number,
            artifact_xml=src.artifact_xml,
        )
        self.revisions.append(rev)
        return doc, rev


class FakeRefRepo:
    def __init__(self) -> None:
        self.active: dict[str, Any] = {}
        self.exists = True

    def process_exists(self, processo_id: str) -> bool:
        return self.exists

    def get_active(self, processo_id: str):
        return self.active.get(processo_id)


def _uc(docs=None, refs=None, validator=None) -> ProcessBpmnDocumentUseCases:
    return ProcessBpmnDocumentUseCases(
        docs or FakeDocRepo(),
        refs if refs is not None else FakeRefRepo(),
        validator=validator or FakeValidator(),
    )


def test_create_blank_document():
    uc = _uc()
    doc = uc.create_document(USER, PROCESSO, None)
    assert doc.version == 1
    assert "bpmn:definitions" in doc.working_copy_xml
    assert doc.working_copy_sha256


def test_create_import_validates_boundary():
    validator = FakeValidator()
    uc = _uc(validator=validator)
    doc = uc.create_document(USER, PROCESSO, XML)
    assert validator.calls == 1
    assert doc.working_copy_xml == XML


def test_xor_create_native_blocked_by_external():
    refs = FakeRefRepo()
    refs.active[PROCESSO] = object()
    uc = _uc(refs=refs)
    with pytest.raises(DualModeConflict):
        uc.create_document(USER, PROCESSO, None)


def test_xor_set_reference_blocked_by_native():
    docs = FakeDocRepo()
    docs.docs[PROCESSO] = SimpleNamespace(id="doc-1")
    refs = FakeRefRepo()
    uc = ProcessBpmnReferenceUseCases(refs, SimpleNamespace(), docs=docs)
    with pytest.raises(RefDualModeConflict):
        uc.set_reference(
            USER,
            PROCESSO,
            model_id="aaaaaaaa-1111-1111-1111-111111111111",
            revision_number=1,
            authorization="Bearer x",
        )


def test_save_stale_version_conflict():
    uc = _uc()
    doc = uc.create_document(USER, PROCESSO, None)
    with pytest.raises(VersionConflict):
        uc.save_working_copy(USER, PROCESSO, xml=XML, expected_version=99)
    assert doc.version == 1


def test_save_then_revision_then_restore():
    uc = _uc()
    doc = uc.create_document(USER, PROCESSO, None)
    updated = uc.save_working_copy(
        USER, PROCESSO, xml=XML, expected_version=doc.version
    )
    assert updated.version == 2

    rev = uc.create_revision(
        USER, PROCESSO, expected_version=2, name="r1", description=None
    )
    assert rev.revision_number == 1
    assert rev.origin == "explicit"

    doc2, rev2 = uc.restore_revision(
        USER, PROCESSO, 1, expected_version=2
    )
    assert rev2.origin == "restore"
    assert rev2.source_revision_number == 1
    assert doc2.version == 3


def test_autosave_never_creates_revision():
    """Invariante ADR-006: save do working copy não gera revisão implícita."""
    docs = FakeDocRepo()
    uc = _uc(docs=docs)
    doc = uc.create_document(USER, PROCESSO, None)
    uc.save_working_copy(USER, PROCESSO, xml=XML, expected_version=doc.version)
    assert docs.list_revisions(doc.id) == []


def test_delete_soft():
    uc = _uc()
    uc.create_document(USER, PROCESSO, None)
    result = uc.delete_document(USER, PROCESSO)
    assert result["deleted"] is True
    with pytest.raises(LookupError):
        uc.get_document(USER, PROCESSO)


def test_access_denied():
    uc = _uc()
    with pytest.raises(AuthorizationDenied):
        uc.get_document(NO_ACCESS, PROCESSO)
    with pytest.raises(AuthorizationDenied):
        uc.create_document(NO_ACCESS, PROCESSO, None)


def test_missing_document_404():
    uc = _uc()
    with pytest.raises(LookupError):
        uc.get_working_copy(USER, PROCESSO)
