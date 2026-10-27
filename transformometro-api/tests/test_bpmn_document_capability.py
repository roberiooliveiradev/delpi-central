"""Governed native BPMN 2.0 authoring via TÉO — capability contract.

Prova o pipeline PREPARE → EXECUTE → VERIFY sobre o use case canônico
(ProcessBpmnDocumentUseCases — o mesmo do editor do Portal), incluindo
XOR dual-mode, concorrência otimista (expected_version), validação de
fronteira fail-closed e a regressão de que entidades flowchart_v1
continuam read-only e intocadas.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.governed_writes import (
    bpmn_document_capability as cap,
)
from tm_app.application.governed_writes.bpmn_document_capability import (
    BPMN_DOCUMENT_CAPABILITIES,
    CREATE_BPMN_DOCUMENT_CAPABILITY,
    CREATE_BPMN_REVISION_CAPABILITY,
    SAVE_BPMN_WORKING_COPY_CAPABILITY,
    BpmnDocumentWriteStack,
)
from tm_app.application.governed_writes.errors import GovernedWriteError
from tm_app.application.use_cases.manage_process_bpmn_document import (
    ProcessBpmnDocumentUseCases,
)
from tm_app.domain.entities.process_bpmn_document import (
    ProcessBpmnDocument,
    ProcessBpmnRevision,
)

PROCESSO = "33333333-3333-3333-3333-333333333333"
DOC_ID = "44444444-4444-4444-4444-444444444444"
USER = SimpleNamespace(
    id="user-a", sub="user-a", is_superadmin=True, permissions=[]
)

XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"/>'
)
XML_V2 = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">'
    '<bpmn:process id="p1"/></bpmn:definitions>'
)


class _Report:
    def __init__(self, issues=()):
        self.evaluated_stages = frozenset()
        self.not_evaluated_stages = frozenset()
        self.issues = issues


class FakeValidator:
    """Boundary stub — o pipeline real (XSD+regras) é coberto no G7."""

    def __init__(self, report=None) -> None:
        self.report = report or _Report()
        self.calls = 0

    def validate(self, artifact, evidence=None):
        self.calls += 1
        return self.report


class FakeDocs:
    def __init__(self, active: ProcessBpmnDocument | None = None):
        self.docs: dict[str, ProcessBpmnDocument] = {}
        if active is not None:
            self.docs[active.processo_id] = active
        self.revisions: list[ProcessBpmnRevision] = []
        self.exists = True

    def process_exists(self, processo_id: str) -> bool:
        return self.exists

    def get_active(self, processo_id: str):
        return self.docs.get(processo_id)

    def has_active(self, processo_id: str) -> bool:
        return processo_id in self.docs

    def create(
        self, *, processo_id, working_copy_xml, working_copy_sha256, actor_user_id
    ):
        doc = ProcessBpmnDocument(
            id=DOC_ID,
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
        self,
        *,
        document_id,
        working_copy_xml,
        working_copy_sha256,
        expected_version,
        actor_user_id,
    ):
        for doc in self.docs.values():
            if doc.id == document_id:
                if doc.version != expected_version:
                    return None
                doc.working_copy_xml = working_copy_xml
                doc.working_copy_sha256 = working_copy_sha256
                doc.version += 1
                return doc
        return None

    def list_revisions(self, document_id: str):
        return [r for r in self.revisions if r.document_id == document_id]

    def get_latest_revision_number(self, document_id: str):
        nums = [
            r.revision_number
            for r in self.revisions
            if r.document_id == document_id
        ]
        return max(nums) if nums else None

    def create_revision(self, **kw):
        n = (self.get_latest_revision_number(kw["document_id"]) or 0) + 1
        for doc in self.docs.values():
            if doc.id == kw["document_id"] and doc.version != kw[
                "expected_version"
            ]:
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

    def soft_delete(self, *, processo_id, actor_user_id):
        return self.docs.pop(processo_id, None)


class FakeRefs:
    def __init__(self, active=None):
        self._active = active

    def get_active(self, pid):
        return self._active


def _doc(xml: str = XML, version: int = 1) -> ProcessBpmnDocument:
    import hashlib

    return ProcessBpmnDocument(
        id=DOC_ID,
        processo_id=PROCESSO,
        working_copy_xml=xml,
        working_copy_sha256=hashlib.sha256(xml.encode()).hexdigest(),
        version=version,
        created_by_user_id="u",
        updated_by_user_id="u",
    )


def _stack(
    docs: FakeDocs | None = None,
    refs: FakeRefs | None = None,
    validator: FakeValidator | None = None,
) -> BpmnDocumentWriteStack:
    docs = docs or FakeDocs()
    refs = refs or FakeRefs()
    return BpmnDocumentWriteStack(
        use_case=ProcessBpmnDocumentUseCases(
            docs, refs, validator=validator or FakeValidator()
        ),
        docs=docs,
        refs=refs,
    )


def _request(user=USER):
    req = MagicMock()
    req.state.user = user
    return req


def _prepare(stack, request, args, *, capability, validator=None):
    """PREPARE com authz e boundary stubados (mesmo padrão do test G8)."""
    with (
        patch.object(cap, "check_processo_manage_access", return_value=None),
        patch.object(
            cap,
            "LxmlBpmnValidator",
            return_value=validator or FakeValidator(),
        ),
    ):
        return cap.prepare(stack, request, args, capability=capability)


# ---------------------------------------------------------------------
# Registry / discovery contract
# ---------------------------------------------------------------------


class TestRegistry:
    def test_actions_map_to_capabilities(self):
        from tm_app.application.governed_writes.orchestrator import (
            GOVERNED_OPERATION_ACTION_TO_CAPABILITY,
            WRITE_CAPABILITIES,
        )

        for action in BPMN_DOCUMENT_CAPABILITIES:
            assert GOVERNED_OPERATION_ACTION_TO_CAPABILITY[action] == action
            assert action in WRITE_CAPABILITIES

    def test_execution_policies(self):
        from tm_app.application.governed_writes.confirmation_policy import (
            AUTO_ACT,
            CONFIRM_BEFORE_ACT,
            confirmation_kind_for_workflow,
            execution_policy_for_capability,
        )

        # Create = transição de autoridade → confirm; update/append → auto.
        assert (
            confirmation_kind_for_workflow("create_bpmn_document")
            == CONFIRM_BEFORE_ACT
        )
        assert (
            execution_policy_for_capability("create_bpmn_document")
            == CONFIRM_BEFORE_ACT
        )
        assert (
            execution_policy_for_capability("save_bpmn_working_copy")
            == AUTO_ACT
        )
        assert (
            execution_policy_for_capability("create_bpmn_revision") == AUTO_ACT
        )

    def test_capability_descriptors_registered(self):
        from tm_app.application.gpt_actions.capability_descriptors import (
            build_capability_surface_catalog,
        )

        catalog = build_capability_surface_catalog()
        ids = {w.get("id") for w in catalog["workflows"]}
        assert {
            "create_bpmn_document",
            "save_bpmn_working_copy",
            "create_bpmn_revision",
        } <= ids
        mcp = build_capability_surface_catalog("mcp")
        mcp_ids = {w.get("id") for w in mcp["workflows"]}
        assert {
            "create_bpmn_document",
            "save_bpmn_working_copy",
            "create_bpmn_revision",
        } <= mcp_ids

    def test_entity_schema_documents_governed_contract(self):
        from tm_app.application.gpt_actions.registration_guide import (
            build_registration_guide,
        )

        guide = build_registration_guide()
        schema = guide["entity_schemas"]["process_bpmn_document"]
        notes = " ".join(schema["notes"])
        assert "create_bpmn_document" in notes
        assert "save_bpmn_working_copy" in notes
        assert "create_bpmn_revision" in notes
        assert "expected_version" in notes
        # Legacy entities remain strictly read-only.
        for legacy in (
            "process_diagram",
            "instance_diagram_scope",
            "revision_diagram_overlay",
        ):
            assert guide["entity_schemas"][legacy].get("read_only") is True

    def test_entity_remains_get_only_for_record_ops(self):
        from tm_app.application.gpt_actions.entities import (
            GptEntity,
            entity_supports,
        )

        entity = GptEntity.PROCESS_BPMN_DOCUMENT
        assert entity_supports(entity, "get")
        assert not entity_supports(entity, "create")
        assert not entity_supports(entity, "update")
        assert not entity_supports(entity, "delete")


# ---------------------------------------------------------------------
# PREPARE — create_bpmn_document
# ---------------------------------------------------------------------


class TestPrepareCreate:
    def test_blank_ready_seals_none_xml(self):
        stack = _stack()
        out = _prepare(
            stack,
            _request(),
            {"processo_id": PROCESSO},
            capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
        )
        assert out["validation_result"]["ready"] is True
        assert out["exact_change"]["candidate_xml"] is None
        assert out["exact_change"]["candidate_sha256"] is None
        assert out["consequential_impact"]["mutates_legacy"] is False
        assert out["consequential_impact"]["writes_to_bpmn_modeler"] is False
        assert stack.docs.get_active(PROCESSO) is None

    def test_with_xml_seals_sha256(self):
        stack = _stack()
        out = _prepare(
            stack,
            _request(),
            {"processo_id": PROCESSO, "xml": XML},
            capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
        )
        assert out["validation_result"]["ready"] is True
        assert out["exact_change"]["candidate_xml"] == XML
        assert len(out["exact_change"]["candidate_sha256"]) == 64
        assert stack.docs.get_active(PROCESSO) is None

    def test_invalid_xml_ready_false_never_persists(self):
        stack = _stack()
        out = _prepare(
            stack,
            _request(),
            {"processo_id": PROCESSO, "xml": "not xml at all"},
            capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
        )
        assert out["validation_result"]["ready"] is False
        assert stack.docs.get_active(PROCESSO) is None

    def test_validation_errors_ready_false(self):
        issue = SimpleNamespace(
            rule_id="BPMN_SCHEMA",
            source=SimpleNamespace(value="schema"),
            stage=SimpleNamespace(value="schema"),
            severity=SimpleNamespace(value="error"),
            message="Elemento BPMN não suportado.",
            reference=None,
        )
        stack = _stack()
        out = _prepare(
            stack,
            _request(),
            {"processo_id": PROCESSO, "xml": XML},
            capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
            validator=FakeValidator(_Report(issues=[issue])),
        )
        assert out["validation_result"]["ready"] is False
        assert out["validation_result"]["bpmn_validation"]["passed"] is False

    def test_native_exists_409(self):
        stack = _stack(docs=FakeDocs(active=_doc()))
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {"processo_id": PROCESSO},
                capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
            )
        assert exc.value.status_code == 409
        assert "NATIVE_BPMN_ALREADY_EXISTS" in str(exc.value.code)

    def test_external_reference_409(self):
        stack = _stack(refs=FakeRefs(active=SimpleNamespace(id="ref")))
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {"processo_id": PROCESSO},
                capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
            )
        assert exc.value.status_code == 409
        assert "dual_mode" in str(exc.value.code)

    def test_missing_processo_id_400(self):
        stack = _stack()
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {},
                capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
            )
        assert exc.value.status_code == 400

    def test_processo_not_found_404(self):
        docs = FakeDocs()
        docs.exists = False
        stack = _stack(docs=docs)
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {"processo_id": PROCESSO},
                capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
            )
        assert exc.value.status_code == 404

    def test_denied_authz_propagates(self):
        stack = _stack()
        denied = SimpleNamespace(status_code=403)
        with patch.object(
            cap, "check_processo_manage_access", return_value=denied
        ):
            with pytest.raises(GovernedWriteError) as exc:
                cap.prepare(
                    stack,
                    _request(),
                    {"processo_id": PROCESSO},
                    capability=CREATE_BPMN_DOCUMENT_CAPABILITY,
                )
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------
# PREPARE — save_bpmn_working_copy
# ---------------------------------------------------------------------


class TestPrepareSave:
    def test_ready_seals_xml_and_version(self):
        stack = _stack(docs=FakeDocs(active=_doc()))
        out = _prepare(
            stack,
            _request(),
            {
                "processo_id": PROCESSO,
                "xml": XML_V2,
                "expected_version": 1,
            },
            capability=SAVE_BPMN_WORKING_COPY_CAPABILITY,
        )
        assert out["validation_result"]["ready"] is True
        change = out["exact_change"]
        assert change["expected_version"] == 1
        assert change["candidate_xml"] == XML_V2
        assert len(change["candidate_sha256"]) == 64
        # PREPARE nunca persiste
        assert stack.docs.get_active(PROCESSO).version == 1
        assert stack.docs.get_active(PROCESSO).working_copy_xml == XML

    def test_stale_version_409(self):
        stack = _stack(docs=FakeDocs(active=_doc()))
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {
                    "processo_id": PROCESSO,
                    "xml": XML_V2,
                    "expected_version": 7,
                },
                capability=SAVE_BPMN_WORKING_COPY_CAPABILITY,
            )
        assert exc.value.status_code == 409
        assert "VERSION_CONFLICT" in str(exc.value.code)

    def test_no_document_404(self):
        stack = _stack()
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {
                    "processo_id": PROCESSO,
                    "xml": XML_V2,
                    "expected_version": 1,
                },
                capability=SAVE_BPMN_WORKING_COPY_CAPABILITY,
            )
        assert exc.value.status_code == 404

    def test_missing_xml_400(self):
        stack = _stack(docs=FakeDocs(active=_doc()))
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {"processo_id": PROCESSO, "expected_version": 1},
                capability=SAVE_BPMN_WORKING_COPY_CAPABILITY,
            )
        assert exc.value.status_code == 400

    def test_missing_expected_version_400(self):
        stack = _stack(docs=FakeDocs(active=_doc()))
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {"processo_id": PROCESSO, "xml": XML_V2},
                capability=SAVE_BPMN_WORKING_COPY_CAPABILITY,
            )
        assert exc.value.status_code == 400

    def test_invalid_xml_ready_false(self):
        stack = _stack(docs=FakeDocs(active=_doc()))
        out = _prepare(
            stack,
            _request(),
            {
                "processo_id": PROCESSO,
                "xml": "not xml at all",
                "expected_version": 1,
            },
            capability=SAVE_BPMN_WORKING_COPY_CAPABILITY,
        )
        assert out["validation_result"]["ready"] is False
        assert stack.docs.get_active(PROCESSO).working_copy_xml == XML


# ---------------------------------------------------------------------
# PREPARE — create_bpmn_revision
# ---------------------------------------------------------------------


class TestPrepareRevision:
    def test_ready_seals_checkpoint(self):
        doc = _doc()
        stack = _stack(docs=FakeDocs(active=doc))
        out = _prepare(
            stack,
            _request(),
            {
                "processo_id": PROCESSO,
                "expected_version": 1,
                "name": "R1 AS-IS",
                "description": "checkpoint",
            },
            capability=CREATE_BPMN_REVISION_CAPABILITY,
        )
        assert out["validation_result"]["ready"] is True
        change = out["exact_change"]
        assert change["name"] == "R1 AS-IS"
        assert change["artifact_sha256"] == doc.working_copy_sha256
        assert out["consequential_impact"]["revision_origin"] == "explicit"
        assert stack.docs.revisions == []

    def test_stale_version_409(self):
        stack = _stack(docs=FakeDocs(active=_doc(version=3)))
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {"processo_id": PROCESSO, "expected_version": 1},
                capability=CREATE_BPMN_REVISION_CAPABILITY,
            )
        assert exc.value.status_code == 409

    def test_no_document_404(self):
        stack = _stack()
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {"processo_id": PROCESSO, "expected_version": 1},
                capability=CREATE_BPMN_REVISION_CAPABILITY,
            )
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------
# Fingerprint — stale proposal detection
# ---------------------------------------------------------------------


class TestFingerprint:
    def test_recompute_matches_prepare(self):
        stack = _stack(docs=FakeDocs(active=_doc()))
        out = _prepare(
            stack,
            _request(),
            {
                "processo_id": PROCESSO,
                "xml": XML_V2,
                "expected_version": 1,
            },
            capability=SAVE_BPMN_WORKING_COPY_CAPABILITY,
        )
        sealed = out["exact_change"]
        assert cap.recompute_fingerprint(stack, sealed) == out[
            "current_state_fingerprint"
        ]

    def test_fingerprint_changes_after_save(self):
        docs = FakeDocs(active=_doc())
        stack = _stack(docs=docs)
        fp1 = _prepare(
            stack,
            _request(),
            {
                "processo_id": PROCESSO,
                "xml": XML_V2,
                "expected_version": 1,
            },
            capability=SAVE_BPMN_WORKING_COPY_CAPABILITY,
        )["current_state_fingerprint"]
        # Simula save concorrente: working copy muda → fingerprint muda.
        docs.update_working_copy(
            document_id=DOC_ID,
            working_copy_xml=XML_V2,
            working_copy_sha256="other",
            expected_version=1,
            actor_user_id="u",
        )
        assert cap.recompute_fingerprint(
            stack, {"processo_id": PROCESSO}
        ) != fp1


# ---------------------------------------------------------------------
# EXECUTE — canonical write via the use case
# ---------------------------------------------------------------------


class TestExecute:
    def _denied(self):
        return SimpleNamespace(status_code=403)

    def test_create_commits_via_use_case(self):
        docs = FakeDocs()
        stack = _stack(docs=docs)
        change = {
            "capability": CREATE_BPMN_DOCUMENT_CAPABILITY,
            "processo_id": PROCESSO,
            "candidate_xml": XML,
            "candidate_sha256": "x",
        }
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ) as authz:
            result = cap.execute(stack, _request(), change)
        authz.assert_called_once()
        doc = docs.get_active(PROCESSO)
        assert doc is not None
        assert doc.working_copy_xml == XML
        assert result["document"]["document_id"] == DOC_ID

    def test_create_native_appeared_conflict_409(self):
        docs = FakeDocs(active=_doc())
        stack = _stack(docs=docs)
        change = {
            "capability": CREATE_BPMN_DOCUMENT_CAPABILITY,
            "processo_id": PROCESSO,
            "candidate_xml": XML,
        }
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ):
            with pytest.raises(GovernedWriteError) as exc:
                cap.execute(stack, _request(), change)
        assert exc.value.status_code == 409

    def test_create_denied_authz_propagates(self):
        docs = FakeDocs()
        stack = _stack(docs=docs)
        change = {
            "capability": CREATE_BPMN_DOCUMENT_CAPABILITY,
            "processo_id": PROCESSO,
            "candidate_xml": XML,
        }
        with patch.object(
            cap,
            "check_processo_manage_access",
            return_value=self._denied(),
        ):
            with pytest.raises(GovernedWriteError) as exc:
                cap.execute(stack, _request(), change)
        assert exc.value.status_code == 403
        assert docs.get_active(PROCESSO) is None

    def test_save_bumps_version(self):
        docs = FakeDocs(active=_doc())
        stack = _stack(docs=docs)
        change = {
            "capability": SAVE_BPMN_WORKING_COPY_CAPABILITY,
            "processo_id": PROCESSO,
            "expected_version": 1,
            "candidate_xml": XML_V2,
        }
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ):
            result = cap.execute(stack, _request(), change)
        doc = docs.get_active(PROCESSO)
        assert doc.version == 2
        assert doc.working_copy_xml == XML_V2
        assert result["document"]["version"] == 2

    def test_save_stale_version_409(self):
        docs = FakeDocs(active=_doc(version=2))
        stack = _stack(docs=docs)
        change = {
            "capability": SAVE_BPMN_WORKING_COPY_CAPABILITY,
            "processo_id": PROCESSO,
            "expected_version": 1,
            "candidate_xml": XML_V2,
        }
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ):
            with pytest.raises(GovernedWriteError) as exc:
                cap.execute(stack, _request(), change)
        assert exc.value.status_code == 409

    def test_revision_creates_checkpoint(self):
        docs = FakeDocs(active=_doc())
        stack = _stack(docs=docs)
        change = {
            "capability": CREATE_BPMN_REVISION_CAPABILITY,
            "processo_id": PROCESSO,
            "expected_version": 1,
            "name": "R1",
            "description": None,
            "artifact_sha256": docs.get_active(PROCESSO).working_copy_sha256,
        }
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ):
            result = cap.execute(stack, _request(), change)
        assert len(docs.revisions) == 1
        assert docs.revisions[0].origin == "explicit"
        assert result["revision"]["revision_number"] == 1


# ---------------------------------------------------------------------
# VERIFY — authoritative read-back
# ---------------------------------------------------------------------


class TestVerify:
    def _exec(self, docs, change):
        stack = _stack(docs=docs)
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ):
            result = cap.execute(stack, _request(), change)
        return stack, result

    def test_create_readback_verified(self):
        import hashlib

        docs = FakeDocs()
        change = {
            "capability": CREATE_BPMN_DOCUMENT_CAPABILITY,
            "processo_id": PROCESSO,
            "candidate_xml": XML,
            "candidate_sha256": hashlib.sha256(XML.encode()).hexdigest(),
        }
        stack, result = self._exec(docs, change)
        out = cap.verify(stack, change, result)
        assert out["verified"] is True
        assert out["document_id"] == DOC_ID
        assert out["working_copy_sha256"] == change["candidate_sha256"]

    def test_save_readback_checksum_mismatch_fails(self):
        docs = FakeDocs(active=_doc())
        stack, _ = self._exec(
            docs,
            {
                "capability": SAVE_BPMN_WORKING_COPY_CAPABILITY,
                "processo_id": PROCESSO,
                "expected_version": 1,
                "candidate_xml": XML_V2,
            },
        )
        bad_change = {
            "capability": SAVE_BPMN_WORKING_COPY_CAPABILITY,
            "processo_id": PROCESSO,
            "candidate_sha256": "0" * 64,
        }
        with pytest.raises(GovernedWriteError) as exc:
            cap.verify(stack, bad_change, {})
        assert "outcome_verification_failed" in str(exc.value.code)

    def test_verify_absent_document_fails(self):
        stack = _stack()
        with pytest.raises(GovernedWriteError) as exc:
            cap.verify(
                stack,
                {
                    "capability": CREATE_BPMN_DOCUMENT_CAPABILITY,
                    "processo_id": PROCESSO,
                },
                {},
            )
        assert "outcome_verification_failed" in str(exc.value.code)

    def test_revision_readback_verified(self):
        docs = FakeDocs(active=_doc())
        stack, result = self._exec(
            docs,
            {
                "capability": CREATE_BPMN_REVISION_CAPABILITY,
                "processo_id": PROCESSO,
                "expected_version": 1,
                "name": "R1",
                "description": None,
                "artifact_sha256": docs.get_active(
                    PROCESSO
                ).working_copy_sha256,
            },
        )
        change = {
            "capability": CREATE_BPMN_REVISION_CAPABILITY,
            "processo_id": PROCESSO,
            "artifact_sha256": docs.get_active(
                PROCESSO
            ).working_copy_sha256,
        }
        out = cap.verify(stack, change, result)
        assert out["verified"] is True
        assert out["revision"]["revision_number"] == 1


# ---------------------------------------------------------------------
# Legacy write regression — nothing here can reach flowchart_v1
# ---------------------------------------------------------------------


class TestLegacyIsolation:
    def test_legacy_entities_still_blocked(self):
        """LEGACY_DIAGRAM_READ_ONLY stays — this capability never writes
        process_diagram / instance_diagram_scope / revision_diagram_overlay."""
        from tm_app.application.gpt_actions.entities import (
            GptEntity,
            entity_supports,
        )

        for legacy in (
            GptEntity.PROCESS_DIAGRAM,
            GptEntity.INSTANCE_DIAGRAM_SCOPE,
            GptEntity.REVISION_DIAGRAM_OVERLAY,
        ):
            assert not entity_supports(legacy, "create")
            assert not entity_supports(legacy, "update")
            assert not entity_supports(legacy, "delete")

    def test_stack_exposes_no_legacy_ports(self):
        stack = _stack()
        assert not hasattr(stack, "legacy")
        assert set(stack._fields) == {"use_case", "docs", "refs"}
