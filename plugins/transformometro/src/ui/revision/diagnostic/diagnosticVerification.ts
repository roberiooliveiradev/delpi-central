/**
 * Read-back verification — a COMMIT 2xx is never treated as success on its
 * own. The sealed `expected_postcondition` is checked against the canonical
 * GET read-back before the UI reports the outcome.
 */
import type {
  Diagnostic,
  DiagnosticProposal,
} from "../../../data/api/transformometroDiagnosticApi";

export type OutcomeVerification =
  | { ok: true }
  | { ok: false; reason: string };

/**
 * Verifies `expected_postcondition` (sealed at PREPARE) against the
 * authoritative Diagnostic state re-read after COMMIT.
 */
export function verifyDiagnosticOutcome(
  proposal: DiagnosticProposal,
  diagnostic: Diagnostic,
): OutcomeVerification {
  const post = proposal.expected_postcondition ?? {};
  const type = post["type"];
  const payload = (post["payload"] ?? {}) as Record<string, unknown>;

  if (type === "diagnostic_created") {
    return String(post["diagnostic_id"] ?? "") === diagnostic.diagnostic_id
      ? { ok: true }
      : { ok: false, reason: "diagnostic_not_found" };
  }

  if (type === "entity_present") {
    const action = String(post["action"] ?? "");
    const present =
      (action === "add_finding" &&
        diagnostic.findings.some((f) => f.finding_id === payload["finding_id"])) ||
      (action === "add_hypothesis" &&
        diagnostic.hypotheses.some((h) => h.hypothesis_id === payload["hypothesis_id"])) ||
      (action === "add_causal_link" &&
        diagnostic.causal_links.some((l) => l.link_id === payload["link_id"])) ||
      (action === "add_evidence_link" &&
        diagnostic.evidence_links.some((l) => l.link_id === payload["link_id"])) ||
      (action === "add_conclusion" &&
        diagnostic.conclusions.some((c) => c.conclusion_id === payload["conclusion_id"]));
    return present ? { ok: true } : { ok: false, reason: "entity_absent" };
  }

  if (type === "hypothesis_lifecycle" || type === "conclusion_lifecycle") {
    const target = String(post["target"] ?? "");
    const idKey =
      type === "hypothesis_lifecycle" ? "hypothesis_id" : "conclusion_id";
    const items =
      type === "hypothesis_lifecycle" ? diagnostic.hypotheses : diagnostic.conclusions;
    const item = items.find(
      (entry) =>
        (entry as Record<string, unknown>)[idKey] === post[idKey],
    );
    return item && item.lifecycle === target
      ? { ok: true }
      : { ok: false, reason: "lifecycle_not_applied" };
  }

  if (type === "hypothesis_effective") {
    const target = String(post["target"] ?? "");
    const item = diagnostic.hypotheses.find(
      (h) => h.hypothesis_id === post["hypothesis_id"],
    );
    return item && item.effective_validation === target
      ? { ok: true }
      : { ok: false, reason: "effective_validation_not_applied" };
  }

  // Unknown postcondition shape → do not claim success.
  return { ok: false, reason: "unknown_postcondition" };
}
