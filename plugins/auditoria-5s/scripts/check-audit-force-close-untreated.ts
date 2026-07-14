/**
 * Regressão: encerramento admin sem tratar NCs.
 * Uso: node --experimental-strip-types scripts/check-audit-force-close-untreated.ts
 */
import assert from "node:assert/strict";

import {
  auditStatusLabel,
  branchFromPathname,
  canForceCloseUntreatedNcs,
  isAdminPath,
  isAuditClosed,
} from "../src/constants/audit5s.ts";

assert.equal(isAuditClosed("closed"), true);
assert.equal(isAuditClosed("closed_without_nc_treatment"), true);
assert.equal(isAuditClosed("nc_in_progress"), false);

assert.equal(canForceCloseUntreatedNcs("evaluation_complete", 80), true);
assert.equal(canForceCloseUntreatedNcs("nc_in_progress", 70), true);
assert.equal(canForceCloseUntreatedNcs("evaluation_complete", 100), false);
assert.equal(canForceCloseUntreatedNcs("closed", 80), false);
assert.equal(canForceCloseUntreatedNcs("closed_without_nc_treatment", 80), false);

assert.equal(
  auditStatusLabel("closed_without_nc_treatment"),
  "Encerrado sem tratar NC's",
);

assert.equal(branchFromPathname("/apps/auditoria-5s/filial-01/admin"), "01");
assert.equal(branchFromPathname("/apps/auditoria-5s/filial-02/admin"), "02");
assert.equal(branchFromPathname("/apps/auditoria-5s/admin"), null);

assert.equal(isAdminPath("/apps/auditoria-5s/filial-01/admin"), true);
assert.equal(isAdminPath("/apps/auditoria-5s/filial-01"), false);
assert.equal(isAdminPath("/apps/auditoria-5s/filial-02/admin/"), true);

console.log("ok: force-close untreated NC + admin por filial");
