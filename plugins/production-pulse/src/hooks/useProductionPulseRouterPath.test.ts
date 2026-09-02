import { describe, expect, it } from "vitest";

import { parseProductionPulseRoute } from "../constants/routes";

describe("device detail tab routing", () => {
  it("resolve aba a partir da query após navegação interna (?tab=)", () => {
    const devicePath = "/apps/production-pulse/devices/abc-123";

    expect(parseProductionPulseRoute(devicePath, "")).toMatchObject({
      kind: "deviceDetail",
      tab: "overview",
    });
    expect(parseProductionPulseRoute(devicePath, "?tab=history")).toMatchObject({
      kind: "deviceDetail",
      tab: "history",
    });
    expect(parseProductionPulseRoute(devicePath, "?tab=commands")).toMatchObject({
      kind: "deviceDetail",
      tab: "commands",
    });
  });
});
