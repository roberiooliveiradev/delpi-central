"""Diagnostic read-model → transport projection shared by surfaces.

Pure field mapping from the canonical Application read models
(``DiagnosticReadView``, ``DiagnosticReadContext``, ``DiagnosticListResult``,
``RevisionContext``) to plain JSON-safe dicts. This module holds NO domain
rule, NO authorization and NO persistence — both interface consumers
(Portal HTTP routes and the MCP tool bridge) project through it so the two
surfaces cannot drift apart.
"""

from __future__ import annotations

from typing import Any


def project_provenance(provenance: Any) -> dict | None:
    if provenance is None:
        return None
    return {
        "origin": provenance.origin.value,
        "detail": provenance.detail,
    }


def project_validation_history(history: Any) -> list[dict]:
    return [
        {
            "from_lifecycle": s.from_lifecycle.value,
            "to_lifecycle": s.to_lifecycle.value,
            "effective_validation": s.effective_validation.value,
            "note": s.note,
        }
        for s in (history or ())
    ]


def project_revision(revision: Any) -> dict:
    return {
        "revision_id": revision.revision_id,
        "processo_id": revision.processo_id,
        "instancia_id": revision.instancia_id,
        "versao_revisao": revision.versao_revisao,
        "cenario_tipo": revision.cenario_tipo,
        "revisao_referencia_id": revision.revisao_referencia_id,
    }


def project_finding(finding: Any) -> dict:
    return {
        "finding_id": finding.finding_id,
        "statement": finding.statement,
        "epistemic_state": finding.epistemic_state.value,
        "role": finding.role.value if finding.role is not None else None,
        "provenance": project_provenance(finding.provenance),
    }


def project_claim_fields(claim: Any) -> dict:
    return {
        "lifecycle": claim.lifecycle.value,
        "effective_validation": claim.effective_validation.value,
        "epistemic_state": claim.epistemic_state.value,
        "provenance": project_provenance(claim.provenance),
        "validation_history": project_validation_history(
            claim.validation_history
        ),
    }


def project_hypothesis(hypothesis: Any) -> dict:
    return {
        "hypothesis_id": hypothesis.hypothesis_id,
        "statement": hypothesis.statement,
        **project_claim_fields(hypothesis),
    }


def project_causal_link(link: Any) -> dict:
    return {
        "link_id": link.link_id,
        "source_hypothesis_id": link.source_hypothesis_id,
        "target_id": link.target_id,
        "relation": link.relation.value,
    }


def project_evidence_link_entity(link: Any) -> dict:
    return {
        "link_id": link.link_id,
        "evidence_id": link.evidence_id,
        "relation": link.relation.value,
        "target_id": link.target_id,
    }


def project_conclusion(conclusion: Any) -> dict:
    return {
        "conclusion_id": conclusion.conclusion_id,
        "statement": conclusion.statement,
        "rationale": conclusion.rationale,
        "hypothesis_ids": list(conclusion.hypothesis_ids),
        "finding_ids": list(conclusion.finding_ids),
        "root_cause_hypothesis_id": (
            conclusion.root_cause.hypothesis_id
            if conclusion.root_cause is not None
            else None
        ),
        **project_claim_fields(conclusion),
    }


def project_evidence_link_view(link: Any) -> dict:
    evidence = link.evidence
    return {
        "link_id": link.link_id,
        "evidence_id": link.evidence_id,
        "relation": link.relation,
        "target_id": link.target_id,
        "target_kind": link.target_kind,
        "resolved_in_revision": link.resolved_in_revision,
        "evidence": (
            {
                "evidence_id": evidence.evidence_id,
                "revisao_id": evidence.revisao_id,
                "tipo": evidence.tipo,
                "nome_arquivo": evidence.nome_arquivo,
                "descricao": evidence.descricao,
            }
            if evidence is not None
            else None
        ),
    }


def project_diagnostic(diagnostic: Any) -> dict:
    return {
        "diagnostic_id": diagnostic.diagnostic_id,
        "revision_id": diagnostic.revision_id,
        "problem_statement": diagnostic.problem_statement.text,
        "version": diagnostic.version,
        "provenance": project_provenance(diagnostic.provenance),
        "findings": [project_finding(f) for f in diagnostic.findings],
        "hypotheses": [project_hypothesis(h) for h in diagnostic.hypotheses],
        "causal_links": [
            project_causal_link(l) for l in diagnostic.causal_links
        ],
        "evidence_links": [
            project_evidence_link_entity(l)
            for l in diagnostic.evidence_links
        ],
        "conclusions": [
            project_conclusion(c)
            for c in diagnostic.diagnostic_conclusions
        ],
    }


def project_read_context(ctx: Any) -> dict:
    """``DiagnosticReadContext`` → full detail payload (shared shape)."""
    return {
        "diagnostic": project_diagnostic(ctx.diagnostic),
        "revision": project_revision(ctx.revision),
        "evidence_links": [
            project_evidence_link_view(l) for l in ctx.evidence_links
        ],
        "data_quality": {
            "signals": [
                {"code": s.code, "detail": s.detail}
                for s in ctx.data_quality.signals
            ],
            "unresolved_evidence_links": list(
                ctx.data_quality.unresolved_evidence_links
            ),
        },
    }


def project_summary(item: Any) -> dict:
    """``DiagnosticSummary`` → list-item payload (shared shape)."""
    return {
        "diagnostic_id": item.diagnostic_id,
        "version": item.version,
        "problem_statement": item.problem_statement,
        "findings_count": item.findings_count,
        "hypotheses_count": item.hypotheses_count,
        "causal_links_count": item.causal_links_count,
        "evidence_links_count": item.evidence_links_count,
        "conclusions_count": item.conclusions_count,
        "has_validated_conclusion": item.has_validated_conclusion,
        "revalidation_attention_required": item.revalidation_attention_required,
    }
