/**
 * Smoke: coluna Status do board NC honra workflow terminal (cancelada/concluída)
 * antes do SLA («Em dia» / atraso).
 * npm run check:nc-board-row-status
 */
import assert from "node:assert/strict";

import type { NcBoardItem } from "../src/types/ncManagement.ts";
import {
  canAddNcBoardNotes,
  canUpdateNcBoardItem,
  isNcBoardViewOnly,
} from "../src/constants/audit5s.ts";
import { resolveNcBoardRowStatus } from "../src/utils/ncDueSla.ts";

function boardItem(overrides: Partial<NcBoardItem>): NcBoardItem {
  return {
    id: "nc-1",
    audit_id: "audit-1",
    response_id: "resp-1",
    description: "Achado",
    root_cause: "Causa",
    corrective_action: "Ação",
    responsible_name: "Ana",
    due_date: "2026-08-01",
    priority: "medium",
    status: "open",
    is_registered: true,
    audit_code: "A5S-1",
    audit_date: "2026-08-01",
    area_name: "Produção",
    branch_code: "01",
    shift: "TURNO_1",
    criterion_code: "C1",
    criterion_description: "Critério",
    senso_order: 1,
    senso_name: "Utilização",
    plan_started: true,
    workflow_step: 2,
    due_sla_level: "ok",
    days_until_due: 10,
    has_before_evidence: false,
    has_after_evidence: false,
    last_action_at: null,
    ...overrides,
  };
}

const cancelled = resolveNcBoardRowStatus(
  boardItem({
    status: "cancelled",
    due_sla_level: "none",
    days_until_due: null,
  }),
);
assert.equal(cancelled.label, "Cancelada");
assert.equal(cancelled.tone, "cancelled");

const cancelledWithStaleSla = resolveNcBoardRowStatus(
  boardItem({
    status: "cancelled",
    due_sla_level: "overdue",
    days_until_due: -4,
  }),
);
assert.equal(cancelledWithStaleSla.label, "Cancelada");
assert.notEqual(cancelledWithStaleSla.label, "Em dia");
assert.notEqual(cancelledWithStaleSla.label, "Atrasado");

const closed = resolveNcBoardRowStatus(boardItem({ status: "closed" }));
assert.equal(closed.label, "Concluída");

const onTrack = resolveNcBoardRowStatus(
  boardItem({ status: "in_progress", due_sla_level: "due_soon", days_until_due: 1 }),
);
assert.equal(onTrack.label, "Em dia");

assert.equal(isNcBoardViewOnly("cancelled"), true);
assert.equal(canUpdateNcBoardItem("cancelled"), false);
assert.equal(canAddNcBoardNotes("cancelled", true), false);
assert.equal(isNcBoardViewOnly("closed"), false);
assert.equal(canUpdateNcBoardItem("closed"), true);
assert.equal(canAddNcBoardNotes("closed", true), true);
assert.equal(canAddNcBoardNotes("open", false), false);

console.log("ok: nc-board row status cancelled");
