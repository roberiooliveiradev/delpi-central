import { describe, expect, it } from "vitest";

import { buildDelpiMesHref, parseDelpiMesRoute } from "./useDelpiMesRoute";

describe("Delpi MES routing", () => {
  it("defaults the product root to monitoring and branch 01", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes", "")).toEqual({ area: "monitoring", branch: "01" });
  });

  it("preserves area and branch in a shareable URL", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/downtimes", "?branch=02")).toEqual({ area: "downtimes", branch: "02" });
    expect(buildDelpiMesHref("history", "02")).toBe("/apps/delpi-mes/history?branch=02");
  });
});
