import { describe, expect, it } from "vitest";

import {
  formatByRoleSummary,
  formatPlacementMeta,
  resolveOperatorSurface,
} from "./operatorDisplay";
import type { OperatorDeviceItem, OperatorPlacement } from "../types/operator";

describe("operatorDisplay", () => {
  it("summarizes roles for hub card meta", () => {
    expect(formatByRoleSummary({ pulse_counter: 1, process_gauge: 2 })).toBe("1 cont · 2 sens");
    expect(
      formatPlacementMeta({
        placementKey: "wc:01:CT-53",
        placementLabel: "CT-53",
        anchorType: "work_center",
        branch: "01",
        deviceCount: 3,
        onlineCount: 2,
        byRole: { pulse_counter: 1, process_gauge: 2 },
        primaryMetricPreview: null,
      } satisfies OperatorPlacement),
    ).toBe("1 cont · 2 sens · 2 online");
  });

  it("routes counter vs gauge surfaces from capabilities", () => {
    const counter = {
      capabilities: { metrics: ["counter"], commands: ["reset"], operatorSurface: "counter_pad" },
    } as OperatorDeviceItem;
    const gauge = {
      capabilities: { metrics: ["rpm"], commands: [], operatorSurface: "gauge_readout" },
    } as OperatorDeviceItem;

    expect(resolveOperatorSurface(counter)).toBe("counter_pad");
    expect(resolveOperatorSurface(gauge)).toBe("gauge_readout");
  });
});
