import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { MachineLoadOperation } from "./api.ts";
import { operationPendingQty, resolveStatus } from "./cockpitStatus.ts";

function operation(overrides: Partial<MachineLoadOperation> = {}): MachineLoadOperation {
  return {
    work_center: "CT-01A",
    work_center_name: "CORTE",
    scheduled_date: "2026-09-16",
    scheduled_start_time: "05:00",
    scheduled_end_date: null,
    scheduled_end_time: null,
    production_order: "10964501004",
    operation_code: "01",
    operation_description: "CORTAR",
    tool: "23-B31",
    resource: null,
    product_code: "50320064",
    product_description: "CF",
    unit: "MI",
    planned_qty: 7.8,
    produced_qty: 1.5,
    pending_qty: 6.3,
    pa_product_code: "90300080",
    pa_product_description: "CHICOTE",
    pa_due_date: "2026-09-20",
    due_date: "2026-09-20",
    production_status: "in_progress",
    is_in_production: true,
    production_started_date: "2026-09-16",
    production_started_time: "05:12:44",
    active_operator_name: "CARLA",
    active_operator_count: 1,
    appointment_count: 4,
    last_appointment_date: "2026-09-16",
    ...overrides,
  };
}

describe("cockpit operation status (fila open-only)", () => {
  it("P0: operação sem run MES permanece Na fila", () => {
    const row = operation({
      is_in_production: false,
      production_status: "started",
      appointment_count: 1,
      active_operator_name: "JOAO",
    });
    assert.equal(resolveStatus(row).tone, "queued");
    assert.equal(resolveStatus(row).label, "Na fila");
    assert.match(resolveStatus(row).operatorNote ?? "", /JOAO/);
  });

  it("irmão: operação sem apontamento exibe Na fila", () => {
    const row = operation({
      operation_code: "03",
      is_in_production: false,
      production_status: "not_started",
      active_operator_name: null,
    });
    assert.equal(resolveStatus(row).label, "Na fila");
    assert.equal(resolveStatus(row).tone, "queued");
  });

  it("parcial em coletor aberto permanece Em produção", () => {
    const row = operation({ operation_produced_qty: 3, operation_pending_qty: 4.8 });
    assert.equal(operationPendingQty(row), 4.8);
    assert.equal(resolveStatus(row).label, "Em produção");
    assert.equal(resolveStatus(row).tone, "running");
  });

  it("snapshot antigo sem campo da operação cai no saldo do cabeçalho", () => {
    const row = operation();
    assert.equal(row.operation_pending_qty, undefined);
    assert.equal(operationPendingQty(row), 6.3);
    assert.equal(resolveStatus(row).label, "Em produção");
  });
});
