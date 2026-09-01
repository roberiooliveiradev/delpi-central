import { describe, expect, it } from "vitest";

import {
  parseProductionPulseRoute,
  productionPulseDeviceNewPath,
} from "./routes";

describe("parseProductionPulseRoute", () => {
  it("maps panel root", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse").kind).toBe("panel");
  });

  it("maps operator subtree", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/operator").kind).toBe("operator");
    expect(parseProductionPulseRoute("/apps/production-pulse/operator/placements/wc:01:CT-1").kind).toBe(
      "operator",
    );
  });

  it("maps device create and edit routes", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/new", "?branch=02")).toEqual({
      kind: "deviceNew",
      branch: "02",
    });
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/abc-123/edit").kind).toBe(
      "deviceEdit",
    );
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/abc-123").kind).toBe(
      "deviceDetail",
    );
  });

  it("builds new device path with branch", () => {
    expect(productionPulseDeviceNewPath("01")).toBe("/apps/production-pulse/devices/new?branch=01");
  });

  it("returns unknown for foreign paths", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/legacy").kind).toBe("unknown");
  });
});
