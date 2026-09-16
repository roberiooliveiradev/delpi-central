import { describe, expect, it } from "vitest";

import type { MachineLoadLiveStatusPayload } from "../types";
import { applyMachineLoadLiveStatus } from "./machineLoadLiveStatus";
import { makeMachineLoadPayload } from "./machineLoadTestPayload";

function makeLiveStatus(
  items: MachineLoadLiveStatusPayload["items"],
): MachineLoadLiveStatusPayload {
  return {
    branch: "01",
    as_of: "2026-08-20T08:30:00Z",
    summary: { operation_count: 3, in_production_count: items.length },
    items,
  };
}

describe("applyMachineLoadLiveStatus", () => {
  it("aplica o status do chão de fábrica e recalcula os contadores das abas", () => {
    const payload = makeMachineLoadPayload();

    const merged = applyMachineLoadLiveStatus(
      payload,
      makeLiveStatus([
        {
          production_order: "24640401010",
          operation_code: "03",
          production_status: "in_progress",
          is_in_production: true,
          active_operator_name: "SILVANA ANDRADE DOS SANTOS",
          appointment_count: 3,
        },
      ]),
    );

    const running = merged.operations?.find((item) => item.production_order === "24640401010");
    expect(running?.is_in_production).toBe(true);
    expect(running?.active_operator_name).toBe("SILVANA ANDRADE DOS SANTOS");
    expect(merged.summary.in_production_count).toBe(1);
    expect(merged.work_centers[0].in_production_count).toBe(0);
    expect(merged.work_centers[1].in_production_count).toBe(1);
  });

  it("operação fora do status vivo mantém o valor congelado do snapshot", () => {
    const payload = makeMachineLoadPayload();

    const merged = applyMachineLoadLiveStatus(
      payload,
      makeLiveStatus([
        {
          production_order: "24640401002",
          operation_code: "03",
          is_in_production: true,
          production_status: "in_progress",
        },
      ]),
    );

    const untouched = merged.operations?.find((item) => item.production_order === "24640401003");
    expect(untouched?.is_in_production).toBe(false);
    expect(untouched?.production_status).toBe("not_started");
    expect(merged.summary.in_production_count).toBe(1);
  });

  it("status igual ao que já está na tela não recria a fila", () => {
    const payload = makeMachineLoadPayload();

    const merged = applyMachineLoadLiveStatus(
      payload,
      makeLiveStatus([
        {
          production_order: "24640401002",
          operation_code: "03",
          production_status: "not_started",
          is_in_production: false,
        },
      ]),
    );

    expect(merged).toBe(payload);
  });

  it("sem itens de status a fila congelada continua como está", () => {
    const payload = makeMachineLoadPayload();
    expect(applyMachineLoadLiveStatus(payload, makeLiveStatus([]))).toBe(payload);
  });

  it("aplica o saldo da própria operação sem mexer no saldo do cabeçalho", () => {
    const payload = makeMachineLoadPayload();

    const merged = applyMachineLoadLiveStatus(
      payload,
      makeLiveStatus([
        {
          production_order: "24640401010",
          operation_code: "03",
          production_status: "started",
          is_in_production: false,
          operation_produced_qty: 7.1,
          operation_pending_qty: 0,
        },
      ]),
    );

    const item = merged.operations?.find((row) => row.production_order === "24640401010");
    expect(item?.pending_qty).toBe(7.1);
    expect(item?.operation_produced_qty).toBe(7.1);
    expect(item?.operation_pending_qty).toBe(0);
    expect(item?.is_in_production).toBe(false);
  });
});
