"""Diagnostic V1 — Application governed-write slice.

Orchestrates the existing aggregate + repository — never SQL, never a
second authority:

    fresh AuthZ → read aggregate → cross-aggregate checks → domain method
    → save(expected_version) → authoritative read-back → postcondition
    → detached read model

Every method maps to one V1 capability. The use case is intentionally
transport-agnostic: no HTTP, no proposal_handle — PREPARE/ACT belongs to
the external governed-write orchestration layer.

Stable error codes (transport-agnostic):
``diagnostic.not_found``, ``diagnostic.revision_not_found``,
``diagnostic.evidence_out_of_revision``, ``diagnostic.concurrent_modification``,
``diagnostic.outcome_verification_failed``, ``diagnostic.persistence_error``
plus domain codes translated verbatim from ``DiagnosticError``.
"""

from __future__ import annotations

from typing import Callable

from tm_app.application.ports.authorization_port import AuthorizationPort
from tm_app.application.ports.evidence_reader_port import EvidenceReaderPort
from tm_app.application.ports.revision_reader_port import RevisionReaderPort
from tm_app.application.use_cases.diagnostic_read import (
    DiagnosticReadView,
    _snapshot,
)
from tm_app.domain.diagnostic.diagnostic import (
    CausalLink,
    ClaimLifecycle,
    Diagnostic,
    DiagnosticConclusion,
    DiagnosticError,
    EffectiveValidation,
    EpistemicState,
    EvidenceLink,
    Finding,
    Hypothesis,
    ProblemStatement,
    Provenance,
)
from tm_app.domain.ports.diagnostic_repository_port import (
    DiagnosticRepositoryPort,
)


