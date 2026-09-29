import { describe, expect, it } from "vitest";

import type {
  Diagnostic,
  DiagnosticProposal,
} from "../../../data/api/transformometroDiagnosticApi";
import { verifyDiagnosticOutcome } from "./diagnosticVerification";

const baseDiagnostic: Diagnostic = {
  diagnostic_id: "diag-1",
  revision_id: "rev-1",
  problem_statement: "Problema",
  version: 2,
  provenance: null,
  findings: [
    {
      finding_id: "f-1",
      statement: "Achado",
      epistemic_state: "OBSERVED",
      role: "SYMPTOM",
      provenance: null,
    },
  ],
  hypotheses: [
    {
      hypothesis_id: "h-1",
      statement: "Hipótese",
      lifecycle: "VALIDATED",
      effective_validation: "CURRENT",
      epistemic_state: "INFERRED",
      provenance: null,
      validation_history: [],
    },
  ],
  causal_links: [
    { link_id: "l-1", source_hypothesis_id: "h-1", target_id: "f-1", relation: "CONTRIBUTES_TO" },
  ],
  evidence_links: [
    { link_id: "e-1", evidence_id: "ev-1", relation: "CONTRADICTS", target_id: "h-1" },
  ],
  conclusions: [
    {
      conclusion_id: "c-1",
      statement: "Conclusão",
      rationale: "Porque",
      hypothesis_ids: ["h-1"],
      finding_ids: ["f-1"],
      root_cause_hypothesis_id: "h-1",
      lifecycle: "DRAFT",
      effective_validation: "CURRENT",
      epistemic_state: "INFERRED",
      provenance: null,
      validation_history: [],
    },
  ],
};

function proposal(postcondition: Record<string, unknown>): DiagnosticProposal {
  return {
    proposal_handle: "gp_1",
    proposal_id: "p-1",
    capability: "manage_diagnostic",
    resource_type: "diagnostic",
    exact_change: { action: "x", diagnostic_id: "diag-1" },
    expected_postcondition: postcondition,
  };
}

describe("verifyDiagnosticOutcome", () => {
  it("confirma criação quando o diagnostic_id está presente", () => {
    expect(
      verifyDiagnosticOutcome(
        proposal({ type: "diagnostic_created", diagnostic_id: "diag-1", revision_id: "rev-1" }),
        baseDiagnostic,
      ).ok,
    ).toBe(true);
  });

  it("falha criação quando o id não corresponde", () => {
    const r = verifyDiagnosticOutcome(
      proposal({ type: "diagnostic_created", diagnostic_id: "diag-9" }),
      baseDiagnostic,
    );
    expect(r.ok).toBe(false);
  });

  it("confirma entity_present para cada coleção canônica", () => {
    for (const [action, key, id] of [
      ["add_finding", "finding_id", "f-1"],
      ["add_hypothesis", "hypothesis_id", "h-1"],
      ["add_causal_link", "link_id", "l-1"],
      ["add_evidence_link", "link_id", "e-1"],
      ["add_conclusion", "conclusion_id", "c-1"],
    ] as const) {
      const r = verifyDiagnosticOutcome(
        proposal({ type: "entity_present", action, payload: { [key]: id } }),
        baseDiagnostic,
      );
      expect(r.ok, `${action} deve confirmar ${id}`).toBe(true);
    }
  });

  it("falha entity_present quando a entidade não aparece no read-back", () => {
    const r = verifyDiagnosticOutcome(
      proposal({ type: "entity_present", action: "add_finding", payload: { finding_id: "f-9" } }),
      baseDiagnostic,
    );
    expect(r).toEqual({ ok: false, reason: "entity_absent" });
  });

  it("confirma transição de lifecycle de hipótese", () => {
    expect(
      verifyDiagnosticOutcome(
        proposal({ type: "hypothesis_lifecycle", target: "VALIDATED", hypothesis_id: "h-1" }),
        baseDiagnostic,
      ).ok,
    ).toBe(true);
    expect(
      verifyDiagnosticOutcome(
        proposal({ type: "hypothesis_lifecycle", target: "REJECTED", hypothesis_id: "h-1" }),
        baseDiagnostic,
      ).ok,
    ).toBe(false);
  });

  it("confirma marca de effective_validation de hipótese", () => {
    const d: Diagnostic = {
      ...baseDiagnostic,
      hypotheses: [{ ...baseDiagnostic.hypotheses[0], effective_validation: "STALE_EVIDENCE" }],
    };
    expect(
      verifyDiagnosticOutcome(
        proposal({ type: "hypothesis_effective", target: "STALE_EVIDENCE", hypothesis_id: "h-1" }),
        d,
      ).ok,
    ).toBe(true);
  });

  it("confirma lifecycle de conclusão", () => {
    const d: Diagnostic = {
      ...baseDiagnostic,
      conclusions: [{ ...baseDiagnostic.conclusions[0], lifecycle: "VALIDATED" }],
    };
    expect(
      verifyDiagnosticOutcome(
        proposal({ type: "conclusion_lifecycle", target: "VALIDATED", conclusion_id: "c-1" }),
        d,
      ).ok,
    ).toBe(true);
  });

  it("postcondition desconhecido nunca é sucesso", () => {
    expect(
      verifyDiagnosticOutcome(proposal({ type: "algo_novo" }), baseDiagnostic),
    ).toEqual({ ok: false, reason: "unknown_postcondition" });
  });
});
