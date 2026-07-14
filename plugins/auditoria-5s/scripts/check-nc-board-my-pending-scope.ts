/**
 * Smoke estática: escopo my-pending da notificação NC.
 * npm run check:nc-board-my-pending (via tsx ou assert no CI).
 */
import assert from "node:assert/strict";

import {
  auditViewFromPathname,
  ncBoardScopeFromLocation,
} from "../src/constants/audit5s";

assert.equal(
  auditViewFromPathname("/apps/auditoria-5s/filial-01/nc-board/my-pending"),
  "nc-board",
);
assert.equal(
  ncBoardScopeFromLocation("/apps/auditoria-5s/filial-01/nc-board/my-pending"),
  "my-pending",
);
assert.equal(
  ncBoardScopeFromLocation("/apps/auditoria-5s/filial-01/nc-board", "?scope=my-pending"),
  "my-pending",
);
assert.equal(
  ncBoardScopeFromLocation("/apps/auditoria-5s/filial-01/nc-board"),
  null,
);

console.log("ok: nc-board my-pending scope");
