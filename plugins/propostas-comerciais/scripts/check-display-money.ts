/**
 * Moeda só no rótulo: células não carregam R$/US$.
 * Uso: node --experimental-strip-types scripts/check-display-money.ts
 */
import assert from "node:assert/strict";

import { displayMoneyAmount } from "../src/utils/format.ts";

assert.equal(displayMoneyAmount("R$ 374,13"), "374,13");
assert.equal(displayMoneyAmount("R$374,13"), "374,13");
assert.equal(displayMoneyAmount("US$ 12,50"), "12,50");
assert.equal(displayMoneyAmount("374,13"), "374,13");
assert.equal(displayMoneyAmount(null), "—");

console.log("check-display-money: ok");
