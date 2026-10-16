import { describe, expect, it } from "vitest";

import type {
  MachineLoadBalancesPayload,
  MachineLoadCockpitStatusItem,
  MachineLoadCockpitStatusPayload,
} from "../types";
import {
  applyMachineLoadBalances,
  applyMachineLoadCockpitStatus,
} from "./machineLoadCockpitStatus";
import { makeMachineLoadOperation, makeMachineLoadPayload } from "./machineLoadTestPayload";

function makeRun(partial: Partial<MachineLoadCockpitStatusItem>): MachineLoadCockpitStatusItem {
  return {
    work_center: "CT-01A",
    production_order: "24640401002",
    operation_code: "03",
    run_status: "running",
    operational_state: "producing",
    display_status: "producing",
    integrity_status: "complete",
    started_at: "2026-08-20T08:15:00Z",
    ...partial,
  };
}

function makeCockpitStatus(
  items: MachineLoadCockpitStatusItem[],
): MachineLoadCockpitStatusPayload {
  return {
    branch: "01",
    source: "cockpit",
    as_of: "2026-08-20T08:30:00Z",
    summary: {
      active_runs: items.length,
      producing: items.filter((item) => item.display_status === "producing").length,
      stopped: items.filter((item) => item.display_status === "stopped").length,
      paused: items.filter((item) => item.display_status === "paused").length,
      unknown: items.filter((item) => item.display_status === "unknown").length,
    },
    items,
  };
}

function makeBalances(items: MachineLoadBalancesPayload["items"]): MachineLoadBalancesPayload {
  return {
    branch: "01",
    as_of: "2026-08-20T08:30:00Z",
    summary: { item_count: items.length },
    items,
  };
}

describe("applyMachineLoadCockpitStatus", () => {
  it("run produzindo marca a operação e recalcula os contadores das abas", () => {
    const merged = applyMachineLoadCockpitStatus(
      makeMachineLoadPayload(),
      makeCockpitStatus([
        makeRun({ production_order: "24640401010", work_center: "CT-02" }),
      ]),
    );

    const running = merged.operations?.find((item) => item.production_order === "24640401010");
    expect(running?.execution_status).toBe("producing");
    expect(running?.execution_started_at).toBe("2026-08-20T08:15:00Z");
    expect(merged.summary.in_production_count).toBe(1);
    expect(merged.work_centers[0].in_production_count).toBe(0);
    expect(merged.work_centers[1].in_production_count).toBe(1);
  });

  it("operação ausente do snapshot não tem run — não herda execução", () => {
    const merged = applyMachineLoadCockpitStatus(
      makeMachineLoadPayload(),
      makeCockpitStatus([makeRun({})]),
    );

    const absent = merged.operations?.find((item) => item.production_order === "24640401003");
    expect(absent?.execution_status).toBeNull();
    expect(merged.summary.in_production_count).toBe(1);
  });

  it("items=[] limpa execução inclusive de snapshot com HZA congelada", () => {
    const stale = makeMachineLoadPayload({
      operations: [
        makeMachineLoadOperation({
          production_order: "24640401002",
          production_status: "in_progress",
          is_in_production: true,
          active_operator_name: "SILVANA ANDRADE DOS SANTOS",
          execution_status: "producing",
          execution_integrity_status: "complete",
          execution_started_at: "2026-08-20T07:00:00Z",
        }),
      ],
      summary: {
        work_center_count: 2,
        operation_count: 1,
        order_count: 1,
        in_production_count: 1,
      },
    });

    const merged = applyMachineLoadCockpitStatus(stale, makeCockpitStatus([]));

    expect(merged.operations?.[0]?.execution_status).toBeNull();
    expect(merged.summary.in_production_count).toBe(0);
    expect(merged.work_centers[0].in_production_count).toBe(0);
  });

  it("stopped, paused e unknown não inflam o contador de produção", () => {
    const merged = applyMachineLoadCockpitStatus(
      makeMachineLoadPayload(),
      makeCockpitStatus([
        makeRun({ display_status: "stopped", run_status: "running", operational_state: "stopped" }),
        makeRun({
          production_order: "24640401003",
          display_status: "paused",
          run_status: "paused",
          operational_state: "stopped",
        }),
        makeRun({
          production_order: "24640401010",
          work_center: "CT-02",
          display_status: "unknown",
          run_status: "running",
          operational_state: "producing",
          integrity_status: "inconsistent",
        }),
      ]),
    );

    expect(merged.summary.in_production_count).toBe(0);
    const byOrder = Object.fromEntries(
      (merged.operations ?? []).map((item) => [item.production_order, item.execution_status]),
    );
    expect(byOrder["24640401002"]).toBe("stopped");
    expect(byOrder["24640401003"]).toBe("paused");
    expect(byOrder["24640401010"]).toBe("unknown");
  });

  it("mesmo estado não recria a fila — referência preservada", () => {
    const payload = applyMachineLoadCockpitStatus(
      makeMachineLoadPayload(),
      makeCockpitStatus([makeRun({})]),
    );
    expect(applyMachineLoadCockpitStatus(payload, makeCockpitStatus([makeRun({})]))).toBe(payload);
  });

  it("run em centro diferente do exibido conta só na aba dele", () => {
    const merged = applyMachineLoadCockpitStatus(
      makeMachineLoadPayload(),
      makeCockpitStatus([makeRun({ production_order: "24640401010", work_center: "CT-02" })]),
    );
    expect(merged.work_centers[0].in_production_count).toBe(0);
    expect(merged.work_centers[1].in_production_count).toBe(1);
    // A ordem da fila não muda: é projeção, não sequenciamento.
    expect(merged.operations?.map((item) => item.production_order)).toEqual([
      "24640401002",
      "24640401003",
      "24640401010",
    ]);
  });

  it("mesmo OP/operação em dois centros: cada bancada recebe só o próprio run", () => {
    const payload = makeMachineLoadPayload({
      operations: [
        makeMachineLoadOperation({
          work_center: "CT-01A",
          production_order: "12345601001",
          operation_code: "10",
        }),
        makeMachineLoadOperation({
          work_center: "CT-02",
          work_center_name: "APLICAÇÃO DE TERMINAIS",
          production_order: "12345601001",
          operation_code: "10",
        }),
      ],
    });
    // Ordem invertida de propósito: o resultado não pode depender da ordem dos itens.
    const merged = applyMachineLoadCockpitStatus(
      payload,
      makeCockpitStatus([
        makeRun({
          work_center: "CT-02",
          production_order: "12345601001",
          operation_code: "10",
          display_status: "stopped",
          operational_state: "stopped",
        }),
        makeRun({
          work_center: "CT-01A",
          production_order: "12345601001",
          operation_code: "10",
        }),
      ]),
    );

    const byCenter = Object.fromEntries(
      (merged.operations ?? []).map((item) => [item.work_center, item.execution_status]),
    );
    expect(byCenter["CT-01A"]).toBe("producing");
    expect(byCenter["CT-02"]).toBe("stopped");
    expect(merged.summary.in_production_count).toBe(1);
    expect(merged.work_centers[0].in_production_count).toBe(1);
    expect(merged.work_centers[1].in_production_count).toBe(0);
  });

  it("transferência: run na bancada de origem não produz na bancada nova", () => {
    // Fila WORKING já mostra a OP/operação só no CT-02 (transferida);
    // o run continua registrado no CT-01A — execução não migra junto.
    const merged = applyMachineLoadCockpitStatus(
      makeMachineLoadPayload(),
      makeCockpitStatus([
        makeRun({
          work_center: "CT-01A",
          production_order: "24640401010",
          operation_code: "03",
        }),
      ]),
    );

    const moved = merged.operations?.find(
      (item) => item.production_order === "24640401010" && item.work_center === "CT-02",
    );
    expect(moved?.execution_status).toBeNull();
    expect(merged.summary.in_production_count).toBe(0);
    expect(merged.work_centers[1].in_production_count).toBe(0);
  });

  it("run em bancada sem linha na fila não contamina OP/operação igual de outro CT", () => {
    const merged = applyMachineLoadCockpitStatus(
      makeMachineLoadPayload(),
      makeCockpitStatus([
        makeRun({
          work_center: "CT-99",
          production_order: "24640401002",
          operation_code: "03",
          display_status: "paused",
          run_status: "paused",
          operational_state: "stopped",
        }),
      ]),
    );

    expect(merged.operations?.[0]?.execution_status).toBeNull();
    expect(merged.summary.in_production_count).toBe(0);
  });

  it("resposta de outra filial não projeta estado nesta fila", () => {
    const payload = makeMachineLoadPayload();
    const merged = applyMachineLoadCockpitStatus(payload, {
      ...makeCockpitStatus([makeRun({})]),
      branch: "02",
    });

    expect(merged).toBe(payload);
    expect(merged.operations?.[0]?.execution_status).toBeNull();
  });
});

