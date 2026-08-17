/**
 * Regressão: progresso do board NC = barra % pelos campos obrigatórios + evidências.
 * Uso: node --experimental-strip-types scripts/check-nc-board-progress.ts
 */
import assert from "node:assert/strict";

import {
  computeNcBoardProgressPct,
  NC_BOARD_PROGRESS_STEP_COUNT,
} from "../src/utils/ncBoardProgress.ts";

assert.equal(NC_BOARD_PROGRESS_STEP_COUNT, 7);

const empty = {
  status: "open",
  description: null,
  root_cause: null,
  corrective_action: null,
  responsible_name: null,
  due_date: null,
  has_before_evidence: false,
  has_after_evidence: false,
};

assert.equal(computeNcBoardProgressPct(empty), 0);

const planOnly = {
  ...empty,
  description: "NC encontrada no posto",
  root_cause: "Falta de padrão",
  corrective_action: "Padronizar e treinar",
  responsible_name: "Ana",
  due_date: "2026-08-20",
};
assert.equal(computeNcBoardProgressPct(planOnly), Math.round((5 / 7) * 100));

const withEvidence = {
  ...planOnly,
  status: "in_progress",
  has_before_evidence: true,
  has_after_evidence: true,
};
assert.equal(computeNcBoardProgressPct(withEvidence), 100);

assert.equal(
  computeNcBoardProgressPct({ ...empty, status: "closed" }),
  100,
  "closed sempre 100%",
);

assert.equal(
  computeNcBoardProgressPct({
    ...empty,
    description: "abc",
  }),
  Math.round((1 / 7) * 100),
);

console.log("ok: progresso board NC (barra % por campos obrigatórios)");
