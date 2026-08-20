import { describe, expect, it } from "vitest";

import type { MachineLoadLocateStop } from "../types";
import {
  conjuntoKeyFromOrder,
  locateJourneyProgress,
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
    unit: "MI",
    tool: "23-014",
    production_status: "not_started",
    is_in_production: false,
    production_started_time: null,
    active_operator_name: null,
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
    expect(machineLoadLocateRowKey(stop({}))).toBe("10808301005::01");
  });

  it("maps journey progress tones in order", () => {
    const steps = locateJourneyProgress([
      stop({ production_status: "started" }),
      stop({ is_in_production: true, production_status: "in_progress" }),
      stop({ production_status: "not_started" }),
    ]);
    expect(steps.map((step) => step.tone)).toEqual(["done", "running", "queued"]);
  });

  it("prefers live in-production over frozen status", () => {
    expect(locateStopStatusTone("started", true)).toBe("running");
  });
});