describe("applyMachineLoadBalances", () => {
  it("atualiza produzido e saldo da própria operação", () => {
    const merged = applyMachineLoadBalances(
      makeMachineLoadPayload(),
      makeBalances([
        {
          production_order: "24640401002",
          operation_code: "03",
          operation_produced_qty: 3.5,
          operation_pending_qty: 3.6,
        },
      ]),
    );

    const item = merged.operations?.find((row) => row.production_order === "24640401002");
    expect(item?.operation_produced_qty).toBe(3.5);
    expect(item?.operation_pending_qty).toBe(3.6);
    // Saldo do cabeçalho da OP não é tocado pelo lote da operação.
    expect(item?.pending_qty).toBe(7.1);
  });

  it("saldo esgotado aplica zero; operação ausente mantém último valor", () => {
    const merged = applyMachineLoadBalances(
      makeMachineLoadPayload(),
      makeBalances([
        {
          production_order: "24640401002",
          operation_code: "03",
          operation_produced_qty: 7.1,
          operation_pending_qty: 0,
        },
      ]),
    );

    const done = merged.operations?.find((row) => row.production_order === "24640401002");
    expect(done?.operation_pending_qty).toBe(0);
    const untouched = merged.operations?.find((row) => row.production_order === "24640401003");
    expect(untouched?.operation_pending_qty).toBeUndefined();
  });

  it("não toca o estado de execução nem a ordem da fila", () => {
    const payload = applyMachineLoadCockpitStatus(
      makeMachineLoadPayload(),
      makeCockpitStatus([makeRun({})]),
    );
    const merged = applyMachineLoadBalances(
      payload,
      makeBalances([
        {
          production_order: "24640401002",
          operation_code: "03",
          operation_produced_qty: 1,
          operation_pending_qty: 6.1,
        },
      ]),
    );

    expect(merged.operations?.[0]?.execution_status).toBe("producing");
    expect(merged.operations?.map((item) => item.production_order)).toEqual([
      "24640401002",
      "24640401003",
      "24640401010",
    ]);
  });
});
