"""G8 — migração governada flowchart_v1 → BPMN nativo.

Cobre: mapper puro (classificação, ambiguidades, resoluções, DI,
determinismo), capability governed (PREPARE sem escrita, gates XOR,
fingerprint/stale, ACT, read-back) e use case ACT (sequência
documento→R1→metadata + compensação fail-closed).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.governed_writes import bpmn_migration_capability as cap
from tm_app.application.governed_writes.bpmn_migration_capability import (
    MigrationWriteStack,
)
from tm_app.application.governed_writes.errors import GovernedWriteError
from tm_app.application.use_cases.migrate_legacy_diagram_to_bpmn import (
    MigrationExecutionError,
    MigrateLegacyDiagramToBpmnUseCase,
)
from tm_app.application.use_cases.manage_process_bpmn_document import (
    DualModeConflict,
)
from tm_app.domain.diagram.legacy_bpmn_migration import (
    CLASS_AMBIGUOUS,
    CLASS_EXACT,
    CLASS_HEURISTIC,
    CLASS_IGNORED_METADATA,
    STATUS_AMBIGUOUS,
    STATUS_READY,
    LegacyFlowchartToBpmnMapper,
)
from tm_app.domain.entities.process_bpmn_document import (
    ProcessBpmnDocument,
    ProcessBpmnRevision,
)

PROCESSO = "33333333-3333-3333-3333-333333333333"
DOC_ID = "44444444-4444-4444-4444-444444444444"
REV_ID = "55555555-5555-5555-5555-555555555555"
USER = SimpleNamespace(id="user-a", sub="user-a", name="User A")

# ---------------------------------------------------------------------
# Fixtures flowchart_v1 (schema real: nodes[].type do catálogo BPMN,
# edges[].kind sequence|association|message_flow, lanes[]).
# ---------------------------------------------------------------------


def _linear() -> dict[str, Any]:
    return {
        "format": "flowchart_v1",
        "format_version": 1,
        "lanes": [{"id": "lane_a", "label": "Comercial", "height": 168}],
        "nodes": [
            {
                "id": "n1",
                "type": "start",
                "label": "Início",
                "lane_id": "lane_a",
                "position": {"x": 80, "y": 60},
            },
            {
                "id": "n2",
                "type": "process",
                "label": "Analisar pedido",
                "lane_id": "lane_a",
                "position": {"x": 240, "y": 50},
            },
            {
                "id": "n4",
                "type": "end",
                "label": "Fim",
                "lane_id": "lane_a",
                "position": {"x": 520, "y": 60},
            },
        ],
        "edges": [
            {"id": "e1", "from": "n1", "to": "n2", "kind": "sequence"},
            {"id": "e2", "from": "n2", "to": "n4", "kind": "sequence"},
        ],
    }


def _ambiguous_decision() -> dict[str, Any]:
    flow = _linear()
    flow["nodes"].insert(
        2,
        {
            "id": "n3",
            "type": "decision",
            "label": "Material liberado?",
            "lane_id": "lane_a",
            "position": {"x": 400, "y": 40},
        },
    )
    flow["edges"] = [
        {"id": "e1", "from": "n1", "to": "n2", "kind": "sequence"},
        {"id": "e2", "from": "n2", "to": "n3", "kind": "sequence"},
        {"id": "e3", "from": "n3", "to": "n4", "kind": "sequence"},
        {"id": "e4", "from": "n3", "to": "n2", "kind": "sequence"},
    ]
    return flow


def _classifications(candidate) -> dict[str, int]:
    return candidate.statistics["by_classification"]


# ---------------------------------------------------------------------
# Mapper puro
# ---------------------------------------------------------------------


class TestMapper:
    def test_linear_flow_ready_all_exact(self):
        candidate = LegacyFlowchartToBpmnMapper().map(
            _linear(), process_name="P"
        )
        assert candidate.status == STATUS_READY
        cls = _classifications(candidate)
        # 3 nodes + 2 edges + 1 lane, tudo EXACT
        assert cls.get(CLASS_EXACT, 0) == 6
        assert candidate.ambiguities == []
        assert "<bpmn:sequenceFlow" in candidate.bpmn_xml
        assert "<bpmndi:BPMNDiagram" in candidate.bpmn_xml
        assert "<bpmndi:BPMNShape" in candidate.bpmn_xml

    def test_id_traceability_all_objects(self):
        candidate = LegacyFlowchartToBpmnMapper().map(_linear())
        assert candidate.id_map["n1"] == "n1"
        assert candidate.id_map["edge:e1"] == "e1"
        assert candidate.id_map["lane:lane_a"] == "lane_a"
        report_ids = {r["legacy_id"] for r in candidate.mapping_report}
        assert {"n1", "n2", "n4", "e1", "e2", "lane_a"} <= report_ids

    def test_unlabeled_decision_exits_ambiguous(self):
        candidate = LegacyFlowchartToBpmnMapper().map(_ambiguous_decision())
        assert candidate.status == STATUS_AMBIGUOUS
        assert len(candidate.ambiguities) == 1
        amb = candidate.ambiguities[0]
        assert amb.ambiguity_id == "A-gw-n3"
        assert {o["id"] for o in amb.options} == {
            "label_edges",
            "accept_unconditional",
        }
        assert amb.recommended_option == "label_edges"

    def test_resolution_label_edges_reprepare_ready(self):
        candidate = LegacyFlowchartToBpmnMapper().map(
            _ambiguous_decision(),
            resolutions={
                "A-gw-n3": {
                    "option": "label_edges",
                    "values": {"e3": "Sim", "e4": "Não — retrabalho"},
                }
            },
        )
        assert candidate.status == STATUS_READY
        assert candidate.ambiguities == []
        assert 'name="Sim"' in candidate.bpmn_xml
        assert "retrabalho" in candidate.bpmn_xml

    def test_resolution_accept_unconditional_ready(self):
        candidate = LegacyFlowchartToBpmnMapper().map(
            _ambiguous_decision(),
            resolutions={"A-gw-n3": {"option": "accept_unconditional"}},
        )
        assert candidate.status == STATUS_READY

    def test_partial_resolution_stays_ambiguous(self):
        candidate = LegacyFlowchartToBpmnMapper().map(
            _ambiguous_decision(),
            resolutions={
                "A-gw-n3": {
                    "option": "label_edges",
                    "values": {"e3": "Sim"},  # e4 segue sem label
                }
            },
        )
        assert candidate.status == STATUS_AMBIGUOUS

    def test_message_flow_ambiguous_without_pools(self):
        flow = _linear()
        flow["edges"][1] = {
            "id": "e2",
            "from": "n2",
            "to": "n4",
            "kind": "message_flow",
        }
        candidate = LegacyFlowchartToBpmnMapper().map(flow)
        assert candidate.status == STATUS_AMBIGUOUS
        amb = [a for a in candidate.ambiguities if "e2" in a.legacy_object_ids]
        assert amb, "message_flow sem participants deve ser ambiguidade"

    def test_metadata_classified_ignored_not_silently_dropped(self):
        flow = _linear()
        flow["nodes"][1]["highlight"] = True
        flow["nodes"][1]["meta"] = {"owner_hint": "comercial"}
        flow["edges"][0]["routing"] = "smoothstep"
        candidate = LegacyFlowchartToBpmnMapper().map(flow)
        kinds = [
            r["legacy_kind"]
            for r in candidate.mapping_report
            if r["classification"] == CLASS_IGNORED_METADATA
        ]
        assert "node.highlight" in kinds
        assert "node.meta" in kinds
        assert "edge.routing" in kinds

    def test_missing_start_end_warns_not_blocks(self):
        flow = _linear()
        flow["nodes"] = [n for n in flow["nodes"] if n["type"] == "process"]
        flow["edges"] = []
        candidate = LegacyFlowchartToBpmnMapper().map(flow)
        assert candidate.status == STATUS_READY
        assert any("start" in w.lower() for w in candidate.warnings)
        assert any("end" in w.lower() for w in candidate.warnings)

    def test_isolated_node_warns(self):
        flow = _linear()
        flow["nodes"].append(
            {
                "id": "n_iso",
                "type": "process",
                "label": "Ilha",
                "lane_id": "lane_a",
                "position": {"x": 900, "y": 60},
            }
        )
        candidate = LegacyFlowchartToBpmnMapper().map(flow)
        assert any("isolado" in w.lower() for w in candidate.warnings)

    def test_deterministic_same_input_same_checksum(self):
        a = LegacyFlowchartToBpmnMapper().map(_linear())
        b = LegacyFlowchartToBpmnMapper().map(_linear())
        assert a.checksum_sha256 == b.checksum_sha256
        assert a.bpmn_xml == b.bpmn_xml

    def test_xml_is_well_formed(self):
        import xml.etree.ElementTree as ET

        candidate = LegacyFlowchartToBpmnMapper().map(_ambiguous_decision())
        ET.fromstring(candidate.bpmn_xml)  # não levanta

    def test_ambiguous_classification_in_report(self):
        candidate = LegacyFlowchartToBpmnMapper().map(_ambiguous_decision())
        ambiguous_entries = [
            r
            for r in candidate.mapping_report
            if r["classification"] == CLASS_AMBIGUOUS
        ]
        # e3/e4 não-rotuladas não são marcadas — a ambiguidade vive no
        # gateway; report carrega a classificação por objeto. Pelo menos
        # um entry AMBIGUOUS deve existir para rastreabilidade.
        assert ambiguous_entries or candidate.ambiguities


# ---------------------------------------------------------------------
# Fakes para a capability/use case (ports duck-typed)
# ---------------------------------------------------------------------


class FakeDocs:
    def __init__(self, active: ProcessBpmnDocument | None = None):
        self._active = active
        self.soft_deleted: list[str] = []
        self.created_revisions: list[dict] = []

    def has_active(self, pid):
        return self._active is not None

    def get_active(self, pid):
        return self._active

    def set_active(self, doc):
        self._active = doc

    def create(self, **kw):
        self._active = ProcessBpmnDocument(
            id=DOC_ID,
            processo_id=kw["processo_id"],
            working_copy_xml=kw["working_copy_xml"],
            working_copy_sha256=kw["working_copy_sha256"],
            version=1,
            created_by_user_id=kw["actor_user_id"],
            updated_by_user_id=kw["actor_user_id"],
        )
        return self._active

    def create_revision(self, **kw):
        self.created_revisions.append(kw)
        return ProcessBpmnRevision(
            id=REV_ID,
            document_id=kw["document_id"],
            revision_number=1,
            artifact_sha256=kw["artifact_sha256"],
            origin=kw["origin"],
            restored_from_revision_id=None,
            name=kw["name"],
            description=kw["description"],
            created_by_user_id=kw["actor_user_id"],
            created_by_name=kw["actor_name"],
        )

    def soft_delete(self, *, processo_id, actor_user_id):
        self.soft_deleted.append(processo_id)
        self._active = None

    def list_revisions(self, document_id):
        return [
            ProcessBpmnRevision(
                id=REV_ID,
                document_id=document_id,
                revision_number=1,
                artifact_sha256="sha",
                origin="migration",
                restored_from_revision_id=None,
                name="R1",
                description=None,
                created_by_user_id="u",
                created_by_name=None,
            )
        ]


class FakeRefs:
    def __init__(self, active=None):
        self._active = active

    def get_active(self, pid):
        return self._active


class FakeMigrations:
    def __init__(self):
        self.records: list[dict] = []

    def record_migration(self, **kw):
        self.records.append(kw)
        return {"migration_id": "m-1"}

    def latest_for_processo(self, processo_id):
        if not self.records:
            return None
        kw = self.records[-1]
        return {
            "migration_id": "m-1",
            "processo_id": processo_id,
            "document_id": kw["document_id"],
            "revision_id": kw["revision_id"],
        }


class FakeDocUseCases:
    """Stub do use case G7 — boundary validation real é testada no G7."""

    def __init__(self, docs: FakeDocs):
        self._docs = docs
        self.calls: list[str] = []

    def create_document(self, user, processo_id, xml):
        self.calls.append(xml)
        return self._docs.create(
            processo_id=processo_id,
            working_copy_xml=xml,
            working_copy_sha256=__import__("hashlib").sha256(
                xml.encode("utf-8")
            ).hexdigest(),
            actor_user_id=str(user.id),
        )


def _stack(
    docs=None, refs=None, migrations=None, doc_uc=None
) -> MigrationWriteStack:
    docs = docs or FakeDocs()
    refs = refs or FakeRefs()
    migrations = migrations or FakeMigrations()
    return MigrationWriteStack(
        use_case=MigrateLegacyDiagramToBpmnUseCase(
            docs=docs,
            refs=refs,
            migrations=migrations,
            document_use_cases=doc_uc or FakeDocUseCases(docs),
        ),
        docs=docs,
        refs=refs,
        migrations=migrations,
    )


def _request(user=USER):
    req = MagicMock()
    req.state.user = user
    return req


def _composed(flowchart) -> dict[str, Any]:
    return {
        "processo_id": PROCESSO,
        "at": "2025-01-01",
        "instancia_id": None,
        "flowchart": flowchart,
        "mermaid": "graph TD",
        "applied_revisoes": [],
        "conflicts": [],
        "base_node_count": len(flowchart.get("nodes") or []),
    }


def _prepare(stack, request, args, *, flowchart=None, processo=None):
    with (
        patch.object(
            cap.DiagramaCompositionService,
            "compose_for_processo",
            return_value=_composed(flowchart or _linear()),
        ),
        patch.object(
            cap.ProcessoRepository,
            "get",
            return_value=processo or {"nome_processo": "Proc"},
        ),
        patch.object(
            cap, "check_processo_manage_access", return_value=None
        ),
        patch.object(
            cap,
            "LxmlBpmnValidator",
            return_value=SimpleNamespace(
                validate=lambda a, evidence=None: SimpleNamespace(
                    evaluated_stages=frozenset(),
                    issues=[],
                )
            ),
        ),
    ):
        return cap.prepare(stack, request, args)


# ---------------------------------------------------------------------
# Capability — PREPARE
# ---------------------------------------------------------------------


class TestPrepare:
    def test_prepare_ready_returns_full_report(self):
        stack = _stack()
        out = _prepare(
            stack, _request(), {"processo_id": PROCESSO}
        )
        change = out["exact_change"]
        assert change["candidate_xml"].startswith("<")
        assert len(change["candidate_sha256"]) == 64
        assert len(change["legacy_source_fingerprint"]) == 64
        assert out["validation_result"]["ready"] is True
        assert out["validation_result"]["bpmn_validation"]["passed"]
        report = out["validation_result"]["migration_report"]
        assert report["statistics"]["legacy_nodes"] == 3
        assert report["statistics"]["by_classification"]["EXACT"] == 6
        impact = out["consequential_impact"]
        assert impact["mutates_legacy"] is False
        assert impact["writes_to_bpmn_modeler"] is False
        assert impact["revision_origin"] == "migration"
        # PREPARE não persiste nada
        assert stack.docs._active is None

    def test_prepare_never_writes_anything(self):
        docs = FakeDocs()
        migrations = FakeMigrations()
        stack = _stack(docs=docs, migrations=migrations)
        _prepare(stack, _request(), {"processo_id": PROCESSO})
        assert docs._active is None
        assert docs.created_revisions == []
        assert migrations.records == []

    def test_prepare_ambiguous_still_returns_report_not_ready(self):
        stack = _stack()
        out = _prepare(
            stack,
            _request(),
            {"processo_id": PROCESSO},
            flowchart=_ambiguous_decision(),
        )
        assert out["validation_result"]["ready"] is False
        report = out["validation_result"]["migration_report"]
        assert report["status"] == STATUS_AMBIGUOUS
        assert report["ambiguities"][0]["ambiguity_id"] == "A-gw-n3"
        assert stack.docs._active is None

    def test_prepare_native_exists_409(self):
        docs = FakeDocs(
            active=ProcessBpmnDocument(
                id=DOC_ID,
                processo_id=PROCESSO,
                working_copy_xml="<x/>",
                working_copy_sha256="s",
                version=1,
                created_by_user_id="u",
                updated_by_user_id="u",
            )
        )
        stack = _stack(docs=docs)
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(stack, _request(), {"processo_id": PROCESSO})
        assert exc.value.status_code == 409
        assert "NATIVE_BPMN_ALREADY_EXISTS" in str(exc.value.code)

    def test_prepare_external_reference_409(self):
        stack = _stack(refs=FakeRefs(active=SimpleNamespace(id="ref")))
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(stack, _request(), {"processo_id": PROCESSO})
        assert exc.value.status_code == 409
        assert "dual_mode" in str(exc.value.code)

    def test_prepare_empty_legacy_409(self):
        stack = _stack()
        empty = {
            "format": "flowchart_v1",
            "format_version": 1,
            "nodes": [],
            "edges": [],
            "lanes": [],
        }
        with pytest.raises(GovernedWriteError) as exc:
            _prepare(
                stack,
                _request(),
                {"processo_id": PROCESSO},
                flowchart=empty,
            )
        assert "LEGACY_DIAGRAM_EMPTY" in str(exc.value.code)

    def test_prepare_requires_processo_id(self):
        stack = _stack()
        with pytest.raises(GovernedWriteError):
            cap.prepare(stack, _request(), {})

    def test_fingerprint_changes_when_legacy_changes(self):
        docs = FakeDocs()
        stack = _stack(docs=docs)
        fp1 = _prepare(stack, _request(), {"processo_id": PROCESSO})[
            "exact_change"
        ]["legacy_source_fingerprint"]
        fp2 = _prepare(
            stack,
            _request(),
            {"processo_id": PROCESSO},
            flowchart=_ambiguous_decision(),
        )["exact_change"]["legacy_source_fingerprint"]
        assert fp1 != fp2

    def test_recompute_fingerprint_matches_prepare(self):
        stack = _stack()
        out = _prepare(stack, _request(), {"processo_id": PROCESSO})
        sealed = out["exact_change"]["legacy_source_fingerprint"]
        # Mesma fonte → fingerprint re-computado no ACT é idêntico.
        with patch.object(
            cap.DiagramaCompositionService,
            "compose_for_processo",
            return_value=_composed(_linear()),
        ):
            recomputed = cap.recompute_fingerprint(
                stack, {"processo_id": PROCESSO}
            )
        # Nota: fingerprint selado inclui ausência de native/ref — mesma
        # entrada compõe o mesmo hash.
        assert recomputed == sealed

    def test_recompute_fingerprint_detects_native_appearing(self):
        docs = FakeDocs()
        stack = _stack(docs=docs)
        sealed = _prepare(stack, _request(), {"processo_id": PROCESSO})[
            "exact_change"
        ]["legacy_source_fingerprint"]
        docs.set_active(
            ProcessBpmnDocument(
                id=DOC_ID,
                processo_id=PROCESSO,
                working_copy_xml="<x/>",
                working_copy_sha256="s",
                version=1,
                created_by_user_id="u",
                updated_by_user_id="u",
            )
        )
        with patch.object(
            cap.DiagramaCompositionService,
            "compose_for_processo",
            return_value=_composed(_linear()),
        ):
            recomputed = cap.recompute_fingerprint(
                stack, {"processo_id": PROCESSO}
            )
        assert recomputed != sealed


# ---------------------------------------------------------------------
# Use case ACT — sequência + compensação fail-closed
# ---------------------------------------------------------------------


def _commit_kwargs(candidate_xml="<bpmn/>") -> dict[str, Any]:
    import hashlib

    return {
        "processo_id": PROCESSO,
        "candidate_xml": candidate_xml,
        "candidate_sha256": hashlib.sha256(
            candidate_xml.encode("utf-8")
        ).hexdigest(),
        "legacy_source_fingerprint": "f" * 64,
        "mapping_report": {"status": "READY"},
        "source_summary": {"legacy_nodes": 3},
    }


class TestCommitUseCase:
    def test_commit_creates_document_revision1_and_metadata(self):
        docs = FakeDocs()
        migrations = FakeMigrations()
        uc = MigrateLegacyDiagramToBpmnUseCase(
            docs=docs,
            refs=FakeRefs(),
            migrations=migrations,
            document_use_cases=FakeDocUseCases(docs),
        )
        xml = "<bpmn>ok</bpmn>"
        result = uc.commit(USER, **_commit_kwargs(xml))
        assert result["verified"] is True
        assert result["document_id"] == DOC_ID
        assert result["revision_number"] == 1
        rev = docs.created_revisions[0]
        assert rev["origin"] == "migration"
        assert "migração" in (rev["name"] or "").lower()
        assert migrations.records[0]["document_id"] == DOC_ID
        assert migrations.records[0]["revision_id"] == REV_ID
        assert result["migration_id"] == "m-1"

    def test_commit_native_exists_conflict(self):
        docs = FakeDocs(
            active=ProcessBpmnDocument(
                id=DOC_ID,
                processo_id=PROCESSO,
                working_copy_xml="<x/>",
                working_copy_sha256="s",
                version=1,
                created_by_user_id="u",
                updated_by_user_id="u",
            )
        )
        uc = MigrateLegacyDiagramToBpmnUseCase(
            docs=docs,
            refs=FakeRefs(),
            migrations=FakeMigrations(),
            document_use_cases=FakeDocUseCases(docs),
        )
        with pytest.raises(DualModeConflict) as exc:
            uc.commit(USER, **_commit_kwargs())
        assert "NATIVE_BPMN_ALREADY_EXISTS" in str(exc.value)

    def test_commit_external_reference_conflict(self):
        docs = FakeDocs()
        uc = MigrateLegacyDiagramToBpmnUseCase(
            docs=docs,
            refs=FakeRefs(active=SimpleNamespace(id="ref")),
            migrations=FakeMigrations(),
            document_use_cases=FakeDocUseCases(docs),
        )
        with pytest.raises(DualModeConflict) as exc:
            uc.commit(USER, **_commit_kwargs())
        assert "dual_mode_forbidden" in str(exc.value)

    def test_commit_checksum_mismatch_refused(self):
        docs = FakeDocs()
        uc = MigrateLegacyDiagramToBpmnUseCase(
            docs=docs,
            refs=FakeRefs(),
            migrations=FakeMigrations(),
            document_use_cases=FakeDocUseCases(docs),
        )
        kwargs = _commit_kwargs("<bpmn/>")
        kwargs["candidate_sha256"] = "0" * 64
        with pytest.raises(MigrationExecutionError):
            uc.commit(USER, **kwargs)
        assert docs._active is None

    def test_commit_revision_failure_compensates_document(self):
        docs = FakeDocs()

        def _fail_revision(**kw):
            return None  # stale version → failure

        docs.create_revision = _fail_revision  # type: ignore[assignment]
        uc = MigrateLegacyDiagramToBpmnUseCase(
            docs=docs,
            refs=FakeRefs(),
            migrations=FakeMigrations(),
            document_use_cases=FakeDocUseCases(docs),
        )
        with pytest.raises(MigrationExecutionError):
            uc.commit(USER, **_commit_kwargs())
        # fail-closed: documento semi-criado é compensado
        assert docs.soft_deleted == [PROCESSO]
        assert docs._active is None

    def test_commit_metadata_failure_compensates_document(self):
        docs = FakeDocs()

        class _FailMigrations(FakeMigrations):
            def record_migration(self, **kw):
                raise RuntimeError("db down")

        uc = MigrateLegacyDiagramToBpmnUseCase(
            docs=docs,
            refs=FakeRefs(),
            migrations=_FailMigrations(),
            document_use_cases=FakeDocUseCases(docs),
        )
        with pytest.raises(RuntimeError):
            uc.commit(USER, **_commit_kwargs())
        assert docs.soft_deleted == [PROCESSO]


# ---------------------------------------------------------------------
# Capability — execute/verify
# ---------------------------------------------------------------------


class TestExecuteVerify:
    def _sealed_change(self, xml="<bpmn/>") -> dict[str, Any]:
        import hashlib

        return {
            "processo_id": PROCESSO,
            "candidate_xml": xml,
            "candidate_sha256": hashlib.sha256(
                xml.encode("utf-8")
            ).hexdigest(),
            "legacy_source_fingerprint": "f" * 64,
            "mapping_report": {},
            "source_summary": {},
        }

    def test_execute_revalidates_authz_and_commits(self):
        docs = FakeDocs()
        stack = _stack(docs=docs)
        change = self._sealed_change()
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ) as authz:
            result = cap.execute(stack, _request(), change)
        authz.assert_called_once()
        assert result["verified"] is True
        assert docs.created_revisions[0]["origin"] == "migration"

    def test_execute_denied_authz_propagates(self):
        stack = _stack()
        denied = SimpleNamespace(status_code=403)
        with patch.object(
            cap, "check_processo_manage_access", return_value=denied
        ):
            with pytest.raises(GovernedWriteError) as exc:
                cap.execute(stack, _request(), self._sealed_change())
        assert exc.value.status_code == 403
        assert stack.docs._active is None

    def test_execute_native_appeared_conflict(self):
        docs = FakeDocs(
            active=ProcessBpmnDocument(
                id=DOC_ID,
                processo_id=PROCESSO,
                working_copy_xml="<x/>",
                working_copy_sha256="s",
                version=1,
                created_by_user_id="u",
                updated_by_user_id="u",
            )
        )
        stack = _stack(docs=docs)
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ):
            with pytest.raises(GovernedWriteError) as exc:
                cap.execute(stack, _request(), self._sealed_change())
        assert exc.value.status_code == 409

    def test_verify_happy_path(self):
        docs = FakeDocs()
        stack = _stack(docs=docs)
        change = self._sealed_change()
        with patch.object(
            cap, "check_processo_manage_access", return_value=None
        ):
            result = cap.execute(stack, _request(), change)
        out = cap.verify(stack, change, result)
        assert out["document_id"] == DOC_ID
        assert out["migration"]["migration_id"] == "m-1"

    def test_verify_unverified_write_refused(self):
        stack = _stack()
        with pytest.raises(GovernedWriteError) as exc:
            cap.verify(stack, self._sealed_change(), {"verified": False})
        assert "OUTCOME_VERIFICATION_FAILED" in str(exc.value.code)


# ---------------------------------------------------------------------
# Catálogo TÉO — a capability existe e a policy é confirm_before_act
# ---------------------------------------------------------------------


class TestCatalog:
    def test_action_maps_to_capability(self):
        from tm_app.application.governed_writes.orchestrator import (
            GOVERNED_OPERATION_ACTION_TO_CAPABILITY,
        )

        assert (
            GOVERNED_OPERATION_ACTION_TO_CAPABILITY[
                "migrate_legacy_diagram_to_native_bpmn"
            ]
            == "migrate_legacy_diagram_to_native_bpmn"
        )

    def test_confirmation_policy_is_confirm_before_act(self):
        from tm_app.application.governed_writes.confirmation_policy import (
            CONFIRM_BEFORE_ACT,
            confirmation_kind_for_workflow,
        )

        assert (
            confirmation_kind_for_workflow(
                "migrate_legacy_diagram_to_native_bpmn"
            )
            == CONFIRM_BEFORE_ACT
        )

    def test_capability_descriptor_registered(self):
        from tm_app.application.gpt_actions.capability_descriptors import (
            build_capability_surface_catalog,
        )

        catalog = build_capability_surface_catalog()
        mig = [
            w
            for w in catalog["workflows"]
            if w.get("id") == "migrate_legacy_diagram_to_native_bpmn"
        ]
        assert mig, "capability ausente do catálogo vivo"
        # Actions projection prefixa gpt_*; o choke point canônico
        # continua sendo commit_proposal (mesmo do import_diagram_bpmn_xml).
        assert mig[0]["commit_via"] in {
            "commit_proposal",
            "gpt_commit_proposal",
        }
        assert mig[0]["confirmation_requirement"] is True
        entities = [e["id"] for e in catalog["entities"]]
        assert "process_bpmn_document" in entities
        # Projeção MCP também expõe a capability (paridade §106).
        mcp = build_capability_surface_catalog("mcp")
        mig_mcp = [
            w
            for w in mcp["workflows"]
            if w.get("id") == "migrate_legacy_diagram_to_native_bpmn"
        ]
        assert mig_mcp
        assert mig_mcp[0]["commit_via"] == "commit_proposal"

    def test_read_entity_registered_get_only(self):
        from tm_app.application.gpt_actions.entities import (
            GptEntity,
            entity_supports,
            parse_entity,
        )

        entity = parse_entity("process_bpmn_document")
        assert entity is GptEntity.PROCESS_BPMN_DOCUMENT
        assert entity_supports(entity, "get")
        assert not entity_supports(entity, "create")
        assert not entity_supports(entity, "update")
        assert not entity_supports(entity, "delete")
