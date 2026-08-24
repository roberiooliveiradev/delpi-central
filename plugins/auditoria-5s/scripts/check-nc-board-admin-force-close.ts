/**
 * Regressão: encerramento admin de NC individual no board.
 * Uso: node --experimental-strip-types scripts/check-nc-board-admin-force-close.ts
 */
import assert from "node:assert/strict";

import {
  canAdminForceCloseNcBoardItem,
  canUpdateNcBoardItem,
  isAdminPath,
  isNcBoardViewOnly,
} from "../src/constants/audit5s.ts";

assert.equal(canAdminForceCloseNcBoardItem("open"), true);
assert.equal(canAdminForceCloseNcBoardItem("in_progress"), true);
assert.equal(canAdminForceCloseNcBoardItem("closed"), false);
assert.equal(canAdminForceCloseNcBoardItem("cancelled"), false);

assert.equal(isNcBoardViewOnly("cancelled"), true);
assert.equal(canUpdateNcBoardItem("open"), true);
assert.equal(canUpdateNcBoardItem("cancelled"), false);

assert.equal(isAdminPath("/apps/auditoria-5s/filial-01/admin"), true);
assert.equal(isAdminPath("/apps/auditoria-5s/filial-01/nc-board"), false);

console.log("ok: nc-board admin force-close NC");
