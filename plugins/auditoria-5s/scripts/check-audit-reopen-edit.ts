/**
 * Regressão: reabrir avaliação libera edição; NC só some ao limpar nota do critério.
 * Uso: node --experimental-strip-types scripts/check-audit-reopen-edit.ts
 */
import assert from "node:assert/strict";

import {
  canEditEvaluation,
  canReopenEvaluation,
} from "../src/constants/audit5s.ts";

assert.equal(canEditEvaluation("draft"), true);
assert.equal(canEditEvaluation("evaluation_complete"), false);
assert.equal(canEditEvaluation("nc_in_progress"), false);
assert.equal(canEditEvaluation("closed"), false);

assert.equal(canReopenEvaluation("evaluation_complete"), true);
assert.equal(canReopenEvaluation("nc_in_progress"), true);
assert.equal(canReopenEvaluation("draft"), false);
assert.equal(canReopenEvaluation("closed"), false);

/** Espelha `nc_cleared_by_score` / `is_nc_candidate` da API. */
function isNcCandidate(score: number | null, isNotApplicable: boolean): boolean {
  return !isNotApplicable && (score === 1 || score === 3);
}
function ncClearedByScore(score: number | null, isNotApplicable: boolean): boolean {
  return !isNcCandidate(score, isNotApplicable);
}

assert.equal(ncClearedByScore(5, false), true);
assert.equal(ncClearedByScore(null, true), true);
assert.equal(ncClearedByScore(1, false), false);
assert.equal(ncClearedByScore(3, false), false);

console.log("ok: reabrir avaliação + cancelamento pontual de NC por nota");