class DiagnosticWriteError(LookupError):
    """Transport-agnostic write failure with a stable semantic code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _raise(code: str, message: str) -> None:
    raise DiagnosticWriteError(code, message)


def _map_domain_error(exc: DiagnosticError) -> DiagnosticWriteError:
    return DiagnosticWriteError(exc.code, str(exc))


class DiagnosticWriteUseCase:
    """Governed write primitives for the Diagnostic aggregate.

    Read-back is the only source of truth for success — a successful
    ``save`` return value alone never proves the outcome.
    """

    def __init__(
        self,
        *,
        diagnostics: DiagnosticRepositoryPort,
        revisions: RevisionReaderPort,
        evidence: EvidenceReaderPort,
        authorization: AuthorizationPort,
    ) -> None:
        self._diagnostics = diagnostics
        self._revisions = revisions
        self._evidence = evidence
        self._authorization = authorization

    # ------------------------------------------------------------- create

    async def create_diagnostic(
        self,
        *,
        diagnostic_id: str,
        revision_id: str,
        problem_statement: str,
        provenance: Provenance | None = None,
    ) -> DiagnosticReadView:
        await self._authorization.authorize_fresh()
        if self._revisions.get(revision_id) is None:
            _raise(
                "diagnostic.revision_not_found",
                f"revision inexistente: {revision_id}.",
            )
        try:
            diagnostic = Diagnostic(
                diagnostic_id=diagnostic_id,
                revision_id=revision_id,
                problem_statement=ProblemStatement(text=problem_statement),
                provenance=provenance,
            )
        except DiagnosticError as exc:
            raise _map_domain_error(exc) from exc
        self._persist_create(diagnostic)
        persisted = self._readback(diagnostic_id)
        if (
            persisted.revision_id != revision_id
            or persisted.problem_statement.text != problem_statement.strip()
            or persisted.version < 1
        ):
            _raise(
                "diagnostic.outcome_verification_failed",
                "read-back divergiu do diagnostic criado.",
            )
        return _snapshot(persisted)

    # ---------------------------------------------------- entity additions

    async def add_finding(
        self, *, diagnostic_id: str, finding: Finding
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.add_finding(finding),
            verify=lambda d: any(
                f.finding_id == finding.finding_id
                and f.statement == finding.statement
                for f in d.findings
            ),
        )

    async def add_hypothesis(
        self, *, diagnostic_id: str, hypothesis: Hypothesis
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.add_hypothesis(hypothesis),
            verify=lambda d: any(
                h.hypothesis_id == hypothesis.hypothesis_id
                and h.lifecycle is ClaimLifecycle.DRAFT
                for h in d.hypotheses
            ),
        )

    async def add_causal_link(
        self, *, diagnostic_id: str, link: CausalLink
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.add_causal_link(link),
            verify=lambda d: any(
                l.link_id == link.link_id for l in d.causal_links
            ),
        )

    async def add_evidence_link(
        self, *, diagnostic_id: str, link: EvidenceLink
    ) -> DiagnosticReadView:
        def precheck(diagnostic: Diagnostic) -> None:
            resolved = {
                ref.evidence_id
                for ref in self._evidence.list_by_revision(diagnostic.revision_id)
            }
            if link.evidence_id not in resolved:
                _raise(
                    "diagnostic.evidence_out_of_revision",
                    f"evidence {link.evidence_id} não pertence à revision "
                    f"{diagnostic.revision_id}.",
                )

        return await self._mutate(
            diagnostic_id,
            precheck=precheck,
            apply=lambda d: d.add_evidence_link(link),
            verify=lambda d: any(
                l.link_id == link.link_id for l in d.evidence_links
            ),
        )

    async def add_conclusion(
        self, *, diagnostic_id: str, conclusion: DiagnosticConclusion
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.add_conclusion(conclusion),
            verify=lambda d: any(
                c.conclusion_id == conclusion.conclusion_id
                and c.lifecycle is ClaimLifecycle.DRAFT
                for c in d.diagnostic_conclusions
            ),
        )

    # ------------------------------------------------- lifecycle mutations

    async def validate_hypothesis(
        self, *, diagnostic_id: str, hypothesis_id: str, note: str | None = None
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.validate_hypothesis(hypothesis_id, note=note),
            verify=lambda d: self._claim(
                d.hypotheses, hypothesis_id
            ) is not None
            and self._claim(d.hypotheses, hypothesis_id).lifecycle
            is ClaimLifecycle.VALIDATED
            and self._claim(d.hypotheses, hypothesis_id).epistemic_state
            is EpistemicState.INFERRED,
        )

    async def reject_hypothesis(
        self, *, diagnostic_id: str, hypothesis_id: str, note: str | None = None
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.reject_hypothesis(hypothesis_id, note=note),
            verify=lambda d: self._claim(
                d.hypotheses, hypothesis_id
            ) is not None
            and self._claim(d.hypotheses, hypothesis_id).lifecycle
            is ClaimLifecycle.REJECTED,
        )

    async def supersede_hypothesis(
        self, *, diagnostic_id: str, hypothesis_id: str, note: str | None = None
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.supersede_hypothesis(hypothesis_id, note=note),
            verify=lambda d: self._claim(
                d.hypotheses, hypothesis_id
            ) is not None
            and self._claim(d.hypotheses, hypothesis_id).lifecycle
            is ClaimLifecycle.SUPERSEDED,
        )

    # ------------------------------------------- effective-validation marks

    async def mark_hypothesis_stale_evidence(
        self, *, diagnostic_id: str, hypothesis_id: str
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.mark_hypothesis_stale_evidence(hypothesis_id),
            verify=lambda d: self._claim(
                d.hypotheses, hypothesis_id
            ) is not None
            and self._claim(d.hypotheses, hypothesis_id).effective_validation
            is EffectiveValidation.STALE_EVIDENCE,
        )

    async def mark_hypothesis_revalidation_required(
        self, *, diagnostic_id: str, hypothesis_id: str
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.mark_hypothesis_revalidation_required(
                hypothesis_id
            ),
            verify=lambda d: self._claim(
                d.hypotheses, hypothesis_id
            ) is not None
            and self._claim(d.hypotheses, hypothesis_id).effective_validation
            is EffectiveValidation.REVALIDATION_REQUIRED,
        )

    # --------------------------------------------------- conclusion mutations

    async def validate_conclusion(
        self, *, diagnostic_id: str, conclusion_id: str, note: str | None = None
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.validate_conclusion(conclusion_id, note=note),
            verify=lambda d: self._claim(
                d.diagnostic_conclusions, conclusion_id
            ) is not None
            and self._claim(
                d.diagnostic_conclusions, conclusion_id
            ).lifecycle
            is ClaimLifecycle.VALIDATED
            and self._claim(
                d.diagnostic_conclusions, conclusion_id
            ).effective_validation
            is EffectiveValidation.CURRENT,
        )

    async def reject_conclusion(
        self, *, diagnostic_id: str, conclusion_id: str, note: str | None = None
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.reject_conclusion(conclusion_id, note=note),
            verify=lambda d: self._claim(
                d.diagnostic_conclusions, conclusion_id
            ) is not None
            and self._claim(
                d.diagnostic_conclusions, conclusion_id
            ).lifecycle
            is ClaimLifecycle.REJECTED,
        )

    async def supersede_conclusion(
        self, *, diagnostic_id: str, conclusion_id: str, note: str | None = None
    ) -> DiagnosticReadView:
        return await self._mutate(
            diagnostic_id,
            apply=lambda d: d.supersede_conclusion(conclusion_id, note=note),
            verify=lambda d: self._claim(
                d.diagnostic_conclusions, conclusion_id
            ) is not None
            and self._claim(
                d.diagnostic_conclusions, conclusion_id
            ).lifecycle
            is ClaimLifecycle.SUPERSEDED,
        )

    # ------------------------------------------------------------ internals

    @staticmethod
    def _claim(claims, claim_id: str):
        for claim in claims:
            if getattr(claim, "hypothesis_id", None) == claim_id:
                return claim
            if getattr(claim, "conclusion_id", None) == claim_id:
                return claim
        return None

    def _require(self, diagnostic_id: str) -> Diagnostic:
        diagnostic = self._diagnostics.get(diagnostic_id)
        if diagnostic is None:
            _raise(
                "diagnostic.not_found",
                f"diagnostic inexistente: {diagnostic_id}.",
            )
        return diagnostic

    def _readback(self, diagnostic_id: str) -> Diagnostic:
        persisted = self._diagnostics.get(diagnostic_id)
        if persisted is None:
            _raise(
                "diagnostic.outcome_verification_failed",
                "read-back não encontrou o diagnostic persistido.",
            )
        return persisted

    def _persist_create(self, diagnostic: Diagnostic) -> None:
        try:
            self._diagnostics.create(diagnostic)
        except Exception as exc:
            self._map_persistence_error(exc)

    def _persist_save(self, diagnostic: Diagnostic, expected_version: int) -> None:
        try:
            self._diagnostics.save(diagnostic, expected_version=expected_version)
        except Exception as exc:
            self._map_persistence_error(exc)

    @staticmethod
    def _map_persistence_error(exc: Exception) -> None:
        code = getattr(exc, "code", "") or ""
        if code == "diagnostic.concurrent_modification":
            _raise(
                "diagnostic.concurrent_modification",
                "diagnostic modificado concorrentemente; repare o estado.",
            )
        if code == "diagnostic.save_fidelity_mismatch":
            _raise(
                "diagnostic.outcome_verification_failed",
                "persistência não confirmou o estado esperado.",
            )
        _raise(
            "diagnostic.persistence_error",
            "falha ao persistir o diagnostic.",
        )

    async def _mutate(
        self,
        diagnostic_id: str,
        *,
        apply: Callable[[Diagnostic], None],
        verify: Callable[[Diagnostic], bool],
        precheck: Callable[[Diagnostic], None] | None = None,
    ) -> DiagnosticReadView:
        await self._authorization.authorize_fresh()
        diagnostic = self._require(diagnostic_id)
        if precheck is not None:
            precheck(diagnostic)
        expected_version = diagnostic.version
        try:
            apply(diagnostic)
        except DiagnosticError as exc:
            raise _map_domain_error(exc) from exc
        self._persist_save(diagnostic, expected_version)
        persisted = self._readback(diagnostic_id)
        if persisted.version <= expected_version:
            _raise(
                "diagnostic.outcome_verification_failed",
                "version não avançou após a mutação.",
            )
        if not verify(persisted):
            _raise(
                "diagnostic.outcome_verification_failed",
                "read-back divergiu do estado esperado.",
            )
        return _snapshot(persisted)
