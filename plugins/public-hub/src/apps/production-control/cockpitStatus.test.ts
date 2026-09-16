import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { MachineLoadOperation } from "./api.ts";
import {
  hasExhaustedOperationBalance,
  isFinishedOperation,
  operationPendingQty,
  resolveStatus,
} from "./cockpitStatus.ts";

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

describe("cockpit operation balance", () => {
  it("P0: apontamento parcial (0,980 de 1,100) permanece Na fila, sem risco", () => {
    const row = operation({
      planned_qty: 1.1,
      operation_produced_qty: 0.98,
      operation_pending_qty: 0.12,
      pending_qty: 0.12,
      is_in_production: false,
      production_status: "started",
      appointment_count: 1,
      active_operator_name: "JOAO",
    });
    assert.equal(hasExhaustedOperationBalance(row), false);
    assert.equal(isFinishedOperation(row), false);
    assert.equal(resolveStatus(row).tone, "queued");
    assert.equal(resolveStatus(row).label, "Na fila");
    assert.match(resolveStatus(row).operatorNote ?? "", /JOAO/);
  });

  it("irmão: operação apontada por inteiro vira Já apontada mesmo com saldo no cabeçalho", () => {
    const row = operation({
      operation_produced_qty: 7.8,
      operation_pending_qty: 0,
      pending_qty: 6.3,
      is_in_production: false,
      production_status: "started",
    });
    assert.equal(operationPendingQty(row), 0);
    assert.equal(hasExhaustedOperationBalance(row), true);
    assert.equal(isFinishedOperation(row), true);
    assert.equal(resolveStatus(row).label, "Já apontada");
    assert.equal(resolveStatus(row).tone, "done");
  });

  it("irmão: operação sem apontamento usa o saldo da bancada, não o do cabeçalho", () => {
    const row = operation({
      operation_code: "03",
      operation_produced_qty: 0,
      operation_pending_qty: 7.8,
      is_in_production: false,
      production_status: "not_started",
      active_operator_name: null,
    });
    assert.equal(operationPendingQty(row), 7.8);
    assert.equal(hasExhaustedOperationBalance(row), false);
    assert.equal(resolveStatus(row).label, "Na fila");
  });

  it("parcial em coletor aberto e saldo > 0 permanece Em produção", () => {
    const row = operation({ operation_produced_qty: 3, operation_pending_qty: 4.8 });
    assert.equal(operationPendingQty(row), 4.8);
    assert.equal(resolveStatus(row).label, "Em produção");
  });

  it("snapshot antigo sem campo da operação cai no saldo do cabeçalho", () => {
    const row = operation();
    assert.equal(row.operation_pending_qty, undefined);
    assert.equal(operationPendingQty(row), 6.3);
    assert.equal(resolveStatus(row).label, "Em produção");
  });

  it("negativo: operação sem apontamento e OP aberta não vira Já apontada", () => {
    const row = operation({
      is_in_production: false,
      production_status: "not_started",
      operation_produced_qty: 0,
      operation_pending_qty: 7.8,
      active_operator_name: null,
    });
    assert.equal(resolveStatus(row).label, "Na fila");
    assert.equal(isFinishedOperation(row), false);
  });
});
