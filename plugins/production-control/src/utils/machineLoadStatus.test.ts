import { describe, expect, it } from "vitest";

import {
  filterActiveMachineLoadOperations,
  hasExhaustedMachineLoadBalance,
  isMachineLoadFinishedOperation,
  machineLoadRowModifierClass,
  machineLoadStatusBadge,
  machineLoadStatusRank,
  resolveMachineLoadQueueStatus,
} from "./machineLoadStatus";

describe("machineLoadStatus", () => {
  it("produzindo marca com verde e lidera a ordenação", () => {
    expect(machineLoadStatusBadge("in_progress").variant).toBe("success");
    expect(machineLoadStatusBadge("in_progress").label).toBe("Produzindo");
  });

  it("estados do cockpit têm badges próprios", () => {
    expect(machineLoadStatusBadge("stopped").label).toBe("Parada");
    expect(machineLoadStatusBadge("stopped").variant).toBe("warning");
    expect(machineLoadStatusBadge("paused").label).toBe("Pausada");
    expect(machineLoadStatusBadge("paused").variant).toBe("info");
    expect(machineLoadStatusBadge("unconfirmed").label).toBe("Estado não confirmado");
    expect(machineLoadStatusBadge("unconfirmed").variant).toBe("warning");
  });

  it("distingue já apontada de não iniciada", () => {
    expect(machineLoadStatusBadge("started").variant).toBe("info");
    expect(machineLoadStatusBadge("not_started").variant).toBe("neutral");
  });

  it("cai em não iniciada quando o status vem vazio ou desconhecido", () => {
    expect(machineLoadStatusBadge(null).label).toBe(machineLoadStatusBadge("not_started").label);
    expect(machineLoadStatusBadge("running").variant).toBe("neutral");
  });

  it("ordena produzindo antes dos demais estados", () => {
    const ordered = ["not_started", "in_progress", "started", "paused", "stopped", "unconfirmed"].sort(
      (a, b) => machineLoadStatusRank(a) - machineLoadStatusRank(b),
    );
    expect(ordered[0]).toBe("in_progress");
  });

  it("P0: apontamento parcial sem run não tacha nem some no Limpar fila", () => {
    const partial = {
      operation_pending_qty: 0.12,
      pending_qty: 0.12,
      execution_status: null,
    };
    expect(hasExhaustedMachineLoadBalance(partial)).toBe(false);
    expect(isMachineLoadFinishedOperation(partial)).toBe(false);
    expect(resolveMachineLoadQueueStatus(partial)).toBe("not_started");
    expect(machineLoadRowModifierClass(partial)).toBeUndefined();
  });

  it("irmão: saldo esgotado sem run tacha e conta como finalizada", () => {
    const done = {
      operation_pending_qty: 0,
      pending_qty: 1.1,
      execution_status: null,
    };
    expect(isMachineLoadFinishedOperation(done)).toBe(true);
    expect(resolveMachineLoadQueueStatus(done)).toBe("started");
    expect(machineLoadRowModifierClass(done)).toBe("ppc-load__row--started");
  });

  it("negativo: HZA congelada no snapshot não marca produção — só o cockpit decide", () => {
    // production_status/is_in_production ficaram no snapshot antigo: ignorados.
    const staleHza = {
      operation_pending_qty: 5,
      pending_qty: 5,
      execution_status: null,
    };
    expect(resolveMachineLoadQueueStatus(staleHza)).toBe("not_started");
    expect(machineLoadRowModifierClass(staleHza)).toBeUndefined();
  });

  it("produzindo com saldo esgotado continua visível e destacada", () => {
    const running = {
      operation_pending_qty: 0,
      pending_qty: 0,
      execution_status: "producing",
    };
    expect(resolveMachineLoadQueueStatus(running)).toBe("in_progress");
    expect(isMachineLoadFinishedOperation(running)).toBe(false);
    expect(machineLoadRowModifierClass(running)).toBe("ppc-load__row--running");
  });

  it("run aberto com saldo zero não é ocultado pelo filtro de finalizadas", () => {
    const openRunZeroBalance = {
      operation_pending_qty: 0,
      pending_qty: 0,
      execution_status: "stopped",
    };
    expect(isMachineLoadFinishedOperation(openRunZeroBalance)).toBe(false);
    expect(filterActiveMachineLoadOperations([openRunZeroBalance])).toHaveLength(1);
  });

  it("stopped, paused e unknown viram classes de linha próprias", () => {
    const base = { operation_pending_qty: 5, pending_qty: 5 };
    expect(machineLoadRowModifierClass({ ...base, execution_status: "stopped" })).toBe(
      "ppc-load__row--stopped",
    );
    expect(machineLoadRowModifierClass({ ...base, execution_status: "paused" })).toBe(
      "ppc-load__row--paused",
    );
    expect(machineLoadRowModifierClass({ ...base, execution_status: "unknown" })).toBe(
      "ppc-load__row--unconfirmed",
    );
  });

  it("filtra só esgotadas sem run, mantendo parciais e execuções abertas", () => {
    const rows = [
      { operation_pending_qty: 0, pending_qty: 0, execution_status: null },
      { operation_pending_qty: 2, pending_qty: 2, execution_status: "producing" },
      { operation_pending_qty: 1.1, pending_qty: 1.1, execution_status: null },
      { operation_pending_qty: 0.12, pending_qty: 0.12, execution_status: null },
      { operation_pending_qty: 0, pending_qty: 0, execution_status: "paused" },
    ];
    expect(filterActiveMachineLoadOperations(rows)).toEqual([rows[1], rows[2], rows[3], rows[4]]);
    expect(isMachineLoadFinishedOperation(rows[0]!)).toBe(true);
    expect(isMachineLoadFinishedOperation(rows[3]!)).toBe(false);
  });
});
