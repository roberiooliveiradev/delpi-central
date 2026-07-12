/**
 * Regressão: auditoria 100% — status, ação e regra do pill sem NC.
 * Uso: node --experimental-strip-types scripts/check-audit-perfect-score.ts
 */
import assert from "node:assert/strict";

import {
  auditRequiresNcTreatment,
  auditStatusLabel,
  auditStatusVariant,
  canFinalizeWithoutNc,
  isPerfectAuditScore,
  listPrimaryActionLabel,
  ncActionLabel,
} from "../src/constants/audit5s.ts";

/** Espelha `scorePercentClass` em auditList.ts (mesma regra canônica). */
function scorePercentClass(
  value: number | null | undefined,
  status?: string,
): string {
  if (status && auditRequiresNcTreatment(status, value)) {
    return "a5s-score-pill--attention";
  }
  if (value == null) return "a5s-score-pill--empty";
  if (value >= 80) return "a5s-score-pill--high";
  if (value >= 60) return "a5s-score-pill--mid";
  return "a5s-score-pill--low";
}

assert.equal(isPerfectAuditScore(100), true);
assert.equal(isPerfectAuditScore(99.99), false);
assert.equal(canFinalizeWithoutNc("evaluation_complete", 100), true);
assert.equal(canFinalizeWithoutNc("evaluation_complete", 94.67), false);
assert.equal(auditRequiresNcTreatment("evaluation_complete", 100), false);
assert.equal(auditRequiresNcTreatment("evaluation_complete", 94.67), true);
assert.equal(scorePercentClass(100, "evaluation_complete"), "a5s-score-pill--high");
assert.equal(scorePercentClass(94.67, "evaluation_complete"), "a5s-score-pill--attention");
assert.equal(auditStatusLabel("evaluation_complete", 100), "Pronto para finalizar");
assert.equal(auditStatusVariant("evaluation_complete", 100), "complete");
assert.equal(ncActionLabel("evaluation_complete", 100), "Finalizar");
assert.equal(listPrimaryActionLabel("evaluation_complete", 100), "Finalizar");
assert.equal(listPrimaryActionLabel("evaluation_complete", 94.67), "Tratar NC");

console.log("ok: auditoria 100% sem NC (pill, status, Finalizar)");
