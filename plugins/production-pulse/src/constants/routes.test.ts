import { describe, expect, it } from "vitest";

import { parseProductionPulseRoute } from "./routes";

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

  it("returns unknown for foreign paths", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/legacy").kind).toBe("unknown");
  });
});
