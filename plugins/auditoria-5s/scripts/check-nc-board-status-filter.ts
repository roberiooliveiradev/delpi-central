/**
 * Regressão: filtro de status do board de NCs.
 * Em aberto = candidatos + open + in_progress; sem opções isoladas; default = pending.
 * Uso: node --experimental-strip-types scripts/check-nc-board-status-filter.ts
 */
import assert from "node:assert/strict";

import {
  NC_BOARD_STATUS_FILTER_OPTIONS,
  normalizeNcBoardStatusFilter,
} from "../src/constants/audit5s.ts";

const values = NC_BOARD_STATUS_FILTER_OPTIONS.map((item) => item.value);
const labels = NC_BOARD_STATUS_FILTER_OPTIONS.map((item) => item.label);

assert.ok(values.includes("pending"), "Em aberto (pending) obrigatório");
assert.ok(values.includes("cancelled"), "Cancelada obrigatória");
assert.ok(values.includes("closed"));
assert.ok(values.includes(""));
assert.ok(!values.includes("open"), "open não deve estar no filtro");
assert.ok(!values.includes("in_progress"), "in_progress não deve estar no filtro");
assert.ok(!labels.some((label) => /plano em registro/i.test(label)));
assert.ok(!labels.some((label) => /aguardando evidências/i.test(label)));

assert.equal(normalizeNcBoardStatusFilter("open"), "pending");
assert.equal(normalizeNcBoardStatusFilter("in_progress"), "pending");
assert.equal(normalizeNcBoardStatusFilter("cancelled"), "cancelled");
assert.equal(normalizeNcBoardStatusFilter("pending"), "pending");

console.log("ok: filtro status board NC (Em aberto cobre open+in_progress; Cancelada; default pending)");
