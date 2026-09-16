import { describe, expect, it } from "vitest";

import {
  filterActiveMachineLoadOperations,
  hasExhaustedMachineLoadBalance,
  isMachineLoadFinishedOperation,
  isMachineLoadStarted,
  machineLoadRowModifierClass,
  machineLoadStatusBadge,
  machineLoadStatusRank,
  resolveMachineLoadQueueStatus,
} from "./machineLoadStatus";

describe("machineLoadStatus", () => {
  it("marca em produção com verde", () => {
    expect(machineLoadStatusBadge("in_progress").variant).toBe("success");
  });

  it("distingue já apontada de não iniciada", () => {
    expect(machineLoadStatusBadge("started").variant).toBe("info");
    expect(machineLoadStatusBadge("not_started").variant).toBe("neutral");
  });

  it("cai em não iniciada quando o status vem vazio ou desconhecido", () => {
    expect(machineLoadStatusBadge(null).label).toBe(machineLoadStatusBadge("not_started").label);
    expect(machineLoadStatusBadge("running").variant).toBe("neutral");
  });

  it("ordena em produção antes de já apontada e não iniciada", () => {
    const ordered = ["not_started", "in_progress", "started"].sort(
      (a, b) => machineLoadStatusRank(a) - machineLoadStatusRank(b),
    );
    expect(ordered).toEqual(["in_progress", "started", "not_started"]);
  });

  it("P0: apontamento parcial não tacha nem some no Limpar fila", () => {
    const partial = {
      production_status: "started" as const,
      is_in_production: false,
      operation_pending_qty: 0.12,
      pending_qty: 0.12,
    };
    expect(isMachineLoadStarted("started")).toBe(true);
    expect(hasExhaustedMachineLoadBalance(partial)).toBe(false);
    expect(isMachineLoadFinishedOperation(partial)).toBe(false);
    expect(resolveMachineLoadQueueStatus(partial)).toBe("not_started");
    expect(machineLoadRowModifierClass(partial)).toBeUndefined();
  });

  it("irmão: saldo esgotado tacha e conta como finalizada", () => {
    const done = {
      production_status: "started" as const,
      is_in_production: false,
      operation_pending_qty: 0,
      pending_qty: 1.1,
    };
    expect(isMachineLoadFinishedOperation(done)).toBe(true);
    expect(resolveMachineLoadQueueStatus(done)).toBe("started");
    expect(machineLoadRowModifierClass(done)).toBe("ppc-load__row--started");
  });

  it("em produção com saldo continua com linha verde", () => {
    expect(
      machineLoadRowModifierClass({
        production_status: "started",
        is_in_production: true,
        operation_pending_qty: 0.5,
        pending_qty: 0.5,
      }),
    ).toBe("ppc-load__row--running");
  });

  it("filtra só operações com saldo esgotado, mantendo parciais e em produção", () => {
    const rows = [
      {
        production_status: "started" as const,
        is_in_production: false,
        operation_pending_qty: 0,
        pending_qty: 0,
      },
      {
        production_status: "in_progress" as const,
        is_in_production: true,
        operation_pending_qty: 2,
        pending_qty: 2,
      },
      {
        production_status: "not_started" as const,
        is_in_production: false,
        operation_pending_qty: 1.1,
        pending_qty: 1.1,
      },
      {
        production_status: "started" as const,
        is_in_production: false,
        operation_pending_qty: 0.12,
        pending_qty: 0.12,
      },
    ];
    expect(filterActiveMachineLoadOperations(rows)).toEqual([rows[1], rows[2], rows[3]]);
    expect(isMachineLoadFinishedOperation(rows[0]!)).toBe(true);
    expect(isMachineLoadFinishedOperation(rows[3]!)).toBe(false);
  });
});
