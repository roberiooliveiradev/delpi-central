import { describe, expect, it } from "vitest";

import type { MachineLoadLocateStop } from "../types";
import {
  conjuntoKeyFromOrder,
  locateJourneyProgress,
  locateStopStatusLabel,
  locateStopStatusTone,
  machineLoadLocateRowKey,
} from "./machineLoadLocate";

function stop(partial: Partial<MachineLoadLocateStop>): MachineLoadLocateStop {
  return {
    work_center: "CT-01A",
    work_center_name: "CORTE",
    production_order: "10808301005",
    operation_code: "01",
    operation_description: "CORTAR",
    product_code: "50233616",
    product_description: "x",
    pa_product_code: "90262910",
    pa_due_date: "2026-08-24",
    scheduled_date: "2026-08-19",
    scheduled_start_time: "06:02",
    pending_qty: 1,
    operation_pending_qty: 1,
    unit: "MI",
    tool: "23-014",
    execution_status: null,
    execution_integrity_status: null,
    execution_started_at: null,
    queue_position: 1,
    queue_size: 10,
    ...partial,
  };
}

describe("machineLoadLocate", () => {
  it("extracts C2_NUM as conjunto key from full OP", () => {
    expect(conjuntoKeyFromOrder("10840401003")).toBe("108404");
    expect(conjuntoKeyFromOrder("108404")).toBe("108404");
    expect(conjuntoKeyFromOrder("10840")).toBeNull();
  });

  it("builds a stable row key for highlight", () => {
    expect(machineLoadLocateRowKey(stop({}))).toBe("CT-01A::10808301005::01");
    // Mesmo OP+operação em outro CT não colide nem herda o destaque da parada.
    expect(machineLoadLocateRowKey(stop({ work_center: "CT-02" }))).toBe(
      "CT-02::10808301005::01",
    );
  });

  it("maps journey progress tones by cockpit execution", () => {
    const steps = locateJourneyProgress([
      stop({ execution_status: null, operation_pending_qty: 0 }),
      stop({ execution_status: "producing" }),
      stop({ execution_status: "stopped" }),
      stop({ execution_status: "paused" }),
      stop({ execution_status: "unknown" }),
      stop({ execution_status: null }),
    ]);
    expect(steps.map((step) => step.tone)).toEqual([
      "done",
      "running",
      "stopped",
      "paused",
      "unknown",
      "queued",
    ]);
  });

  it("run stopped nunca aparece como produzindo", () => {
    const stopped = stop({ execution_status: "stopped" });
    expect(locateStopStatusTone(stopped)).toBe("stopped");
    expect(locateStopStatusLabel(stopped)).toBe("Parada");
  });

  it("leitura inconsistente vira estado não confirmado, não ausência", () => {
    const unknown = stop({ execution_status: "unknown", execution_integrity_status: "inconsistent" });
    expect(locateStopStatusTone(unknown)).toBe("unknown");
    expect(locateStopStatusLabel(unknown)).toBe("Estado não confirmado");
  });

  it("sem run: saldo esgotado = já apontada; saldo aberto = na fila", () => {
    const done = stop({ execution_status: null, operation_pending_qty: 0 });
    expect(locateStopStatusTone(done)).toBe("done");
    expect(locateStopStatusLabel(done)).toBe("Já apontada");

    const queued = stop({ execution_status: null });
    expect(locateStopStatusTone(queued)).toBe("queued");
    expect(locateStopStatusLabel(queued)).toBe("Não iniciada");
  });
});
