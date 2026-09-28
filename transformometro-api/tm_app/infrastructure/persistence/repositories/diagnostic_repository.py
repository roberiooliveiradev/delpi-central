"""PostgreSQL adapter for the Diagnostic V1 aggregate.

Aggregate-only persistence: the whole aggregate is written inside one
transaction and rehydrated through the domain constructors — never through
``add_*`` mutation methods (those accept DRAFT-only by kernel contract).

Concurrency: ``save`` issues an atomic
``UPDATE ... WHERE diagnostic_id = ? AND version = expected_version
RETURNING version``. Zero rows means a lost update, not a stale check in
Python.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from psycopg import Connection

from tm_app.domain.diagnostic.diagnostic import (
    CausalLink,
    ClaimLifecycle,
    Diagnostic,
    DiagnosticConclusion,
    EffectiveValidation,
    EpistemicState,
    EvidenceLink,
    EvidenceRelation,
    Finding,
    FindingRole,
    Hypothesis,
    ProblemStatement,
    Provenance,
    ProvenanceOrigin,
    RootCauseDesignation,
    ValidationSnapshot,
)
from tm_app.domain.ports.diagnostic_repository_port import (
    DiagnosticRepositoryPort,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

logger = logging.getLogger(__name__)

_S = "transformometro"


class DiagnosticConcurrencyError(PluginsRepositoryError):
    """Lost update detected by the atomic version guard."""

    code = "diagnostic.concurrent_modification"

    def __init__(self, diagnostic_id: str, expected_version: int) -> None:
        self.diagnostic_id = diagnostic_id
        self.expected_version = expected_version
        super().__init__(
            f"{self.code}: version esperada {expected_version} diverge "
            f"para diagnostic {diagnostic_id}."
        )


class DiagnosticFidelityError(PluginsRepositoryError):
    """Durable read-back diverges from the submitted aggregate.

    Raised for silently-dropped history (omitted children) and for
    mutations the domain does not authorize (immutable field changes) —
    the write transaction is rolled back.
    """

    code = "diagnostic.save_fidelity_mismatch"

    def __init__(self, diagnostic_id: str) -> None:
        self.diagnostic_id = diagnostic_id
        super().__init__(
            f"{self.code}: aggregate reidratado diverge do submetido "
            f"para diagnostic {diagnostic_id}."
        )


def _same_semantics(a: Diagnostic, b: Diagnostic) -> bool:
    """Field-level equality ignoring persistence metadata (timestamps)."""
    return (
        a.diagnostic_id == b.diagnostic_id
        and a.revision_id == b.revision_id
        and a.problem_statement == b.problem_statement
        and a.provenance == b.provenance
        and set(a.findings) == set(b.findings)
        and set(a.hypotheses) == set(b.hypotheses)
        and set(a.causal_links) == set(b.causal_links)
        and set(a.evidence_links) == set(b.evidence_links)
        and set(a.diagnostic_conclusions) == set(b.diagnostic_conclusions)
    )


def _provenance_fields(provenance: Provenance | None) -> tuple[str | None, str | None]:
    if provenance is None:
        return (None, None)
    return (provenance.origin.value, provenance.detail)


def _row_to_provenance(row: dict[str, Any]) -> Provenance | None:
    origin = row.get("provenance_origin")
    if origin is None:
        return None
    return Provenance(
        origin=ProvenanceOrigin(origin),
        detail=row.get("provenance_detail"),
    )


class DiagnosticRepository(PluginBaseRepository, DiagnosticRepositoryPort):
    """PostgreSQL adapter — aggregate writes in a single transaction."""

    # ------------------------------------------------------------------ reads

    def get(self, diagnostic_id: str) -> Diagnostic | None:
        with self.db() as connection:
            root = self._fetch_root(connection, diagnostic_id)
            if root is None:
                return None
            children = self._fetch_children(connection, [diagnostic_id])
        return self._rehydrate(root, children)

    def list_by_revision(self, revision_id: str) -> list[Diagnostic]:
        with self.db() as connection:
            roots = self._fetch_roots_by_revision(connection, revision_id)
            if not roots:
                return []
            ids = [str(r["diagnostic_id"]) for r in roots]
            children = self._fetch_children(connection, ids)
        return [self._rehydrate(root, children) for root in roots]

    def _fetch_root(
        self, connection: Connection[dict[str, Any]], diagnostic_id: str
    ) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT * FROM {_S}.diagnostics
                    WHERE diagnostic_id = %s::uuid""",
                (diagnostic_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row is not None else None

    def _fetch_roots_by_revision(
        self, connection: Connection[dict[str, Any]], revision_id: str
    ) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT * FROM {_S}.diagnostics
                    WHERE revision_id = %s::uuid
                    ORDER BY created_at, diagnostic_id""",
                (revision_id,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def _fetch_children(
        self, connection: Connection[dict[str, Any]], diagnostic_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        """One query per child collection — no per-aggregate fan-out."""
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT * FROM {_S}.diagnostic_findings
                    WHERE diagnostic_id = ANY(%s::uuid[])
                    ORDER BY created_at, finding_id""",
                (diagnostic_ids,),
            )
            findings = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"""SELECT * FROM {_S}.diagnostic_hypotheses
                    WHERE diagnostic_id = ANY(%s::uuid[])
                    ORDER BY created_at, hypothesis_id""",
                (diagnostic_ids,),
            )
            hypotheses = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"""SELECT * FROM {_S}.diagnostic_causal_links
                    WHERE diagnostic_id = ANY(%s::uuid[])
                    ORDER BY created_at, link_id""",
                (diagnostic_ids,),
            )
            causal_links = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"""SELECT * FROM {_S}.diagnostic_evidence_links
                    WHERE diagnostic_id = ANY(%s::uuid[])
                    ORDER BY created_at, link_id""",
                (diagnostic_ids,),
            )
            evidence_links = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"""SELECT * FROM {_S}.diagnostic_conclusions
                    WHERE diagnostic_id = ANY(%s::uuid[])
                    ORDER BY created_at, conclusion_id""",
                (diagnostic_ids,),
            )
            conclusions = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"""SELECT r.* FROM {_S}.diagnostic_conclusion_refs r
                    JOIN {_S}.diagnostic_conclusions c
                      ON c.conclusion_id = r.conclusion_id
                    WHERE c.diagnostic_id = ANY(%s::uuid[])
                    ORDER BY r.conclusion_id, r.ref_kind, r.ordem""",
                (diagnostic_ids,),
            )
            refs = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"""SELECT * FROM {_S}.diagnostic_claim_snapshots
                    WHERE diagnostic_id = ANY(%s::uuid[])
                    ORDER BY claim_kind, claim_id, ordem""",
                (diagnostic_ids,),
            )
            snapshots = [dict(r) for r in cursor.fetchall()]

        return {
            "findings": findings,
            "hypotheses": hypotheses,
            "causal_links": causal_links,
            "evidence_links": evidence_links,
            "conclusions": conclusions,
            "conclusion_refs": refs,
            "claim_snapshots": snapshots,
        }

    # ------------------------------------------------------------- rehydrate

    def _rehydrate(
        self, root: dict[str, Any], children: dict[str, list[dict[str, Any]]]
    ) -> Diagnostic:
        diagnostic_id = str(root["diagnostic_id"])

        def owned(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
            return [
                r for r in rows if str(r["diagnostic_id"]) == diagnostic_id
            ]

        snapshots_of = {
            kind: {}
            for kind in ("hypothesis", "conclusion")
        }
        for row in children["claim_snapshots"]:
            if str(row["diagnostic_id"]) != diagnostic_id:
                continue
            snapshots_of[row["claim_kind"]].setdefault(
                str(row["claim_id"]), []
            ).append(
                ValidationSnapshot(
                    from_lifecycle=(
                        ClaimLifecycle(row["from_lifecycle"])
                        if row["from_lifecycle"]
                        else None
                    ),
                    to_lifecycle=ClaimLifecycle(row["to_lifecycle"]),
                    effective_validation=EffectiveValidation(
                        row["effective_validation"]
                    ),
                    note=row.get("note"),
                )
            )

        findings = [
            Finding(
                finding_id=str(r["finding_id"]),
                statement=r["statement"],
                epistemic_state=EpistemicState(r["epistemic_state"]),
                role=(
                    FindingRole(r["role"]) if r.get("role") else None
                ),
                provenance=_row_to_provenance(r),
            )
            for r in owned(children["findings"])
        ]

        hypotheses = [
            Hypothesis(
                hypothesis_id=str(r["hypothesis_id"]),
                statement=r["statement"],
                lifecycle=ClaimLifecycle(r["lifecycle"]),
                effective_validation=EffectiveValidation(
                    r["effective_validation"]
                ),
                provenance=_row_to_provenance(r),
                validation_history=tuple(
                    snapshots_of["hypothesis"].get(str(r["hypothesis_id"]), [])
                ),
            )
            for r in owned(children["hypotheses"])
        ]

        causal_links = [
            CausalLink(
                link_id=str(r["link_id"]),
                source_hypothesis_id=str(r["source_hypothesis_id"]),
                target_id=str(r["target_id"]),
            )
            for r in owned(children["causal_links"])
        ]

        evidence_links = [
            EvidenceLink(
                link_id=str(r["link_id"]),
                evidence_id=str(r["evidence_id"]),
                relation=EvidenceRelation(r["relation"]),
                target_id=(
                    str(r["target_id"]) if r.get("target_id") else None
                ),
            )
            for r in owned(children["evidence_links"])
        ]

        conclusions = []
        for r in owned(children["conclusions"]):
            conclusion_id = str(r["conclusion_id"])
            refs = [
                ref
                for ref in children["conclusion_refs"]
                if str(ref["conclusion_id"]) == conclusion_id
            ]
            hypothesis_ids = tuple(
                str(ref["ref_id"])
                for ref in sorted(refs, key=lambda x: x["ordem"])
                if ref["ref_kind"] == "hypothesis"
            )
            finding_ids = tuple(
                str(ref["ref_id"])
                for ref in sorted(refs, key=lambda x: x["ordem"])
                if ref["ref_kind"] == "finding"
            )
            root_cause_id = r.get("root_cause_hypothesis_id")
            conclusions.append(
                DiagnosticConclusion(
                    conclusion_id=conclusion_id,
                    statement=r["statement"],
                    lifecycle=ClaimLifecycle(r["lifecycle"]),
                    effective_validation=EffectiveValidation(
                        r["effective_validation"]
                    ),
                    rationale=r.get("rationale"),
                    hypothesis_ids=hypothesis_ids,
                    finding_ids=finding_ids,
                    root_cause=(
                        RootCauseDesignation(str(root_cause_id))
                        if root_cause_id
                        else None
                    ),
                    provenance=_row_to_provenance(r),
                    validation_history=tuple(
                        snapshots_of["conclusion"].get(conclusion_id, [])
                    ),
                )
            )

        return Diagnostic(
            diagnostic_id=diagnostic_id,
            revision_id=str(root["revision_id"]),
            problem_statement=ProblemStatement(root["problem_statement"]),
            version=int(root["version"]),
            findings=findings,
            hypotheses=hypotheses,
            causal_links=causal_links,
            evidence_links=evidence_links,
            diagnostic_conclusions=conclusions,
            provenance=_row_to_provenance(root),
        )

    # ----------------------------------------------------------------- writes

    def create(self, diagnostic: Diagnostic) -> Diagnostic:
        try:
            with self.db() as connection:
                self._insert_root(connection, diagnostic)
                self._write_children(connection, diagnostic)
                self._assert_durable_fidelity(
                    connection, diagnostic, expected_version=None
                )
                connection.commit()
        except (DiagnosticConcurrencyError, DiagnosticFidelityError):
            raise
        except Exception as exc:
            logger.exception("diagnostic create failed")
            raise PluginsRepositoryError(
                f"Falha ao persistir diagnostic: {exc}"
            ) from exc
        return diagnostic

    def save(self, diagnostic: Diagnostic, *, expected_version: int) -> int:
        try:
            with self.db() as connection:
                new_version = self._update_root(
                    connection, diagnostic, expected_version
                )
                self._write_children(connection, diagnostic)
                self._assert_durable_fidelity(
                    connection, diagnostic, expected_version=new_version
                )
                connection.commit()
        except (DiagnosticConcurrencyError, DiagnosticFidelityError):
            raise
        except Exception as exc:
            logger.exception("diagnostic save failed")
            raise PluginsRepositoryError(
                f"Falha ao persistir diagnostic: {exc}"
            ) from exc
        return new_version

    def _assert_durable_fidelity(
        self,
        connection: Connection[dict[str, Any]],
        diagnostic: Diagnostic,
        *,
        expected_version: int | None,
    ) -> None:
        """Authoritative in-transaction read-back.

        Success requires the durable aggregate to be semantically equal to
        the submitted one (plus the expected version on save). An aggregate
        that omits persisted children or mutates fields the domain freezes
        fails closed here — never hard-deleted, never silently kept.
        """
        root = self._fetch_root(connection, diagnostic.diagnostic_id)
        if root is None:
            raise DiagnosticFidelityError(diagnostic.diagnostic_id)
        children = self._fetch_children(connection, [diagnostic.diagnostic_id])
        rehydrated = self._rehydrate(root, children)
        if expected_version is not None:
            if rehydrated.version != expected_version:
                raise DiagnosticFidelityError(diagnostic.diagnostic_id)
        elif rehydrated.version != diagnostic.version:
            raise DiagnosticFidelityError(diagnostic.diagnostic_id)
        if not _same_semantics(diagnostic, rehydrated):
            raise DiagnosticFidelityError(diagnostic.diagnostic_id)

    def _insert_root(
        self, connection: Connection[dict[str, Any]], diagnostic: Diagnostic
    ) -> None:
        origin, detail = _provenance_fields(diagnostic.provenance)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""INSERT INTO {_S}.diagnostics
                    (diagnostic_id, revision_id, problem_statement, version,
                     provenance_origin, provenance_detail)
                    VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s)""",
                (
                    diagnostic.diagnostic_id,
                    diagnostic.revision_id,
                    diagnostic.problem_statement.text,
                    diagnostic.version,
                    origin,
                    detail,
                ),
            )

    def _update_root(
        self,
        connection: Connection[dict[str, Any]],
        diagnostic: Diagnostic,
        expected_version: int,
    ) -> int:
        origin, detail = _provenance_fields(diagnostic.provenance)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""UPDATE {_S}.diagnostics
                    SET problem_statement = %s,
                        provenance_origin = %s,
                        provenance_detail = %s,
                        version = version + 1,
                        updated_at = NOW()
                    WHERE diagnostic_id = %s::uuid
                      AND version = %s
                    RETURNING version""",
                (
                    diagnostic.problem_statement.text,
                    origin,
                    detail,
                    diagnostic.diagnostic_id,
                    expected_version,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise DiagnosticConcurrencyError(
                diagnostic.diagnostic_id, expected_version
            )
        return int(row["version"])

    def _write_children(
        self, connection: Connection[dict[str, Any]], diagnostic: Diagnostic
    ) -> None:
        """Upsert the full child set — never delete.

        The aggregate has no removal API, so the persisted child set always
        equals the aggregate child set; only lifecycle/effective fields of
        already-materialized claims can change. Historical rows are never
        hard-deleted.
        """
        did = diagnostic.diagnostic_id
        with connection.cursor() as cursor:
            if diagnostic.findings:
                cursor.executemany(
                    f"""INSERT INTO {_S}.diagnostic_findings
                        (finding_id, diagnostic_id, statement, epistemic_state,
                         role, provenance_origin, provenance_detail)
                        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s)
                        ON CONFLICT (finding_id) DO NOTHING""",
                    [
                        (
                            f.finding_id,
                            did,
                            f.statement,
                            f.epistemic_state.value,
                            f.role.value if f.role else None,
                            *_provenance_fields(f.provenance),
                        )
                        for f in diagnostic.findings
                    ],
                )
            if diagnostic.hypotheses:
                cursor.executemany(
                    f"""INSERT INTO {_S}.diagnostic_hypotheses
                        (hypothesis_id, diagnostic_id, statement,
                         epistemic_state, lifecycle, effective_validation,
                         provenance_origin, provenance_detail)
                        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (hypothesis_id) DO UPDATE SET
                            lifecycle = EXCLUDED.lifecycle,
                            effective_validation =
                                EXCLUDED.effective_validation,
                            updated_at = NOW()""",
                    [
                        (
                            h.hypothesis_id,
                            did,
                            h.statement,
                            h.epistemic_state.value,
                            h.lifecycle.value,
                            h.effective_validation.value,
                            *_provenance_fields(h.provenance),
                        )
                        for h in diagnostic.hypotheses
                    ],
                )
            if diagnostic.causal_links:
                cursor.executemany(
                    f"""INSERT INTO {_S}.diagnostic_causal_links
                        (link_id, diagnostic_id, source_hypothesis_id,
                         target_id, relation)
                        VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid, %s)
                        ON CONFLICT (link_id) DO NOTHING""",
                    [
                        (
                            link.link_id,
                            did,
                            link.source_hypothesis_id,
                            link.target_id,
                            link.relation.value,
                        )
                        for link in diagnostic.causal_links
                    ],
                )
            if diagnostic.evidence_links:
                cursor.executemany(
                    f"""INSERT INTO {_S}.diagnostic_evidence_links
                        (link_id, diagnostic_id, evidence_id, relation,
                         target_id)
                        VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s::uuid)
                        ON CONFLICT (link_id) DO NOTHING""",
                    [
                        (
                            link.link_id,
                            did,
                            link.evidence_id,
                            link.relation.value,
                            link.target_id,
                        )
                        for link in diagnostic.evidence_links
                    ],
                )
            if diagnostic.diagnostic_conclusions:
                cursor.executemany(
                    f"""INSERT INTO {_S}.diagnostic_conclusions
                        (conclusion_id, diagnostic_id, statement, rationale,
                         epistemic_state, lifecycle, effective_validation,
                         root_cause_hypothesis_id,
                         provenance_origin, provenance_detail)
                        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s,
                                %s::uuid, %s, %s)
                        ON CONFLICT (conclusion_id) DO UPDATE SET
                            lifecycle = EXCLUDED.lifecycle,
                            effective_validation =
                                EXCLUDED.effective_validation,
                            updated_at = NOW()""",
                    [
                        (
                            c.conclusion_id,
                            did,
                            c.statement,
                            c.rationale,
                            c.epistemic_state.value,
                            c.lifecycle.value,
                            c.effective_validation.value,
                            (
                                c.root_cause.hypothesis_id
                                if c.root_cause
                                else None
                            ),
                            *_provenance_fields(c.provenance),
                        )
                        for c in diagnostic.diagnostic_conclusions
                    ],
                )
            ref_rows: list[tuple[Any, ...]] = []
            for conclusion in diagnostic.diagnostic_conclusions:
                ref_rows += [
                    (conclusion.conclusion_id, "hypothesis", ref_id, i)
                    for i, ref_id in enumerate(conclusion.hypothesis_ids)
                ]
                ref_rows += [
                    (conclusion.conclusion_id, "finding", ref_id, i)
                    for i, ref_id in enumerate(conclusion.finding_ids)
                ]
            if ref_rows:
                cursor.executemany(
                    f"""INSERT INTO {_S}.diagnostic_conclusion_refs
                        (conclusion_id, ref_kind, ref_id, ordem)
                        VALUES (%s::uuid, %s, %s::uuid, %s)
                        ON CONFLICT (conclusion_id, ref_kind, ref_id)
                        DO NOTHING""",
                    ref_rows,
                )
            snapshot_rows: list[tuple[Any, ...]] = []
            for claim_kind, claims in (
                ("hypothesis", diagnostic.hypotheses),
                ("conclusion", diagnostic.diagnostic_conclusions),
            ):
                for claim in claims:
                    claim_id = (
                        claim.hypothesis_id
                        if claim_kind == "hypothesis"
                        else claim.conclusion_id
                    )
                    for i, snap in enumerate(claim.validation_history):
                        snapshot_rows.append(
                            (
                                claim_kind,
                                claim_id,
                                did,
                                i,
                                (
                                    snap.from_lifecycle.value
                                    if snap.from_lifecycle
                                    else None
                                ),
                                snap.to_lifecycle.value,
                                snap.effective_validation.value,
                                snap.note,
                            )
                        )
            if snapshot_rows:
                cursor.executemany(
                    f"""INSERT INTO {_S}.diagnostic_claim_snapshots
                        (claim_kind, claim_id, diagnostic_id, ordem,
                         from_lifecycle, to_lifecycle, effective_validation,
                         note)
                        VALUES (%s, %s::uuid, %s::uuid, %s, %s, %s, %s, %s)
                        ON CONFLICT (claim_kind, claim_id, ordem)
                        DO NOTHING""",
                    snapshot_rows,
                )
